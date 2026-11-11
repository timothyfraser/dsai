# photo_to_record.py
# Turn a photo into one checked row of a CSV, with a vision model
# Pairs with photo_to_record.R
# Course kit, module 17
#
# Topic: Visual Language Models
#
# In 05_vlms_cloud.py, we asked a vision model for a JSON string
# and hoped it came back clean. This script stops hoping.
# It sends a photo plus a schema (a list of the fields we want, and their types),
# then checks every field of the reply before it writes anything.
# A reply that breaks the schema is refused, and no row is written.
#
# Run it from the top of the course repo, so the image path resolves:
#   python photo_to_record.py 06_agents/05_coffeeshop_small.jpg records.csv
#
# No model handy? Set VLM_STUB=1 and the script uses a fixed reply instead.
#   VLM_STUB=1 python photo_to_record.py 06_agents/05_coffeeshop_small.jpg records.csv
# VLM_STUB=guess and VLM_STUB=mismatch send two broken replies, to show the refusal.

# If you haven't already, install these packages...
# pip install requests python-dotenv

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import base64  # for image encoding before API upload
import csv  # for writing the record as a CSV row
import json  # for reading the schema and parsing the reply
import os  # for environment variables and file checks
import sys  # for command-line arguments and exit codes
import time  # for waiting between retries

import requests  # for HTTP requests

## 0.2 Configuration #################################

# The photo to read, and the CSV to add a row to.
# You can pass both on the command line instead.
image_path = sys.argv[1] if len(sys.argv) > 1 else "06_agents/05_coffeeshop_small.jpg"
csv_path = sys.argv[2] if len(sys.argv) > 2 else "records.csv"

# The schema sits next to this script. Edit it to ask for your own fields.
schema_path = os.environ.get(
    "RECORD_SCHEMA",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "record_schema.json"),
)

# Local by default (ministral-3:3b through Ollama). Set VLM_CLOUD=1 to use Google's free Gemini tier.
# The free tier may use your prompts to improve Google's products, so send only public or made-up data.
use_cloud = os.environ.get("VLM_CLOUD", "") == "1"
model = os.environ.get("VLM_MODEL", "gemini-flash-lite-latest" if use_cloud else "ministral-3:3b")
stub = os.environ.get("VLM_STUB", "")

if not os.path.exists(image_path):
    raise FileNotFoundError(f"Image not found: {image_path}")

with open(schema_path, encoding="utf-8") as f:
    schema = json.load(f)


# 1. WRITE THE PROMPT FROM THE SCHEMA #######################

# We never type the field list twice. The prompt is built from the schema,
# so the model is asked for exactly the fields the checker will check.
def build_prompt(schema):
    lines = [
        "Look at this photo and fill in a JSON object with these fields.",
        "Output only the JSON object. Do not include any other text.",
        "Do not include any extra formatting like '```json' in your response.",
        "If you cannot see something clearly, write \"unknown\". Do not guess.",
        "",
    ]
    for field in schema["fields"]:
        if field["type"] == "integer":
            kind = "a whole number" + (', or "unknown"' if field.get("allow_unknown") else "")
        elif field["type"] == "choice":
            kind = "one of: " + ", ".join(f'"{c}"' for c in field["choices"])
        else:
            kind = "a short text"
        lines.append(f'"{field["name"]}": {kind}. ({field["description"]})')
    return "\n".join(lines)


prompt = build_prompt(schema)
print("Prompt sent with the photo:\n" + prompt + "\n")


# 2. ASK THE MODEL #################################

