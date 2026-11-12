#!/bin/bash

# 00_ollama.sh - Ollama Startup Script
# Serves Ollama on a specific port, pulls a small model, runs it, and provides stop controls
# 🛑🌐🤖📡🚀
# Load your local paths and variables
source .bashrc

# Configuration
PORT=11434  # Default Ollama port (change as needed)
# Set environment variable for port
export OLLAMA_HOST="127.0.0.1:$PORT"
MODEL="granite4:3b"  # Small, reputable model from IBM
SERVER_PID=""
MODEL_PID=""

# Start server in background, and assign the process ID to the SERVER_PID variable
# Only start a server if none answers (Ollama may already be running)
if curl -s -m 2 http://127.0.0.1:$PORT/api/version > /dev/null; then
  echo "Ollama is already running; using it."
else
  ollama serve > /dev/null 2>&1 & SERVER_PID=$!
fi
# View the process ID of ollama
echo $SERVER_PID

# Pull model of interest
# ollama pull granite4:3b

# run model of interest interactively -- usually I don't want this
# ollama run $MODEL & MODEL_PID=$!
# echo $MODEL_PID

# Need to kill the server and model if they are running? These might help.
# kill $SERVER_PID 2>/dev/null
# pkill -f "ollama serve" 2>/dev/null
# pkill -f "ollama run" 2>/dev/null


# Test query the model
echo "Testing the model..."
test=$(curl -s -X POST http://localhost:$PORT/api/generate \
    -H "Content-Type: application/json" \
    -d '{
        "model": "'$MODEL'",
        "prompt": "Hello! Please respond with just: Model is working.",
        "stream": false
    }' 2>/dev/null)



# install jq for json parsing
# https://chocolatey.org/install to install chocolatey
# choco install jq

# or for other systems... sudo apt-get install jq

# Use jq to extract the response text
echo "$test" | jq '.'


# Extract just some parts
echo "$test" | jq '.model, .response'


test=$(curl -s -X POST http://localhost:$PORT/api/chat \
    -H "Content-Type: application/json" \
    -d '{
        "model": "granite4:3b",
        "stream": false,
        "messages": [
            {
            "role": "user",
            "content": "What is the current temperature in London?"
            }
        ],
        "tools": [
            {
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get the current weather conditions for a given location.",
                "parameters": {
                "type": "object",
                "required": ["location"],
                "properties": {
                    "location": {
                    "type": "string",
                    "description": "The city and optional state/country, e.g., 'London, UK'"
                    }
                }
                }
            }
            }
        ]
        }' 2>/dev/null)

echo "$test" | jq '.'
