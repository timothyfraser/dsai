# 01_transcribe.py
# Speech-to-Text (STT): turn a recording into text, on your own laptop
# Pairs with 01_transcribe.R
# Course kit, module 18
#
# Topic: Speech-to-Text
#
# This script transcribes a .wav file with faster-whisper, a fast local version
# of OpenAI's open Whisper model. Nothing leaves your computer.
# The last section shows the same job done by a cloud API, for comparison.

# If you haven't already, install these packages...
# pip install faster-whisper requests python-dotenv
# The first run downloads the model (about 150 MB for "base.en"). After that it works offline.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import os  # for environment variables + file checks
import time  # for timing each transcription

## 0.2 Settings ###################################

# Run this script from the top of the course repo, so the audio path resolves.
AUDIO_PATH = os.getenv("AUDIO_PATH", "06_agents/06_jfk.wav")

# Whisper comes in sizes: tiny, base, small, medium, large.
# Bigger is more accurate and slower. ".en" models only know English, and are a bit better at it.
# Start with "base.en" on a laptop; try "tiny.en" if it feels slow.
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base.en")


# 1. TRANSCRIBE LOCALLY #####################################

def transcribe(audio_path, model_size=WHISPER_MODEL):
    """Return the words spoken in an audio file, as one string."""

    # Testing values
    # audio_path = "06_agents/06_jfk.wav"
    # model_size = "base.en"

    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Import here, so the rest of the kit still loads when faster-whisper is missing.
    from faster_whisper import WhisperModel

    # device="cpu" and compute_type="int8" are the settings for a laptop with no graphics card.
    # int8 stores the model's numbers in a smaller format: faster, almost as accurate.
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    # Whisper cuts the audio into segments (stretches of speech) and transcribes each one.
    segments, info = model.transcribe(audio_path, beam_size=5)

    # Join the segments back into one string.
    text = " ".join(segment.text.strip() for segment in segments)
    return text


# 2. EXAMPLE: JOHN F KENNEDY SPEECH CLIP #################################

# Same clip as 06_agents/06_alms_cloud.py, Example 3.
start = time.time()
transcript = transcribe(AUDIO_PATH)
print(f"\nTime taken: {time.time() - start:.2f} seconds")
print("\nTranscript:")
print(transcript)

# Compare with the ALM in 06_alms_cloud.py:
# The ALM was asked to transcribe; Whisper can do nothing BUT transcribe.
# A narrow model is often the more predictable tool for a narrow job.


# 3. THE SAME JOB IN THE CLOUD (OPTIONAL) #################################

# A cloud STT model is usually more accurate on hard audio (noise, accents, jargon),
# but your recording leaves your computer, and every minute costs a little money.
# Needs OPENAI_API_KEY in .env. Uncomment to try.

# import requests
# from dotenv import load_dotenv
# load_dotenv()
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
# with open(AUDIO_PATH, "rb") as f:
#     response = requests.post(
#         "https://api.openai.com/v1/audio/transcriptions",
#         headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
#         files={"file": f},
#         data={"model": "gpt-4o-mini-transcribe"},  # model names change over time
#         timeout=120,
#     )
# response.raise_for_status()
# print(response.json()["text"])
