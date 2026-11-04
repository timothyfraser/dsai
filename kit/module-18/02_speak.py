# 02_speak.py
# Text-to-Speech (TTS): turn text into a spoken .wav file, on your own laptop
# Pairs with 02_speak.R
# Course kit, module 18
#
# Topic: Text-to-Speech
#
# This script speaks a sentence with Piper, a small local TTS engine that runs
# well on a laptop processor. Nothing leaves your computer.
# The last section shows the same job done by a cloud API, for comparison.

# If you haven't already, install Piper and download one voice...
# pip install piper-tts
# python3 -m piper.download_voices en_US-lessac-medium
# A voice is two files: en_US-lessac-medium.onnx (the model) and a matching .onnx.json (its settings).
# Each voice has a model card that says how you may use it. Read it before you publish audio.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import os  # for environment variables + file checks
import subprocess  # for running the piper command
import sys  # for finding this Python
import time  # for timing each run

## 0.2 Settings ###################################

# The voice to use. Piper looks for <voice>.onnx in the folder you run from, or in --data-dir.
PIPER_VOICE = os.getenv("PIPER_VOICE", "en_US-lessac-medium")
OUTPUT_PATH = os.getenv("SPEAK_OUTPUT", "speak_test.wav")


# 1. SPEAK LOCALLY #####################################

def speak(text, output_path=OUTPUT_PATH, voice=PIPER_VOICE):
    """Write `text` as speech to a .wav file and return the file path."""

    # Testing values
    # text = "Pump three is leaking oil."
    # output_path = "speak_test.wav"
    # voice = "en_US-lessac-medium"

    # We run Piper as a command, exactly as you would type it in a terminal:
    # python3 -m piper -m <voice> -f <output.wav> -- "<text>"
    command = [sys.executable, "-m", "piper", "-m", voice, "-f", output_path, "--", text]
    result = subprocess.run(command, capture_output=True, text=True)

    # If Piper failed, show its own error message instead of a vague one.
    if result.returncode != 0:
        raise RuntimeError(f"piper failed: {result.stderr.strip()}")
    return output_path


# 2. EXAMPLE: A FIELD REPORT, SPOKEN #################################

TEXT = "Pump three at the north lift station is leaking oil. Priority high."

start = time.time()
path = speak(TEXT)
print(f"\nTime taken: {time.time() - start:.2f} seconds")
print(f"Wrote: {path} ({os.path.getsize(path)} bytes)")

# Play it in any audio player, or in a notebook with:
# from IPython.display import Audio; Audio(path)

# Listen for: numbers ("three" vs "3"), short codes (try "P-3"), and names.
# TTS reads what you write, so write numbers and codes the way you want them said.


# 3. THE SAME JOB IN THE CLOUD (OPTIONAL) #################################

# Cloud voices sound more natural and handle odd words better,
# but your text leaves your computer, and every character costs a little money.
# Needs OPENAI_API_KEY in .env. Uncomment to try.

# import requests
# from dotenv import load_dotenv
# load_dotenv()
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
# response = requests.post(
#     "https://api.openai.com/v1/audio/speech",
#     headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
#     json={"model": "gpt-4o-mini-tts", "voice": "alloy", "input": TEXT, "response_format": "wav"},
#     timeout=120,
# )  # model and voice names change over time
# response.raise_for_status()
# with open("speak_cloud.wav", "wb") as f:
#     f.write(response.content)
