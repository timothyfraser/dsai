# check_decision.py
# Read a DECISION.md and check that the data-source decision is complete.
# Course kit, module 1
#
# Topic: Choosing an API you can build on
#
# A query that returns 200 is half the lab. The other half is the decision
# behind it: which source, against which alternatives, for what reason, on
# what evidence. This script checks that every part is written down. It cannot
# check that the reasoning is good: a reviewer reads the file for that. It
# calls no server and no model, so it runs anywhere.
#
# No python packages to install: it uses only the standard library.
#
# Run it from this folder:
#   python3 check_decision.py path/to/your/DECISION.md   # your own file
#   DECISION_STUB=1 python3 check_decision.py            # the bundled example, which passes
#   DECISION_STUB=bad python3 check_decision.py          # broken on purpose, to show FAIL
# Exits 1 if any check fails.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import os  # for the stub switch
import re  # for finding the sections and the patterns inside them
import sys  # for the file argument and the exit code
from pathlib import Path  # for reading the file

## 0.2 Configuration #################################

HERE = Path(__file__).resolve().parent
STUB = os.environ.get("DECISION_STUB", "")
if STUB == "1":
    PATH = HERE / "example" / "DECISION.md"
elif STUB == "bad":
    PATH = HERE / "example_bad" / "DECISION.md"
else:
    PATH = Path(sys.argv[1] if len(sys.argv) > 1 else "DECISION.md")

# The four sections the lab asks for, by their headings.
SECTIONS = ["Source", "Alternatives", "Reason", "Evidence"]
# The criteria the module's table compares. A reason names at least two.
CRITERIA = ("authentication", "key", "rate limit", "format", "json", "licence", "license", "terms", "reliab", "updated", "update")

results = []
def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))

# 1. READ THE SECTIONS ###################################

if not PATH.exists():
    print(f"FAIL  no file at {PATH}: write a DECISION.md with Source, Alternatives, Reason and Evidence")
    sys.exit(1)
text = PATH.read_text(encoding="utf-8")

# Split on "## Heading" lines. Each section's body is the text up to the next heading.
parts = re.split(r"^##\s+(.+?)\s*$", text, flags=re.M)
body = {parts[i].strip().split()[0].lower(): parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}
def sec(name):
    return body.get(name.lower(), "")
def bullets(s):
    return [l.strip()[1:].strip() for l in s.splitlines() if l.strip().startswith(("-", "*"))]
print(f"Read {PATH}: sections {sorted(body)}\n")

# 2. THE CHECKS ###################################

# D1: every section is there and has words in it.
empty = [s for s in SECTIONS if len(sec(s).split()) < 3]
check("D1 Source, Alternatives, Reason and Evidence are present and filled in", not empty, f"missing or short: {empty}")

# D2: at least two alternatives, each with a reason it lost (more than a bare name).
alts = bullets(sec("Alternatives"))
thin = [a for a in alts if len(a.split()) < 6]
check("D2 at least two alternatives, each with a reason", len(alts) >= 2 and not thin,
      f"{len(alts)} alternatives, {len(thin)} too short to hold a reason")

# D3: the reason is set against the table: it names at least two of its criteria.
reason = sec("Reason").lower()
named = {c for c in CRITERIA if c in reason}
check("D3 the reason names at least two criteria from the table", len(named) >= 2, "name criteria such as the rate limit and the licence")

# D4: the evidence is one real reply: a status 200 and an address or a row count.
ev = sec("Evidence")
check("D4 the evidence names a 200 status and the request or the rows it returned",
      bool(re.search(r"\b200\b", ev)) and bool(re.search(r"https?://|\b\d+\s+rows?\b", ev)),
      "write the status and either the address you called or the row count")

# D5: no secret in the file. A long run of letters and digits looks like a key.
leaked = re.findall(r"\b[A-Za-z0-9_\-]{32,}\b", text)
check("D5 no key value is written in the file", not leaked, f"{len(leaked)} key-shaped strings")

# 3. SUMMARY ###################################

print(f"\n{sum(results)} of {len(results)} checks pass. A reviewer still reads whether the reason holds for the stakeholder's need.")
sys.exit(0 if all(results) else 1)
