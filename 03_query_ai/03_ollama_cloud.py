# 03_ollama_cloud.py
# Query Google's free Gemini tier with an API key
# This script calls Google's free Gemini tier through its OpenAI-compatible endpoint,
# using your API key stored in the .env file
# The free tier may use your prompts to improve Google's products, so send only public or made-up data.

# If you haven't already, install these packages...
# pip install requests python-dotenv

# Load libraries
import requests  # For HTTP requests
import json      # For working with JSON
import os        # For environment variables
import time      # For waiting between retries
from dotenv import load_dotenv  # For loading .env file

# Starting message
print("\n🚀 Querying Google's Gemini in Python...\n")

# Load environment variables from .env file
# This reads the .env file and loads variables into the environment
load_dotenv()

# Get API key from environment variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Check if API key is set
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file. Please set it up first.")

# Gemini API endpoint (OpenAI-compatible)
url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"

MODEL = "gemini-flash-lite-latest"  # Free cloud model

# Construct the request body
body = {
    "model": MODEL,
    "messages": [
        {
            "role": "user",
            "content": "Hello! Please respond with: Model is working."
        }
    ]
}

# Set headers with API key
headers = {
    "Authorization": f"Bearer {GEMINI_API_KEY}",
    "Content-Type": "application/json"
}

# Send POST request to the Gemini API
# If the server is busy (429, 500, 503), wait 2, 4, then 8 seconds and try again
for wait in [2, 4, 8, None]:
    response = requests.post(url, headers=headers, json=body)
    if response.status_code not in (429, 500, 503):
        break
    if wait is None:
        raise RuntimeError(f"Gemini is busy (HTTP {response.status_code}). Try again in a minute.")
    time.sleep(wait)

# Stop with one plain line if the request failed (for example, a wrong key)
if response.status_code != 200:
    raise SystemExit(f"Gemini request failed with HTTP status {response.status_code}.")

# Parse the response JSON
result = response.json()

# Extract the model's reply
output = result["choices"][0]["message"]["content"]

# Print the model's reply
print("📝 Model Response:")
print(output)
print()

# Closing message
print("✅ Gemini query complete.\n")

# Clear environment
globals().clear()
