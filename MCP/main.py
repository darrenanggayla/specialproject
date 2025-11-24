import subprocess
import os
import sys

def run(cmd):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"Command failed: {cmd}")
        sys.exit(1)

# Change directory to ollama-mcp-client
os.chdir("ollama-mcp-client")

# Create virtual environment using uv
# run("uv venv")

# Install package in editable mode
run("uv pip install -e .")

# Run the example
run("uv run examples/ollama_example.py examples/server.json")