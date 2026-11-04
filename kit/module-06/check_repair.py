# check_repair.py
# The lab's checks: compare the database and the audit log against the raw file and the rules.
# Course kit, module 6

# Run from this folder after repair_table ran:  python check_repair.py
# Prints one PASS or FAIL line per check and exits 1 if any check fails.

# 0. SETUP ###################################

import csv
import json
import sqlite3
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "inventory_raw.csv"
ACCEPTED = HERE / "data" / "accepted.json"
DB = HERE / "output" / "inventory.db"
AUDIT = HERE / "output" / "audit.jsonl"
COLUMNS = ["row_id", "sku", "qty_on_hand", "last_restock", "category"]

results = []
def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))

# 1. LOAD ###################################

if not DB.exists() or not AUDIT.exists():
    print("FAIL  output/ is missing: run repair_table first")
    sys.exit(1)
with open(RAW, newline="", encoding="utf-8") as f:
    raw = list(csv.DictReader(f))
audit = [json.loads(l) for l in AUDIT.read_text(encoding="utf-8").splitlines() if l.strip()]
accepted = set(json.loads(ACCEPTED.read_text(encoding="utf-8")))
con = sqlite3.connect(DB)
db = {r[0]: dict(zip(COLUMNS, ["" if v is None else str(v) for v in r]))
      for r in con.execute("SELECT row_id, sku, qty_on_hand, last_restock, category FROM inventory")}
con.close()
applied = [a for a in audit if a["status"] == "applied"]

# 2. THE CHECKS ###################################

# C1: row counts preserved: the same row_ids go in and come out, each once.
check("C1 row count and row ids preserved",
      sorted(int(r["row_id"]) for r in raw) == sorted(db), f"raw {len(raw)} rows, database {len(db)} rows")

# C2: no value changed without an audit line that names the old value, the new value and a reason.
logged = {(a["row_id"], a["column"]): a for a in applied if str(a["reason"]).strip()}
silent = []
for r in raw:
    rid = int(r["row_id"])
    for col in COLUMNS[1:]:
        if rid in db and db[rid][col] != r[col] and (rid, col) not in logged:
            silent.append(f"{rid}:{col}")
check("C2 no value changed without an audit line and a reason", not silent, f"silent {silent}")

# C3: every audit line matches what the database now holds, and starts from the raw value.
bad = [f"{a['row_id']}:{a['column']}" for a in applied
       if a["row_id"] not in db or a["old_value"] != next(
           (r[a["column"]] for r in raw if int(r["row_id"]) == a["row_id"]), None)
       or a["new_value"] != db[a["row_id"]][a["column"]]]
check("C3 audit lines agree with the raw file and the database", not bad, f"lines {bad}")

# C4: every edit the model made reached the table only through the reviewer's list.
unreviewed = [f"{a['row_id']}:{a['column']}" for a in applied
              if a["by"] == "model" and f"{a['row_id']}:{a['column']}" not in accepted]
check("C4 every model edit was reviewer-accepted", not unreviewed, f"unreviewed {unreviewed}")

# C5: types valid: counts are positive whole numbers, dates are real YYYY-MM-DD, categories are allowed.
def valid(col, v):
    if v == "":
        return True
    if col == "qty_on_hand":
        return v.isdigit() and int(v) > 0
    if col == "last_restock":
        try:
            date.fromisoformat(v)
            return len(v) == 10
        except ValueError:
            return False
    if col == "category":
        return v in ("Electronics", "Food")
    return True
bad = [f"{rid}:{col}" for rid, r in db.items() for col in COLUMNS[2:] if not valid(col, r[col])]
check("C5 every value has a valid type", not bad, f"invalid {bad}")

# C6: the audit is replayable: applying its lines to the raw file, in order, rebuilds the database.
replay = {int(r["row_id"]): dict(r) for r in raw}
for a in applied:
    replay[a["row_id"]][a["column"]] = a["new_value"]
diff = [rid for rid in db if rid not in replay or any(replay[rid][c] != db[rid][c] for c in COLUMNS[1:])]
check("C6 replaying the audit on the raw file rebuilds the database", not diff, f"rows {diff}")

# 3. RESULT ###################################

print(f"{sum(results)} of {len(results)} checks pass.")
sys.exit(0 if all(results) else 1)
