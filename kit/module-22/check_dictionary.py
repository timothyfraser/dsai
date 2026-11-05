# check_dictionary.py
# Check C2: the data dictionary covers every field the API returns.
# Course kit, module 22
#
# Run it from your team folder:  python3 check_dictionary.py
# It reads data_dictionary.csv and saved/api_response.json (a response you saved from your API).
# Prints one PASS or FAIL line and exits 1 on a FAIL. Stdlib only.

# 0. SETUP ###################################

import csv   # for reading the dictionary
import json  # for reading the saved response
import sys   # for the exit code
from pathlib import Path  # for file paths

TEAM = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
DICT = TEAM / "data_dictionary.csv"
RESPONSE = TEAM / "saved" / "api_response.json"
TYPES = {"string", "integer", "number", "boolean", "timestamp", "date"}
NEEDED = ["column", "meaning", "type", "unit", "allowed", "null_means", "source"]

# 1. READ ###################################

problems = []
with open(DICT, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    missing_cols = [c for c in NEEDED if c not in (reader.fieldnames or [])]
    entries = {row["column"]: row for row in reader} if not missing_cols else {}
if missing_cols:
    problems.append(f"dictionary is missing columns: {', '.join(missing_cols)}")
try:
    response = json.loads(RESPONSE.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as err:
    print(f"FAIL  C2 the dictionary covers every field the API returns  (cannot read {RESPONSE}: {err})")
    sys.exit(1)

# 2. CHECK EVERY FIELD ###################################

for field in response:
    e = entries.get(field)
    if e is None:
        problems.append(f"{field}: returned by the API but not in the dictionary")
        continue
    if e["type"].strip() not in TYPES:
        problems.append(f"{field}: type '{e['type']}' is not one of {sorted(TYPES)}")
    # A unit of "none" is an answer; an empty cell is not.
    if not e["unit"].strip():
        problems.append(f"{field}: no unit (write 'none' if it has none)")
    # Null is not zero: the dictionary must say what a missing value means.
    if not e["null_means"].strip():
        problems.append(f"{field}: no rule for what a null means")
    # A time with no zone is two times: store UTC, convert only for display.
    if e["type"].strip() == "timestamp" and not (e["unit"].strip() == "UTC" or "/" in e["unit"]):
        problems.append(f"{field}: a timestamp whose unit names no time zone")

print(f"{'PASS' if not problems else 'FAIL'}  C2 the dictionary covers every field the API returns  ("
      + ("; ".join(problems) if problems else f"{len(response)} fields, {len(entries)} dictionary rows") + ")")
sys.exit(1 if problems else 0)
