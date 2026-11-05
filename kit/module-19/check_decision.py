# check_decision.py
# The lab's decision check: read DECISION.md and test that it is complete and tied to the audit log.
# Course kit, module 19

# A script cannot tell whether your cut-off is wise. It can tell whether you wrote the decision
# down in full: a cut-off, two alternatives, a reason that cites real counts from your own
# audit log, and a split of fields between the model and the code. A person reads the rest.

# Run from this folder after geo_clean ran:
#   python3 check_decision.py                 # your DECISION.md
#   DECISION_STUB=1 python3 check_decision.py # the saved example in example/ (stub mode)
#   DECISION_STUB=bad python3 check_decision.py   # a saved bad example: must fail
# Prints one PASS or FAIL line per check and exits 1 if any check fails.

# 0. SETUP ###################################

import csv
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUB = os.environ.get("DECISION_STUB", "")
if STUB == "bad":
    DECISION = HERE / "example" / "DECISION_bad.md"
elif STUB:
    DECISION = HERE / "example" / "DECISION.md"
else:
    DECISION = HERE / "DECISION.md"
OUT = HERE / "output" / "addresses_clean.csv"
CHANGES = HERE / "output" / "changes.jsonl"

TEXT_FIELDS = ["house_number", "street", "unit", "city", "state"]  # what a model may read
MEASURED = ["lat", "lon"]                                         # what code must measure
SECTIONS = ["Cut-off", "Alternatives", "Reason", "Routed to the model",
            "Measured by code", "Model or geocoder"]

results = []
def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))

# 1. LOAD ###################################

if not DECISION.exists():
    print(f"FAIL  {DECISION.name} is missing: copy example/DECISION.md and write your own")
    sys.exit(1)
if not OUT.exists() or not CHANGES.exists():
    print("FAIL  output/ is missing: run geo_clean first")
    sys.exit(1)

text = DECISION.read_text(encoding="utf-8")
sections = {}
for m in re.finditer(r"^## (.+?)\s*\n(.*?)(?=^## |\Z)", text, flags=re.M | re.S):
    sections[m.group(1).strip()] = m.group(2).strip()

out = list(csv.DictReader(open(OUT, newline="", encoding="utf-8")))
changes = [json.loads(l) for l in CHANGES.read_text(encoding="utf-8").splitlines() if l.strip()]
counts = {
    "logged changes": len(changes),
    "rows": len(out),
    "resolved rows": sum(r["status"] == "resolved" for r in out),
    "unresolved rows": sum(r["status"] == "unresolved" for r in out),
    "guard drops": sum(c.get("by") == "guard" for c in changes),
    "model changes": sum(c.get("by") == "model" for c in changes),
    "geocoder lines": sum(c.get("by") == "geocoder" for c in changes),
}
print(f"Loaded {DECISION.name} with {len(sections)} sections; the audit log has {counts['logged changes']} lines.")

def bullets(name):
    return [re.sub(r"^[-*]\s*", "", l).strip() for l in sections.get(name, "").splitlines()
            if l.strip().startswith(("-", "*"))]

cutoff_text = sections.get("Cut-off", "").strip()
cutoff = int(cutoff_text) if cutoff_text in ("1", "2", "3") else None

# 2. THE CHECKS ###################################

# D1: every section is there and none is empty.
empty = [s for s in SECTIONS if not sections.get(s)]
check("D1 every section is present and filled in", not empty, f"missing or empty {empty}")

# D2: the cut-off is a value the confidence scale can take: 1, 2 or 3.
check("D2 the cut-off is 1, 2 or 3", cutoff is not None, f"found '{cutoff_text}'")

# D3: two alternatives, each a different cut-off from the one chosen, each with an effect.
alts = bullets("Alternatives")
alt_values = []
for a in alts:
    m = re.search(r"\b([1-3])\b", a)
    alt_values.append(int(m.group(1)) if m else None)
ok = (len(alts) >= 2 and cutoff is not None and None not in alt_values
      and cutoff not in alt_values and len(set(alt_values)) == len(alt_values)
      and all(len(a.split()) >= 8 for a in alts))
check("D3 two other cut-offs, each with what it would change", ok,
      f"{len(alts)} alternatives, values {alt_values}")

# D4: the reason cites the audit log and at least two real counts taken from it.
reason = sections.get("Reason", "")
numbers = {int(n) for n in re.findall(r"\b\d+\b", reason)}
hits = {k: v for k, v in counts.items() if v in numbers}
check("D4 the reason cites the audit log with at least two of its real counts",
      "changes.jsonl" in reason and len(hits) >= 2,
      f"mentions changes.jsonl: {'changes.jsonl' in reason}, real counts found: {len(hits)}")

# D5: the reason weighs a cost: it names what a wrong place costs.
check("D5 the reason names what a wrong place costs",
      bool(re.search(r"\bcosts?\b", reason, re.I)) and bool(re.search(r"\bwrong\b", reason, re.I)))

# D6: routed versus measured. Text fields go to the model, lat and lon never do.
routed = [b.split()[0].strip("`") for b in bullets("Routed to the model")]
measured = [b.split()[0].strip("`") for b in bullets("Measured by code")]
ok = (bool(routed) and set(routed) <= set(TEXT_FIELDS)
      and set(MEASURED) <= set(measured) and not set(routed) & set(measured))
check("D6 text fields routed to the model, lat and lon measured by code", ok,
      f"routed {routed}, measured {measured}")

# D7: the model-or-geocoder choice weighs cost, accuracy and what each can be held to.
choice = sections.get("Model or geocoder", "").lower()
check("D7 the model-or-geocoder choice weighs cost, accuracy and what each is held to",
      all(w in choice for w in ("cost", "accuracy", "held to")))

# 3. SUMMARY ###################################

print(f"{sum(results)} of {len(results)} checks pass.")
sys.exit(0 if all(results) else 1)
