/* filepath: d:\NTUST\SpecialProject\Mac\MCP\MCP\static\script.js */
document.addEventListener("DOMContentLoaded", () => {
    const chatInput = document.getElementById("chat-input");
    const sendButton = document.getElementById("send-button");
    const chatBox = document.getElementById("chat-box");

    const sendMessage = async () => {
        const query = chatInput.value.trim();
        if (!query) return;

        // Display user message
        appendMessage(query, "user");
        chatInput.value = "";
        
        // Create a placeholder for the bot's response
        const botMessageElement = appendMessage("...", "bot");

        try {
            const response = await fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: query }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            // Handle streaming response
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let botReply = "";
            botMessageElement.querySelector('p').innerText = ""; // Clear the placeholder

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value, { stream: true });
                botReply += chunk;
                botMessageElement.querySelector('p').innerText = botReply;
                chatBox.scrollTop = chatBox.scrollHeight;
            }

        } catch (error) {
            botMessageElement.querySelector('p').innerText = "Sorry, something went wrong.";
            console.error("Error:", error);
        }
    };

    const appendMessage = (text, sender) => {
        const messageWrapper = document.createElement("div");
        messageWrapper.classList.add("message", `${sender}-message`);
        
        const messageParagraph = document.createElement("p");
        messageParagraph.innerText = text;
        
        messageWrapper.appendChild(messageParagraph);
        chatBox.appendChild(messageWrapper);
        chatBox.scrollTop = chatBox.scrollHeight;
        return messageWrapper;
    };

    sendButton.addEventListener("click", sendMessage);
    chatInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            sendMessage();
        }
    });
});