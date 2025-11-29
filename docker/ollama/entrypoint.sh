#!/bin/sh
set -e

# Serve Ollama in the background
ollama serve &

# Wait a few seconds for the server to be ready
sleep 5

# Pull the model if not already downloaded
if [ ! -d "/root/.ollama/models/phi3_3.8b" ]; then
    echo "Pulling phi3:3.8b model..."
    ollama pull phi3:3.8b
else
    echo "Model already exists, skipping pull."
fi

# Wait for serve to keep container alive
wait
