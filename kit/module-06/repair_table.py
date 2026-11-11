# repair_table.py
# Repair a messy CSV with a model's proposals, log every change with a reason,
# apply only what a reviewer accepted, and store the clean table in SQLite.
# Course kit, module 6

# Run from the folder that holds this file:  python repair_table.py
# Set LLM_STUB=1 to use the saved proposals in data/stub_proposals.json instead of a model.

# 0. SETUP ###################################

import csv
import json
import os
import sqlite3
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

# Work inside this script's own folder, so data/ and output/ resolve.
HERE = Path(__file__).resolve().parent
os.chdir(HERE)

RAW_PATH = HERE / "data" / "inventory_raw.csv"
STUB_PATH = HERE / "data" / "stub_proposals.json"
ACCEPTED_PATH = HERE / "data" / "accepted.json"  # the reviewer's list: "row_id:column"
OUT_DIR = HERE / "output"
DB_PATH = OUT_DIR / "inventory.db"
AUDIT_PATH = OUT_DIR / "audit.jsonl"
OUT_DIR.mkdir(exist_ok=True)

# Which model to ask. The default is Google's free Gemini tier. The free tier may use your prompts
# to improve Google's products, so send only public or made-up data.
# To use your own computer instead: LLM_BASE_URL=http://localhost:11434/v1 and LLM_MODEL=granite4:3b
# (run `ollama pull granite4:3b` first). The local path needs no key.
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai")
LLM_MODEL = os.environ.get("LLM_MODEL", "gemini-flash-lite-latest")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
LLM_STUB = os.environ.get("LLM_STUB", "") == "1"
ROWS_PER_BATCH = 10

# The model may edit these columns and no others. row_id and sku are keys, not data to repair.
EDITABLE = ["qty_on_hand", "last_restock", "category"]
CATEGORIES = ["Electronics", "Food"]

SYSTEM_PROMPT = (
    "You repair a store inventory table. Reply with JSON only: a list of edits, each with the "
    "keys row_id, column, new_value, reason. column is one of qty_on_hand, last_restock, "
    "category. qty_on_hand is a positive whole number or empty. last_restock is YYYY-MM-DD or "
    "empty. category is exactly Electronics or Food. An unknown or impossible value becomes "
    "an empty string. Never invent a number. reason is one short sentence saying why."
)

# 1. LOAD DATA ###################################

with open(RAW_PATH, newline="", encoding="utf-8") as f:
    raw_rows = list(csv.DictReader(f))
columns = list(raw_rows[0].keys())
print(f"Loaded {len(raw_rows)} rows from {RAW_PATH.name}.")

# 2. ASK THE MODEL FOR PROPOSALS ###################################

def ask_model(rows):
    """Return the model's list of proposed edits for one batch of rows."""
    if LLM_STUB:
        # Stub mode: the saved proposals for these rows, so the checks run without a model.
        ids = {int(r["row_id"]) for r in rows}
        with open(STUB_PATH, encoding="utf-8") as f:
            return [p for p in json.load(f) if p["row_id"] in ids]
    body = {
        "model": LLM_MODEL,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(rows)},
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
    parsed = json.loads(text)
    return parsed.get("edits", []) if isinstance(parsed, dict) else parsed

proposals = []
for i in range(0, len(raw_rows), ROWS_PER_BATCH):
    proposals += ask_model(raw_rows[i:i + ROWS_PER_BATCH])
print(f"The model proposed {len(proposals)} edits.")

# 3. GUARD, THEN LET THE REVIEWER DECIDE ###################################

raw_by_id = {int(r["row_id"]): r for r in raw_rows}
with open(ACCEPTED_PATH, encoding="utf-8") as f:
    accepted = set(json.load(f))

audit = []  # one entry per proposal and per fallback, written to output/audit.jsonl

def log(row_id, column, old, new, reason, by, status):
    audit.append({"n": len(audit) + 1, "row_id": row_id, "column": column, "old_value": old,
                  "new_value": new, "reason": reason, "by": by, "status": status})

edits = {}  # (row_id, column) -> new value, only what survives the guard and the reviewer
for p in proposals:
    rid, col = int(p["row_id"]), str(p["column"])
    new, reason = str(p.get("new_value", "") or "").strip(), str(p.get("reason", "")).strip()
    old = raw_by_id[rid][col] if rid in raw_by_id and col in columns else ""
    # The guard drops edits that break the contract, and says why.
    if rid not in raw_by_id or col not in EDITABLE:
        log(rid, col, old, new, "Rejected by guard: not an editable row or column.", "guard", "rejected")
    elif not reason:
        log(rid, col, old, new, "Rejected by guard: the model gave no reason.", "guard", "rejected")
    elif new == old:
        log(rid, col, old, new, "Rejected by guard: no change.", "guard", "rejected")
    # The reviewer's list is the only way an edit reaches the table.
    elif f"{rid}:{col}" not in accepted:
        log(rid, col, old, new, reason, "model", "not_accepted")
    else:
        edits[(rid, col)] = new
        log(rid, col, old, new, reason, "model", "applied")

# 4. APPLY, THEN VALIDATE ###################################

def is_valid(col, value):
    """True if the value is allowed for the column; empty is always allowed."""
    if value == "":
        return True
    if col == "qty_on_hand":
        return value.isdigit() and int(value) > 0
    if col == "last_restock":
        try:
            date.fromisoformat(value)
            return len(value) == 10
        except ValueError:
            return False
    if col == "category":
        return value in CATEGORIES
    return True

table = []
for r in raw_rows:
    rid, row = int(r["row_id"]), dict(r)
    for col in EDITABLE:
        if (rid, col) in edits:
            row[col] = edits[(rid, col)]
        # A value that is still invalid has no accepted fix. Empty beats wrong, and the audit says so.
        if not is_valid(col, row[col]):
            log(rid, col, row[col], "", "No accepted fix; invalid value set to empty.", "pipeline", "applied")
            row[col] = ""
    table.append(row)

# 5. WRITE THE DATABASE + AUDIT LOG ###################################

if DB_PATH.exists():
    DB_PATH.unlink()
con = sqlite3.connect(DB_PATH)
con.execute("""CREATE TABLE inventory (
    row_id INTEGER PRIMARY KEY,
    sku TEXT NOT NULL,
    qty_on_hand INTEGER CHECK (qty_on_hand IS NULL OR qty_on_hand > 0),
    last_restock TEXT,
    category TEXT CHECK (category IS NULL OR category IN ('Electronics', 'Food'))
)""")
for r in table:
    con.execute("INSERT INTO inventory VALUES (?, ?, ?, ?, ?)", (
        int(r["row_id"]), r["sku"],
        int(r["qty_on_hand"]) if r["qty_on_hand"] else None,
        r["last_restock"] or None, r["category"] or None))
con.commit()
con.close()
with open(AUDIT_PATH, "w", encoding="utf-8") as f:
    for a in audit:
        f.write(json.dumps(a) + "\n")

n_applied = sum(a["status"] == "applied" for a in audit)
print(f"Wrote {DB_PATH.name}: {len(table)} rows in table inventory.")
print(f"Wrote {AUDIT_PATH.name}: {len(audit)} lines, {n_applied} applied.")
