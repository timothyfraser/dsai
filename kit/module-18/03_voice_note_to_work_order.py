# 03_voice_note_to_work_order.py
# From a voice note to a filed work order: transcribe, extract, validate, write
# Pairs with 03_voice_note_to_work_order.R
# Course kit, module 18
#
# Topic: Audio models in a real workflow
#
# A field technician records a voice note. This script:
# 1. transcribes it (speech-to-text, local),
# 2. asks a local model to fill a work-order form, shaped by a JSON schema,
# 3. checks the answer against that schema in plain code,
# 4. writes one row to a CSV file, marked "draft" until a person confirms it.
#
# Stub mode, for testing with no model installed:
# AUDIO_STUB=1 skips Whisper and uses a fixed transcript.
# LLM_STUB=1 skips Ollama and uses a fixed JSON answer.

# If you haven't already, install these packages...
# pip install faster-whisper requests
# and pull the model in Ollama: ollama pull granite4:3b

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import csv  # for writing the work-order row
import datetime  # for stamping when the row was written
import json  # for reading the model's JSON answer
import os  # for environment variables + file checks

import requests  # for HTTP requests to Ollama

## 0.2 Settings ###################################

# Run this script from the top of the course repo, so the audio path resolves.
AUDIO_PATH = os.getenv("AUDIO_PATH", "06_agents/06_jfk_short.wav")
WORK_ORDERS_CSV = os.getenv("WORK_ORDERS_CSV", "work_orders.csv")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
MODEL = os.getenv("MODEL", "granite4:3b")
AUDIO_STUB = os.getenv("AUDIO_STUB", "") == "1"
LLM_STUB = os.getenv("LLM_STUB", "") == "1"

## 0.3 The contract: a JSON schema for one work order ###################################

# A JSON schema is a description of the shape an answer must have:
# which fields, what type each one is, and which values are allowed.
# The model sees this schema. Your code checks the answer against it. Both matter.
WORK_ORDER_SCHEMA = {
    "type": "object",
    "properties": {
        "asset": {"type": "string"},  # the thing that needs work, e.g. "Pump 3"
        "location": {"type": "string"},  # where it is
        "problem": {"type": "string"},  # what is wrong, in one sentence
        "priority": {"type": "string", "enum": ["low", "medium", "high"]},
        "safety_hazard": {"type": "boolean"},  # is anyone at risk right now?
        "action_requested": {"type": "string"},  # what the technician asked for
    },
    "required": ["asset", "location", "problem", "priority", "safety_hazard", "action_requested"],
}

# The fixed answers used in stub mode. They are test values, not real model output.
STUB_TRANSCRIPT = (
    "This is the night operator at the north lift station. Pump three is leaking oil "
    "from the seal, and there is a slick on the floor by the stairs. I would call it high "
    "priority. Please send a mechanic to replace the seal before the next shift."
)
STUB_JSON = (
    '{"asset": "Pump 3", "location": "North lift station", '
    '"problem": "Oil is leaking from the pump seal onto the floor", "priority": "high", '
    '"safety_hazard": true, "action_requested": "Send a mechanic to replace the seal before the next shift"}'
)
# The check script swaps in a broken answer here, to prove the validator rejects it.
STUB_JSON = os.getenv("LLM_STUB_JSON", STUB_JSON)


# 1. TRANSCRIBE THE VOICE NOTE #####################################

def transcribe(audio_path):
    """Return the words in the voice note (or the stub transcript in stub mode)."""
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    if AUDIO_STUB:
        return STUB_TRANSCRIPT
    # Same call as 01_transcribe.py, kept inline so this script stands alone.
    from faster_whisper import WhisperModel
    model = WhisperModel("base.en", device="cpu", compute_type="int8")
    segments, info = model.transcribe(audio_path, beam_size=5)
    return " ".join(segment.text.strip() for segment in segments)


# 2. ASK A MODEL TO FILL THE FORM #####################################

def extract_work_order(transcript):
    """Return the model's answer as a JSON string, shaped by WORK_ORDER_SCHEMA."""
    if LLM_STUB:
        return STUB_JSON

    prompt = (
        "You file maintenance work orders. Read the technician's voice note below and fill "
        "every field of the work order. Use only facts in the note. If the note does not say "
        "how urgent it is, use \"medium\". Return only JSON.\n\n"
        f"Voice note: {transcript}"
    )
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        # Passing the schema as "format" asks Ollama to only produce JSON of this shape.
        "format": WORK_ORDER_SCHEMA,
        "stream": False,
        "options": {"temperature": 0},  # the same note should give the same form
    }
    response = requests.post(OLLAMA_URL, json=body, timeout=180)
    response.raise_for_status()
    return response.json()["message"]["content"]


# 3. CHECK THE ANSWER AGAINST THE SCHEMA #####################################

def validate_work_order(record):
    """Return a list of problems. An empty list means the record fits the schema."""
    problems = []
    types = {"string": str, "boolean": bool}
    for field in WORK_ORDER_SCHEMA["required"]:
        if field not in record:
            problems.append(f"missing field: {field}")
            continue
        rule = WORK_ORDER_SCHEMA["properties"][field]
        value = record[field]
        if not isinstance(value, types[rule["type"]]):
            problems.append(f"{field} should be a {rule['type']}, got {value!r}")
        elif rule["type"] == "string" and value.strip() == "":
            problems.append(f"{field} is empty")
        elif "enum" in rule and value not in rule["enum"]:
            problems.append(f"{field} must be one of {rule['enum']}, got {value!r}")
    # Fields the schema does not name are a sign the model drifted from the contract.
    for field in record:
        if field not in WORK_ORDER_SCHEMA["properties"]:
            problems.append(f"unexpected field: {field}")
    return problems


# 4. WRITE ONE ROW TO THE CSV #####################################

COLUMNS = ["recorded_at", "audio_file", "transcript"] + WORK_ORDER_SCHEMA["required"] + ["status"]

def write_row(record, transcript, audio_path, csv_path=WORK_ORDERS_CSV):
    """Append the work order to the CSV, with a header the first time."""
    row = {
        "recorded_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "audio_file": os.path.basename(audio_path),
        "transcript": transcript,
        **record,
        # A machine filled this form. It stays a draft until a person reads it and confirms.
        "status": "draft",
    }
    new_file = not os.path.exists(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, quoting=csv.QUOTE_ALL)
        if new_file:
            writer.writeheader()
        writer.writerow(row)
    return row


# 5. RUN THE WHOLE PIPELINE #####################################

transcript = transcribe(AUDIO_PATH)
print("Transcript:")
print(transcript)

answer = extract_work_order(transcript)
record = json.loads(answer)  # fails loudly if the model returned something that is not JSON

problems = validate_work_order(record)
if problems:
    # Do not file a record that breaks the contract. Show why, and stop.
    raise ValueError("Work order rejected: " + "; ".join(problems))

row = write_row(record, transcript, AUDIO_PATH)
print(f"\nFiled a draft work order in {WORK_ORDERS_CSV}:")
print(json.dumps(row, indent=2))
