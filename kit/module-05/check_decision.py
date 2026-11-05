# check_decision.py
# Read a team's DECISION.md and check that the tool-server decision is complete.
# Course kit, module 5
#
# Topic: Which tools go behind an MCP server, and which do not
#
# A deployed server that passes W1 to W8 is half the lab. The other half is
# the decision behind it: which tools went behind the server and which stayed
# a function or a REST route, two alternatives you weighed, the reason (against
# the table in Step 4), the evidence (the agent's tool call log), and who may
# call the public address and holds its key. This script checks that every
# part is written down. It cannot check that the reasoning is good: a reviewer
# reads the file for that. It calls no server and no model, so it runs anywhere.
#
# No python packages to install: it uses only the standard library.
#
# Run it from this folder:
#   DECISION_STUB=1 python3 check_decision.py     # the saved example, which passes
#   DECISION_STUB=bad python3 check_decision.py   # broken on purpose, to show FAIL
#   python3 check_decision.py path/to/your/DECISION.md   # your team's own file
# Exits 1 if any check fails.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import os  # for the stub switch
import re  # for finding the sections and the patterns inside them
import sys  # for the file argument and the exit code
from pathlib import Path  # for reading the file

## 0.2 Configuration #################################

# The stub switch picks a saved file so the check runs with no team file at hand.
STUB = os.environ.get("DECISION_STUB", "")
HERE = Path(__file__).resolve().parent
if STUB == "1":
    PATH = HERE / "example" / "DECISION.md"
elif STUB == "bad":
    PATH = HERE / "example_bad" / "DECISION.md"
else:
    PATH = Path(sys.argv[1] if len(sys.argv) > 1 else "DECISION.md")

# The six sections the lab asks for, by their headings.
SECTIONS = ["Behind", "Kept", "Alternatives", "Reason", "Evidence", "Callers"]
# The columns of the Step 5 table. A reason names at least two of them.
TRADE_OFFS = ("hop", "latency", "key", "public", "address", "state", "memory", "reuse", "discover", "caller")
# Answers that mean "nobody in particular" when written as a key holder.
NOBODY = ("everyone", "all of us", "the whole team", "the team", "anyone", "the agent", "the ai")

results = []
def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))

# 1. READ THE SECTIONS ###################################

if not PATH.exists():
    print(f"FAIL  no file at {PATH}: copy example/DECISION.md and fill it in")
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
check("D1 all six sections are present and filled in", not empty, f"missing or empty: {empty}")

# D2: at least one tool behind the server and at least one kept out, each with a why.
behind, kept = bullets(sec("Behind")), bullets(sec("Kept"))
check("D2 at least one tool behind the server and one kept out",
      len(behind) >= 1 and len(kept) >= 1, f"{len(behind)} behind, {len(kept)} kept out")

# D3: two alternatives the team weighed, written as separate bullets.
alts = bullets(sec("Alternatives"))
check("D3 at least two alternatives considered", len(alts) >= 2, f"{len(alts)} alternatives")

# D4: the reason names a cost or a benefit from the table, at least two of them.
reason = sec("Reason").lower()
named = [t for t in TRADE_OFFS if t in reason]
check("D4 the reason names at least two columns of the table", len(named) >= 2,
      "name the caller, the hop, the key, the public address or the missing state")

# D5: the evidence is the agent's tool call log: a live address and a tools/call line.
ev = sec("Evidence")
check("D5 the evidence has a live address and a tools/call line from the log",
      bool(re.search(r"https?://", ev)) and "tools/call" in ev,
      "paste the live /mcp address and the log line where the agent called your tool")

# D6: a named holder for the key, and who may call the address.
cal = sec("Callers")
key = next((l for l in cal.splitlines() if "key" in l.lower()), "")
holder = key.split(":", 1)[1].strip().lower() if ":" in key else ""
check("D6 a named person holds the key, and the callers are named",
      bool(holder) and not any(holder.startswith(n) for n in NOBODY) and "call" in cal.lower(),
      f"key line is '{key.strip()}'")

# D7: no secret in the file. A long run of letters and digits looks like a key.
leaked = re.findall(r"\b[A-Za-z0-9_\-]{32,}\b", text)
check("D7 no key value is written in the file", not leaked, f"{len(leaked)} key-shaped strings")

# 3. SUMMARY ###################################

print(f"\n{sum(results)} of {len(results)} checks pass. A reviewer still reads the reason.")
sys.exit(0 if all(results) else 1)
