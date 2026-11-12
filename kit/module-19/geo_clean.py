# geo_clean.py
# Standardise messy addresses with a model, then geocode them with a lookup, never with the model.
# Course kit, module 19

# Run from the folder that holds this file:  python geo_clean.py
# Set LLM_STUB=1 to use the saved replies in data/stub_replies.json instead of a model.

# 0. SETUP ###################################

import csv
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

# Work inside this script's own folder, so data/ and output/ resolve.
HERE = Path(__file__).resolve().parent
os.chdir(HERE)

RAW_PATH = HERE / "data" / "addresses_raw.csv"
GAZETTEER_PATH = HERE / "data" / "gazetteer.csv"
STUB_PATH = HERE / "data" / "stub_replies.json"
OUT_DIR = HERE / "output"
OUT_CSV = OUT_DIR / "addresses_clean.csv"
CHANGES_PATH = OUT_DIR / "changes.jsonl"
OUT_DIR.mkdir(exist_ok=True)

# Which model to ask. The default is Google's free Gemini tier. The free tier may use your prompts
# to improve Google's products, so send only public or made-up data.
# To use your own computer instead: LLM_BASE_URL=http://localhost:11434/v1 and LLM_MODEL=granite4:3b
# (run `ollama pull granite4:3b` first). The local path needs no key.
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai")
LLM_MODEL = os.environ.get("LLM_MODEL", "gemini-flash-lite-latest")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
LLM_STUB = os.environ.get("LLM_STUB", "") == "1"

# The model may fill these five text fields and nothing else.
FIELDS = ["house_number", "street", "unit", "city", "state"]

# Below this confidence (1 = low, 2 = medium, 3 = high) we do not trust the model's fields.
MIN_CONFIDENCE = 2

# Tell the model its job, and tell it plainly that coordinates are not its job.
SYSTEM_PROMPT = (
    "You standardise one US street address at a time. Reply with JSON only, with the keys "
    "house_number, street, unit, city, state, confidence, reason. Use upper case. Write street "
    "types and directions in their short form (ST, AVE, RD, WAY, N, S, E, W). Put an apartment "
    "or suite in unit. confidence is 1 (low), 2 (medium) or 3 (high). reason is one short "
    "sentence saying what you changed and why. If the text is not an address, leave "
    "house_number and street empty and set confidence to 1. Never give a latitude, a longitude "
    "or a zip code you were not shown."
)

# 1. LOAD DATA ###################################

with open(RAW_PATH, newline="", encoding="utf-8") as f:
    raw_rows = list(csv.DictReader(f))

# The gazetteer stands in for a real geocoding service: a known address goes in,
# a measured coordinate comes out. Its key is house number + street + city + state.
with open(GAZETTEER_PATH, newline="", encoding="utf-8") as f:
    gazetteer = {
        (g["house_number"], g["street"], g["city"], g["state"]): (g["lat"], g["lon"])
        for g in csv.DictReader(f)
    }

print(f"Loaded {len(raw_rows)} addresses and {len(gazetteer)} gazetteer entries.")

# 2. ASK THE MODEL ###################################

def ask_model(row_id, address_raw):
    """Return the model's reply for one address as a Python dict."""
    if LLM_STUB:
        # Stub mode: the saved reply for this row, so the checks run without a model.
        with open(STUB_PATH, encoding="utf-8") as f:
            return json.load(f)[row_id]
    body = {
        "model": LLM_MODEL,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": address_raw},
        ],
    }
    local = LLM_BASE_URL.startswith(("http://localhost", "http://127.0.0.1"))
    if not local and not GEMINI_API_KEY:
        raise SystemExit("Set GEMINI_API_KEY, or set LLM_BASE_URL to a local Ollama address.")
    headers = {"Content-Type": "application/json",
               "Authorization": "Bearer " + ("ollama" if local else GEMINI_API_KEY)}
    req = urllib.request.Request(
        f"{LLM_BASE_URL}/chat/completions", data=json.dumps(body).encode("utf-8"), headers=headers
    )
    # Retry on 429, 500 and 503: wait 2, 4, then 8 seconds, then stop.
    for wait in (2, 4, 8, None):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                reply = json.loads(resp.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 503) or wait is None:
                raise SystemExit(f"The model call failed with HTTP status {e.code}.")
            time.sleep(wait)
    text = reply["choices"][0]["message"]["content"].strip()
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(text)

