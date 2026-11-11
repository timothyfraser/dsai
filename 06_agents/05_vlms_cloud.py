# 05_vlms_cloud.py
# Using Visual Language Models (VLMs) with Google's free Gemini tier
# Pairs with 05_vlms_cloud.R
# Tim Fraser
#
# Topic: Visual Language Models
#
# What if our AI systems could see, not just read?
# This script shows how to send an image to a vision-capable model
# (like gemini-flash-lite-latest) using Google's free Gemini tier.
# The free tier may use your prompts to improve Google's products,
# so send only public or made-up data.
#
# Get a free key at https://aistudio.google.com/app/apikey
# and save it in your .env file as GEMINI_API_KEY=...

# If you haven't already, install these packages...
# pip install requests pillow python-dotenv

# 0. SETUP ###################################

## Example Image #################################

# Today, we'll use an example image from Unsplash.
# (Great place to get free pictures for your projects!)
# Photo by Toa Heftiba
# Source Link: https://unsplash.com/photos/people-eating-inside-of-cafeteria-during-daytime-6bKpHAun4d8
# Creator Link: https://unsplash.com/@heftiba
#
# It shows a bunch of people in a coffee shop.
#
# Let's say we want to count the number of people in the image.
# There are creepy uses of this, sure, but also some legitimate uses:
# - evacuation checks
# - crowd detection
# - object detection
# - face detection
# - text detection
# - license plate detection
# - car detection
# - pedestrian detection
#
# An ethical system would perform the count, and then delete the image.
# That way, we reduce the risk of the image being reused for harmful purposes.

## 0.1 Load Packages #################################

import base64  # for image encoding before API upload
import json  # for parsing machine-readable model output
import mimetypes  # for finding the image's mime type
import os  # for environment variables and file checks

import requests  # for HTTP requests
import time  # for waiting between retries
from dotenv import load_dotenv  # for loading .env files
from PIL import Image  # for image resizing

## 0.2 Image Processing #################################

# First step: downscale the image.
# Why? Vision models still have context limits, so huge images can be wasteful
# or fail. Smaller images are often enough for counting tasks.

# Path to the original image we want the VLM to analyze
image_path = "06_agents/05_coffeeshop.jpg"

if not os.path.exists(image_path):
    raise FileNotFoundError(f"Image not found: {image_path}")

# Shrink image to 50% of the original size
with Image.open(image_path) as img:
    width, height = img.size
    new_size = (max(1, int(width * 0.5)), max(1, int(height * 0.5)))
    img_small = img.resize(new_size)
    image_path_small = "06_agents/05_coffeeshop_small.jpg"
    img_small.save(image_path_small)

print(f"Saved resized image: {image_path_small} ({new_size[0]}x{new_size[1]})")

## 0.3 Environment #################################

# Load .env (contains GEMINI_API_KEY for cloud access)
if os.path.exists(".env"):
    load_dotenv()
else:
    print(".env file not found. Make sure it exists in the project root.")

gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file.")

## 0.4 Configuration #################################

# gemini-flash-lite-latest is a multimodal model that can read images + text
model = "gemini-flash-lite-latest"
# Prompt we pair with the image
prompt = "Analyze this image and count the number of people in the image."

# Make sure the downscaled image exists before sending
if not os.path.exists(image_path_small):
    raise FileNotFoundError(f"Image not found: {image_path_small}")

# Let's write ourselves a short helper function for the query
def query(image_file_path, user_prompt, model_name, api_key):
    """Send one image + prompt to the Gemini API and return text output."""
    with open(image_file_path, "rb") as image_file:
        image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

    # Find the image's real mime type (eg. image/jpeg)
    mime_type = mimetypes.guess_type(image_file_path)[0] or "image/jpeg"

    # Build the request body (OpenAI-compatible chat format)
    # The image goes in as a data URI inside the message content
    body = {
        "model": model_name,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_base64}"}},
                ],
            }
        ],
    }

    # Send bearer-token auth in request headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # POST to Gemini; if the service is busy (429, 500, 503), retry up to 3 times
    url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    for wait in [2, 4, 8]:
        response = requests.post(url, headers=headers, json=body, timeout=120)
        if response.status_code not in (429, 500, 503):
            break
        time.sleep(wait)
    if response.status_code in (429, 500, 503):
        raise RuntimeError(f"Gemini is busy or over its free limit (HTTP {response.status_code}). Try again later.")
    response.raise_for_status()
    result = response.json()
    return result["choices"][0]["message"]["content"]


# 1. CLOUD VLM WITH REQUESTS ##########################

output = query(image_path_small, prompt, model, gemini_api_key)
print("\nVLM Response (cloud):")
print(output)

# 2. MACHINE READABLE OUTPUT #########################

# Often, in production workflows, we want machine-readable output.
# A good pattern is to ask the model to return only a JSON string.
prompt2 = (
    "Analyze this image and count the number of people in the image. "
    "Output the answer in a JSON string. "
    "Do not include any other text in your response. "
    "Do not include any extra formatting like '```json' in your response. "
    "The JSON string should have the following format: "
    '{"n_sitting":"<total number of people sitting here>","n_standing":"<total number of people standing here>"}'
)

resp2 = query(image_path_small, prompt2, model, gemini_api_key)
print("\nRaw JSON-like response:")
print(resp2)

try:
    # Parse the JSON string into a Python dictionary
    parsed_json = json.loads(resp2)
    print("\nParsed JSON:")
    print(parsed_json)
    print(f"Number of people sitting: {parsed_json.get('n_sitting')}")
    print(f"Number of people standing: {parsed_json.get('n_standing')}")
except json.JSONDecodeError:
    print("\nCould not parse JSON response. Try rerunning the query for stricter formatting.")
