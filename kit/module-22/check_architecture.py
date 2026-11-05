# check_architecture.py
# Checks C1 and C6: the stores table, the decision, and who may read and write each store.
# Course kit, module 22
#
# Run it from the folder that holds your ARCHITECTURE.md:  python3 check_architecture.py
# or name the folder:  python3 check_architecture.py path/to/team
# Prints one PASS or FAIL line per check and exits 1 if any check fails. Stdlib only.

# 0. SETUP ###################################

import json  # for the saved RLS query result
import re    # for reading the Markdown tables
import sys   # for the exit code
from pathlib import Path  # for file paths

TEAM = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
ARCH = TEAM / "ARCHITECTURE.md"
RLS = TEAM / "saved" / "rls.json"
ROLES = {"source of truth", "derived"}
DECISION_FIELDS = ["Chosen", "Alternative 1", "Alternative 2", "Reason", "Evidence"]

failed = 0
def report(name, ok, detail=""):
    global failed
    failed += 0 if ok else 1
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail else ""))

# 1. READ THE FILE ###################################

if not ARCH.exists():
    report("C1 ARCHITECTURE.md names every store and the decision", False, f"{ARCH} not found")
    report("C6 an access rule for every store", False, f"{ARCH} not found")
    sys.exit(1)
text = ARCH.read_text(encoding="utf-8")

def section(heading):
    """Return the text under one '## heading', up to the next '## '."""
    m = re.search(rf"^## {heading}\s*$(.*?)(?=^## |\Z)", text, flags=re.M | re.S)
    return m.group(1) if m else ""

# A row is a line that starts with '|'; the header and the '---' line are skipped.
rows = []
for line in section("Stores").splitlines():
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if not line.strip().startswith("|") or cells[0] in ("Store", "") or set(cells[0]) <= set("-: "):
        continue
    rows.append(dict(zip(["store", "holds", "role", "rebuild", "writers", "readers"], cells)))

# 2. C1: EVERY STORE IS SOURCE OF TRUTH OR DERIVED, AND THE DECISION IS COMPLETE ###########

problems = []
if not rows:
    problems.append("no rows under '## Stores'")
for r in rows:
    role = r.get("role", "").lower()
    if role not in ROLES:
        problems.append(f"{r['store']}: role '{r.get('role', '')}' is not 'source of truth' or 'derived'")
    # A derived copy is only derived if you can say how to throw it away and rebuild it.
    if role == "derived" and not re.search(r"`[^`]+`", r.get("rebuild", "")):
        problems.append(f"{r['store']}: derived, but no rebuild command in backticks")
    if role == "source of truth" and not r.get("rebuild", "").strip("- "):
        problems.append(f"{r['store']}: source of truth, but no backup line")
if rows and not any(r.get("role", "").lower() == "source of truth" for r in rows):
    problems.append("no store is marked source of truth")

decision = section("Decision")
for field in DECISION_FIELDS:
    m = re.search(rf"\*\*{field}:\*\*\s*(.+)", decision)
    value = m.group(1).strip() if m else ""
    # The template's placeholders start with '(' so an unfilled template fails here.
    if not value or value.startswith("("):
        problems.append(f"decision: '{field}' is missing or still the template's text")
report("C1 ARCHITECTURE.md names every store and the decision", not problems,
       "; ".join(problems) if problems else f"{len(rows)} stores, decision complete")

# 3. C6: WHO MAY READ AND WRITE EACH STORE, AND RLS WHERE THE BROWSER READS POSTGRES ###########

problems = []
for r in rows:
    for col in ("writers", "readers"):
        if not r.get(col, "").strip("- ") or r[col].startswith("("):
            problems.append(f"{r['store']}: no {col}")

# The browser holds only the publishable key, and that key is safe only behind RLS.
hosted = [r for r in rows if re.search(r"supabase|postgres", r["store"], flags=re.I)]
browser = [r for r in hosted if "browser" in r.get("readers", "").lower()]
if hosted:
    if not RLS.exists():
        problems.append("hosted Postgres store listed, but saved/rls.json is missing")
    else:
        tables = json.loads(RLS.read_text(encoding="utf-8"))
        off = [t["tablename"] for t in tables if not t.get("rowsecurity")]
        if off:
            problems.append(f"RLS is off on: {', '.join(off)}")
    detail = f"{len(rows)} stores; RLS on in saved/rls.json; {len(browser)} read by the browser"
else:
    detail = f"{len(rows)} stores; no hosted Postgres store, so the RLS part does not apply"
report("C6 an access rule for every store", not problems, "; ".join(problems) if problems else detail)

sys.exit(1 if failed else 0)
