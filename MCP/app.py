import asyncio
import os
from flask import Flask, render_template, request, jsonify, stream_with_context, Response

# This will work once the package is installed correctly
from abstract.config_container import ConfigContainer
from clients.ollama_client import OllamaMCPClient

# --- Configuration ---
# Use absolute paths to avoid directory issues
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
OLLAMA_CLIENT_DIR = os.path.join(ROOT_DIR, "ollama-mcp-client")
SERVER_DIR = os.path.join(OLLAMA_CLIENT_DIR, "server")
SERVER_CONFIG_PATH = os.path.join(OLLAMA_CLIENT_DIR, "examples", "server.json")
DB_PATH = os.path.join(SERVER_DIR, "data.db")

# --- Flask App Initialization ---
app = Flask(__name__)
app.config['OLLAMA_CLIENT'] = None
app.config['CLIENT_LOCK'] = asyncio.Lock()

# --- Ollama Client Management ---
async def get_ollama_client():
    """
    Initializes and returns a singleton OllamaMCPClient instance.
    Uses a lock to prevent race conditions during initialization.
    """
    async with app.config['CLIENT_LOCK']:
        if app.config['OLLAMA_CLIENT'] is None:
            print("Initializing OllamaMCPClient...")
            # The client and its subprocess need to be started from the server's directory
            # to ensure it can find the database file (data.db).
            original_cwd = os.getcwd()
            os.chdir(SERVER_DIR)

            try:
                config = ConfigContainer.form_file(SERVER_CONFIG_PATH)
                client = await OllamaMCPClient.create(config)
                app.config['OLLAMA_CLIENT'] = client
                print("Client initialized successfully.")
            finally:
                # IMPORTANT: Change back to the original directory once the client is created.
                # The client's subprocess will retain the CWD it was started with.
                os.chdir(original_cwd)

    return app.config['OLLAMA_CLIENT']

# --- Flask Routes ---
@app.route("/")
def index():
    """Serves the main chat page."""
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
async def chat():
    """Handles the chat message processing."""
    data = request.get_json()
    query = data.get("message")

    if not query:
        return jsonify({"error": "No message provided"}), 400

    try:
        # Ensure client is initialized before processing
        client = await get_ollama_client()

        async def generate():
            """Async generator to stream the response."""
            # No longer need to change directory here. The client's subprocess
            # is already running in the correct directory.
            async for part in client.process_message(query):
                if part.get("role") == "assistant":
                    content = part.get("content", "")
                    yield content

        return Response(stream_with_context(generate()), mimetype="text/plain")

    except Exception as e:
        print(f"An error occurred: {e}")
        # It's helpful to see the error type as well
        return jsonify({"error": f"{type(e).__name__}: {e}"}), 500

# --- Main Execution ---
if __name__ == "__main__":
    # Ensure the database exists before starting
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        print("Please run the data.py script first to create the database.")
    else:
        app.run(debug=True, port=5001)