# Same request as 05_vlms_local.py and 05_vlms_cloud.py:
# the image goes in as base64 text, next to the prompt.
def query(image_file_path, user_prompt, model_name):
    """Send one image + prompt to Ollama (local) or Gemini (cloud) and return text output."""
    with open(image_file_path, "rb") as image_file:
        image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

    # Stub mode: no model is called. These fixed replies let you test the checks.
    if stub == "1":
        return ('{"clock_time": "unknown", "n_people": 9, "n_in_queue": 3, "seats_free": 4, '
                '"confidence": "medium", '
                '"notes": "People at the back are partly hidden."}')
    if stub == "guess":
        return '```json\n{"n_people": "about 9", "n_in_queue": 3, "seats_free": 4}\n```'
    if stub == "mismatch":
        return ('{"clock_time": "08:40", "n_people": 2, "n_in_queue": 5, "seats_free": 4, '
                '"confidence": "high", "notes": "unknown"}')

    if use_cloud:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key and os.path.exists(".env"):
            from dotenv import load_dotenv  # only needed for the cloud
            load_dotenv()
            api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found. Put it in .env for the cloud.")
        url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        body = {
            "model": model_name,
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": user_prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
            ]}],
        }
        # Retry a busy server up to three times, waiting 2, 4, then 8 seconds.
        for wait in (2, 4, 8, None):
            response = requests.post(url, headers=headers, json=body, timeout=600)
            if response.status_code not in (429, 500, 503):
                break
            if wait is None:
                raise RuntimeError(f"The cloud service kept answering with status {response.status_code}. Try again later.")
            time.sleep(wait)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    body = {
        "model": model_name,
        "messages": [{"role": "user", "content": user_prompt, "images": [image_base64]}],
        "stream": False,
    }
    response = requests.post("http://127.0.0.1:11434/api/chat", json=body, timeout=600)
    response.raise_for_status()
    return response.json()["message"]["content"]


reply = query(image_path, prompt, model)
print("Raw reply:\n" + reply + "\n")


# 3. PARSE THE REPLY #################################

# Models often wrap JSON in ```json fences even when told not to.
# We strip the fences, then parse. Anything else that fails to parse is refused.
def parse_reply(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    return json.loads(text)


try:
    record = parse_reply(reply)
except json.JSONDecodeError:
    print("REFUSED: the reply is not JSON. No row written.")
    sys.exit(1)


# 4. VALIDATE AGAINST THE SCHEMA #######################

# Each field is checked by its type. A problem is a sentence, so the person
# reading the output knows exactly which field failed and why.
def validate(record, schema):
    problems = []
    if not isinstance(record, dict):
        return ["the reply is not a JSON object"]
    for field in schema["fields"]:
        name = field["name"]
        if name not in record:
            problems.append(f"{name}: missing")
            continue
        value = record[name]
        if field.get("allow_unknown") and value == "unknown":
            continue
        if field["type"] == "integer":
            # True and False count as numbers in Python, so we rule them out first.
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                problems.append(f"{name}: {value!r} is not a whole number or \"unknown\"")
        elif field["type"] == "choice":
            if value not in field["choices"]:
                problems.append(f"{name}: {value!r} is not one of {field['choices']}")
        elif not isinstance(value, str):
            problems.append(f"{name}: {value!r} is not text")
    extra = [k for k in record if k not in [f["name"] for f in schema["fields"]]]
    for k in extra:
        problems.append(f"{k}: not in the schema")

    # A rule the schema cannot say by itself: the queue is part of the count.
    counts = [record.get(k) for k in ("n_people", "n_in_queue")]
    if all(isinstance(c, int) and not isinstance(c, bool) for c in counts):
        if counts[1] > counts[0]:
            problems.append(f"counts: {counts[1]} in the queue is more than {counts[0]} people")
    return problems


problems = validate(record, schema)
if problems:
    print("REFUSED: the reply breaks the schema. No row written.")
    for p in problems:
        print("  - " + p)
    sys.exit(1)


# 5. WRITE THE CSV ROW #################################

# The photo and model columns come from us, not from the model.
# We write the header only when the file is new.
columns = ["photo", "model"] + [f["name"] for f in schema["fields"]]
row = {"photo": os.path.basename(image_path), "model": "stub" if stub else model}
row.update({f["name"]: record[f["name"]] for f in schema["fields"]})

is_new = not os.path.exists(csv_path)
with open(csv_path, "a", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=columns)
    if is_new:
        writer.writeheader()
    writer.writerow(row)

print(f"OK: one row written to {csv_path}")
print(row)

# An ethical system keeps the row and deletes the photo when it is done.
# Here we leave the photo alone: it is course material.
