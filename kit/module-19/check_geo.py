# check_geo.py
# The lab's checks: compare output/ against the rules and the held-out fixture.
# Course kit, module 19

# Run from this folder after geo_clean ran:  python check_geo.py
# Prints one PASS or FAIL line per check and exits 1 if any check fails.

# 0. SETUP ###################################

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "addresses_raw.csv"
GAZ = HERE / "data" / "gazetteer.csv"
EXPECTED = HERE / "data" / "expected.csv"  # held out: the model never sees this file
OUT = HERE / "output" / "addresses_clean.csv"
CHANGES = HERE / "output" / "changes.jsonl"
FIELDS = ["house_number", "street", "unit", "city", "state"]

def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

results = []
def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))

# 1. LOAD ###################################

if not OUT.exists() or not CHANGES.exists():
    print("FAIL  output/ is missing: run geo_clean first")
    sys.exit(1)
raw, gaz, expected, out = read_csv(RAW), read_csv(GAZ), read_csv(EXPECTED), read_csv(OUT)
changes = [json.loads(l) for l in CHANGES.read_text(encoding="utf-8").splitlines() if l.strip()]
gaz_points = {(g["lat"], g["lon"]) for g in gaz}

# 2. THE CHECKS ###################################

# C1: every input row comes out exactly once.
check("C1 every input row appears once in the output",
      sorted(r["row_id"] for r in out) == sorted(r["row_id"] for r in raw))

# C2: no invented coordinates. A coordinate appears only on a resolved row, from the gazetteer.
bad = [r["row_id"] for r in out if (r["lat"] or r["lon"]) and
       (r["status"] != "resolved" or r["geocode_source"] != "gazetteer"
        or (r["lat"], r["lon"]) not in gaz_points)]
check("C2 no invented coordinates", not bad, f"rows {bad}")

# C3: every changed field has a log line with a reason.
logged = {(c["row_id"], c["field"]) for c in changes if str(c.get("reason", "")).strip()}
missing = [f"{r['row_id']}:{k}" for r in out for k in FIELDS if r[k] and (r["row_id"], k) not in logged]
missing += [f"{r['row_id']}:lat,lon" for r in out if r["lat"] and (r["row_id"], "lat,lon") not in logged]
check("C3 every changed field is logged with a reason", not missing, f"missing {missing}")

# C4: every row says how sure it is: confidence 1 to 3, status resolved or unresolved.
bad = [r["row_id"] for r in out if r["status"] not in ("resolved", "unresolved")
       or r["confidence"] not in ("1", "2", "3")]
check("C4 every row has a confidence and a status", not bad, f"rows {bad}")

# C5: unsure rows guess nothing: unresolved rows carry no coordinate.
bad = [r["row_id"] for r in out if r["status"] == "unresolved" and (r["lat"] or r["lon"])]
check("C5 unresolved rows carry no coordinate", not bad, f"rows {bad}")

# C6: the output matches the held-out fixture on address, status and coordinate.
by_id = {r["row_id"]: r for r in out}
diff = [e["row_id"] for e in expected if e["row_id"] not in by_id or
        any(by_id[e["row_id"]][k] != e[k] for k in ["address_std", "status", "lat", "lon"])]
check("C6 output matches the held-out fixture", not diff, f"rows {diff}")

# 3. RESULT ###################################

print(f"{sum(results)} of {len(results)} checks pass.")
sys.exit(0 if all(results) else 1)
