from contextlib import AbstractAsyncContextManager, AsyncExitStack
from itertools import chain
import json
import logging
from abstract.api_response import ChatResponse
from abstract.session import Session
import colorlog

from mcp import ClientSession, StdioServerParameters
from mcp.types import TextContent
from mcp.client.stdio import stdio_client
from typing import AsyncIterator, Self, Sequence, cast
from ollama import AsyncClient, Message, Tool

from abstract.config_container import ConfigContainer

SYSTEM_PROMPT = """You are a helpful assistant capable of accessing external functions to answer questions about NTUST.

When a user asks a question:
1. Use the smart_query tool with the user's complete question
2. The tool will automatically extract keywords and search the knowledge base
3. Provide the answer from the tool response in a natural, friendly way

Core Directive:
- ALWAYS use the smart_query tool for each new question - pass the user's full question to it
- DO NOT try to combine information from previous questions
- DO NOT use your general knowledge - only use information from the tool responses
- If the tool returns no matches, politely say the information is not available in the database

Important:
- Each question should be treated independently
- Always call smart_query with the user's current question, not accumulated keywords
- Provide answers in a natural, conversational tone
- Be concise and direct with your answers"""


class OllamaMCPClient(AbstractAsyncContextManager):
    def __init__(self, host: str | None = None):
        # Setup logging
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(levelname)s%(reset)s - %(message)s",
            datefmt=None,
            reset=True,
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        )

        console_handler.setFormatter(formatter)
        if not self.logger.hasHandlers():
            self.logger.addHandler(console_handler)

        # Initialize client objects
        self.client = AsyncClient("")
        self.servers: dict[str, Session] = {}
        self.selected_server: dict[str, Session] = {}
        self.messages = []
        self.exit_stack = AsyncExitStack()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        try:
            await self.exit_stack.aclose()
        except ValueError:
            return

    @classmethod
    async def create(cls, config: ConfigContainer, host="") -> Self:
        """Factory method to create and initialize a client instance"""
        client = cls(host)
        await client._connect_to_multiple_servers(config)
        return client

    async def _connect_to_multiple_servers(self, config: ConfigContainer):
        for name, params in config.items():
            session, tools = await self._connect_to_server(name, params)
            self.servers[name] = Session(session=session, tools=[*tools])

        # Default to no select
        self.selected_server = self.servers

        self.logger.info(
            f"Connected to server with tools: {[cast(Tool.Function, tool.function).name for tool in self.get_tools()]}"
        )

    async def _connect_to_server(
        self, name: str, server_params: StdioServerParameters
    ) -> tuple[ClientSession, Sequence[Tool]]:
        """Connect to an MCP server

        Args:
            server_script_path: Path to the server script (.py)
        """
        stdio, write = await self.exit_stack.enter_async_context(stdio_client(server_params))
        session = cast(ClientSession, await self.exit_stack.enter_async_context(ClientSession(stdio, write)))

        await session.initialize()

        # List available tools
        response = await session.list_tools()
        tools = [
            Tool(
                type="function",
                function=Tool.Function(
                    name=f"{name}/{tool.name}",
                    description=tool.description,
                    parameters=cast(Tool.Function.Parameters, tool.inputSchema),
                ),
            )
            for tool in response.tools
        ]
        return (session, tools)

    def get_tools(self) -> list[Tool]:
        return list(chain.from_iterable(server.tools for server in self.selected_server.values()))

    def select_server(self, servers: list[str]) -> Self:
        self.selected_server = {name: server for name, server in self.servers.items() if name in servers}
        self.logger.info(f"Selected server: {list(self.selected_server.keys())}")
        return self

    async def prepare_prompt(self):
        """Clear current message and create new one"""

        # Get all prompt with name "default"
        # all_prompts = [
        #     (server, prompt)
        #     for server in self.selected_server.values()
        #     for prompt in (await server.session.list_prompts()).prompts
        # ]
        # default_prompts = [
        #     cast(TextContent, (await server.session.get_prompt(prompt.name)).messages[0].content).text
        #     for server, prompt in all_prompts
        #     if prompt.name == "default"
        # ]
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        # + [
        #     {"role": "system", "content": prompt} for prompt in default_prompts
        # ]

    async def process_message(self, message: str, model: str | None = None) -> AsyncIterator[ChatResponse]:
        """Process a query using LLM and available tools"""
        if model is None:
            model = "customqwen:latest"  # Predefined model
        self.messages.append({"role": "user", "content": message})

        async for part in self._recursive_prompt(model):
            yield part

    async def _recursive_prompt(self, model: str) -> AsyncIterator[ChatResponse]:
        # self.logger.debug(f"message: {self.messages}")
        # Streaming does not work when provided with tools, that's the issue with API or ollama itself.
        self.logger.debug("Prompting")
        stream = await self.client.chat(
            model=model,
            messages=self.messages,
            tools=self.get_tools(),
            stream=True,
        )

        tool_message_count = 0
        async for part in stream:
            if part.message.content:
                yield ChatResponse(role="assistant", content=part.message.content)
            elif part.message.tool_calls:
                self.logger.debug(f"Calling tool: {part.message.tool_calls}")
                tool_messages = await self._tool_call(part.message.tool_calls)
                tool_message_count += 1
                for tool_message in tool_messages:
                    yield ChatResponse(role="tool", content=tool_message)
                    self.messages.append({"role": "tool", "content": tool_message})

        if tool_message_count > 0:
            async for part in self._recursive_prompt(model):
                yield part

    async def _tool_call(self, tool_calls: Sequence[Message.ToolCall]) -> list[str]:
        messages: list[str] = []
        for tool in tool_calls:
            split = tool.function.name.split("/")
            session = self.selected_server[split[0]].session
            tool_name = split[1]
            tool_args = tool.function.arguments

            # Execute tool call
            try:
                result = await session.call_tool(tool_name, dict(tool_args))
                self.logger.debug(f"Tool call result: {result.content}")
                message = f"tool: {tool.function.name}\nargs: {tool_args}\nreturn: {cast(TextContent, result.content[0]).text}"
            except Exception as e:
                self.logger.debug(f"Tool call error: {e}")
                message = f"Error in tool: {tool.function}\nargs: {tool_args}\n{e}"

            # Continue conversation with tool results
            messages.append(message)
        return messages
