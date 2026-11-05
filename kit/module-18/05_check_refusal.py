# 05_check_refusal.py
# A note that leaves out a required fact must be refused or marked, never filled with a guess.
# Course kit, module 18
#
# Topic: Testing that the system does not invent a value
#
# Runs 03_voice_note_to_work_order.py and reads what it filed.
# Stub mode (default) swaps in two fixed model answers, so it proves the rule and the
# validator, not the model. A stub cannot show that a real model refuses.
# Live mode runs your omitted-fact recording through your real pipeline:
#   REFUSAL_LIVE=1 AUDIO_PATH=my_notes/omitted.wav OMITTED_FIELD=location python3 kit/module-18/05_check_refusal.py
# Run from the top of the course repo. Exit code 0 means every check passed.

# 0. SETUP ###################################

import csv
import json
import os
import subprocess
import sys
import tempfile

KIT_DIR = os.getenv("KIT_DIR", os.path.dirname(os.path.abspath(__file__)))
AUDIO_PATH = os.getenv("AUDIO_PATH", "06_agents/06_jfk_short.wav")
LIVE = os.getenv("REFUSAL_LIVE", "") == "1"
FIELD = os.getenv("OMITTED_FIELD", "location")
# The values that count as "the note did not say". Add your own words here.
UNKNOWN = ("not stated", "unknown", "not given")

# The model answer for a note that left out the location, in two ways it could behave.
BASE = {"asset": "Pump 3", "problem": "Oil is leaking from the seal", "priority": "high",
        "safety_hazard": True, "action_requested": "Send a mechanic", "location": ""}

results = []
def report(ok, name, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))

def run(csv_path, stub_answer=None):
    env = dict(os.environ, AUDIO_PATH=AUDIO_PATH, WORK_ORDERS_CSV=csv_path)
    if not LIVE:
        env.update(AUDIO_STUB="1", LLM_STUB="1", LLM_STUB_JSON=json.dumps(stub_answer))
    return subprocess.run([sys.executable, os.path.join(KIT_DIR, "03_voice_note_to_work_order.py")],
                          capture_output=True, text=True, env=env)

def filed(csv_path):
    if not os.path.exists(csv_path):
        return None
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows[0] if rows else None

scratch = tempfile.mkdtemp(prefix="m18-refusal-")

# 1. THE CHECKS ###################################

if LIVE:
    # R1: with the real models, the omitted fact is refused or marked as unknown. A filled
    # value here is a guess, because the note never said it.
    out = os.path.join(scratch, "live.csv")
    proc = run(out)
    row = filed(out)
    refused = proc.returncode != 0 and row is None
    marked = row is not None and row.get(FIELD, "").strip().lower() in UNKNOWN
    report(refused or marked, f"R1 the omitted '{FIELD}' is refused or marked unknown, not guessed",
           f"filed {FIELD} = {row.get(FIELD) if row else None!r}")
else:
    # R1: a blank for the missing fact is refused and nothing is filed.
    out = os.path.join(scratch, "blank.csv")
    proc = run(out, {**BASE, FIELD: ""})
    report(proc.returncode != 0 and "Work order rejected" in proc.stderr and filed(out) is None,
           f"R1 a blank '{FIELD}' is refused and nothing is filed")

    # R2: an explicit "not stated" is filed as a draft, so a person sees the gap.
    out = os.path.join(scratch, "marked.csv")
    proc = run(out, {**BASE, FIELD: "not stated"})
    row = filed(out)
    report(proc.returncode == 0 and row is not None and row[FIELD] == "not stated" and row["status"] == "draft",
           f"R2 an explicit 'not stated' for '{FIELD}' is filed as a draft")

# 2. SUMMARY ###################################

print(f"\n{results.count(True)} passed, {results.count(False)} failed" + ("" if LIVE else "  (stub: proves the rule, not the model)"))
sys.exit(0 if all(results) else 1)