# 3. GUARD THE REPLY ###################################

changes = []  # one entry per changed field, written to output/changes.jsonl

def log_change(row_id, field, old, new, reason, by):
    changes.append({"row_id": row_id, "field": field, "old": old, "new": new,
                    "reason": reason, "by": by})

def guard(row_id, address_raw, reply):
    """Keep only the five text fields, and say why anything else was dropped."""
    # The model is not allowed to place a point on the map. Drop any coordinate it offers.
    for key in ["lat", "lon", "latitude", "longitude", "zip"]:
        if key in reply:
            log_change(row_id, key, "", str(reply[key]),
                       "Dropped: coordinates and zip codes come from the geocoder, not the model.",
                       "guard")
    try:
        confidence = int(reply.get("confidence", 1))
    except (TypeError, ValueError):
        confidence = 1
    reason = str(reply.get("reason", "")).strip() or "The model gave no reason."
    fields = {k: str(reply.get(k, "") or "").strip().upper() for k in FIELDS}
    return fields, confidence, reason

# 4. GEOCODE WITH A LOOKUP, NOT THE MODEL ###################################

out_rows = []
for row in raw_rows:
    row_id, address_raw = row["row_id"], row["address_raw"]
    fields, confidence, reason = guard(row_id, address_raw, ask_model(row_id, address_raw))
    out = {"row_id": row_id, "address_raw": address_raw, **{k: "" for k in FIELDS},
           "address_std": "", "confidence": confidence, "status": "unresolved",
           "lat": "", "lon": "", "geocode_source": "", "reason": reason}

    # Too unsure, or no street to look up: keep the row, mark it unresolved, guess nothing.
    if confidence < MIN_CONFIDENCE or not fields["house_number"] or not fields["street"]:
        out["reason"] = f"Unresolved (confidence {confidence}). {reason}"
        out_rows.append(out)
        continue

    # Accept the model's text fields, and log each one with the model's reason.
    for k in FIELDS:
        if fields[k]:
            out[k] = fields[k]
            log_change(row_id, k, address_raw, fields[k], reason, "model")
    line1 = " ".join(x for x in [fields["house_number"], fields["street"], fields["unit"]] if x)
    out["address_std"] = f"{line1}, {fields['city']}, {fields['state']}"

    # The coordinate comes only from the gazetteer. No match means no coordinate.
    key = (fields["house_number"], fields["street"], fields["city"], fields["state"])
    if key in gazetteer:
        out["lat"], out["lon"] = gazetteer[key]
        out["status"], out["geocode_source"] = "resolved", "gazetteer"
        log_change(row_id, "lat,lon", "", f"{out['lat']},{out['lon']}",
                   "Matched the gazetteer on house number, street, city and state.", "geocoder")
    else:
        out["reason"] = f"Unresolved: no gazetteer match. {reason}"
    out_rows.append(out)

# 5. WRITE OUTPUT + CHANGE LOG ###################################

columns = ["row_id", "address_raw", "address_std", *FIELDS, "confidence", "status",
           "lat", "lon", "geocode_source", "reason"]
with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=columns)
    writer.writeheader()
    writer.writerows(out_rows)
with open(CHANGES_PATH, "w", encoding="utf-8") as f:
    for c in changes:
        f.write(json.dumps(c) + "\n")

n_resolved = sum(r["status"] == "resolved" for r in out_rows)
print(f"Wrote {OUT_CSV.name}: {n_resolved} resolved, {len(out_rows) - n_resolved} unresolved.")
print(f"Wrote {CHANGES_PATH.name}: {len(changes)} logged changes.")
