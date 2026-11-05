# check_decision.py
# Read a DECISION.md and check that the choice of one agent, many agents or no agent is complete.
# Course kit, module 8
#
# Topic: Splitting a job across agents, decided on purpose
#
# A chain that runs is half the practice. The other half is the decision behind
# it: one agent, several, or plain code; which alternatives lost and why; and
# the log that shows where an error would travel. This script checks that every
# part is written down. It cannot check that the reasoning is good: a reviewer
# reads the file for that. It calls no model and no server, so it runs anywhere.
#
# No python packages to install: it uses only the standard library.
#
# Run it from this folder:
#   DECISION_STUB=1 python3 check_decision.py     # the saved example, which passes
#   DECISION_STUB=bad python3 check_decision.py   # broken on purpose, to show FAIL
#   python3 check_decision.py path/to/your/DECISION.md   # your own file
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
if len(sys.argv) > 1:
    PATH = Path(sys.argv[1])
elif STUB == "bad":
    PATH = HERE / "example_bad" / "DECISION.md"
elif STUB:
    PATH = HERE / "example" / "DECISION.md"
else:
    PATH = Path("DECISION.md")

# The six sections the practice asks for, by their headings.
SECTIONS = ["Job", "Choice", "Alternatives", "Reason", "Evidence", "Checks"]
# The three answers a choice may be.
CHOICES = ("one agent", "many agents", "no agent")
# The columns of the module's table. A reason names at least two.
COLUMNS = ("calls", "tokens", "latency", "error", "test", "plain code", "cost")
# Words that show a check sits at a hand-off.
CHECK_WORDS = ("schema", "validate", "reject", "assert", "compare", "count", "parse")

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

# D2: the choice is one of the three answers.
choice = sec("Choice").lower()
picked = [c for c in CHOICES if c in choice]
check("D2 the choice is one agent, many agents or no agent", len(picked) == 1,
      f"found {picked}; name exactly one of {list(CHOICES)}")

# D3: at least two alternatives, and none of them is the choice itself.
alts = bullets(sec("Alternatives"))
repeats = [a for a in alts if picked and a.lower().startswith(picked[0])]
check("D3 at least two alternatives, none the same as the choice", len(alts) >= 2 and not repeats,
      f"{len(alts)} alternatives, repeating the choice: {repeats}")

# D4: the reason uses the table, not only a preference.
reason = sec("Reason").lower()
named = [c for c in COLUMNS if c in reason]
check("D4 the reason names at least two of the table's columns", len(named) >= 2,
      f"named {named}; compare calls, tokens, latency, errors, testing or plain code")

# D5: the evidence is a log excerpt a reviewer can read: a fenced block with at least three lines.
fence = re.search(r"```[a-z]*\n(.*?)```", sec("Evidence"), flags=re.S)
lines = [l for l in fence.group(1).splitlines() if l.strip()] if fence else []
check("D5 the evidence holds a log excerpt of at least three lines", len(lines) >= 3,
      "paste three or more lines your chain printed, inside a code fence")

# D6: a check sits at a hand-off, and the checks say which one.
chk = sec("Checks").lower()
check("D6 the checks name a hand-off and a way to test it",
      ("hand-off" in chk or "handoff" in chk or "between" in chk) and any(w in chk for w in CHECK_WORDS),
      "say which hand-off is checked and whether you parse, validate a schema or count")

# D7: no secret in the file. A long run of letters and digits looks like a key.
leaked = re.findall(r"\b[A-Za-z0-9_\-]{32,}\b", text)
check("D7 no key value is written in the file", not leaked, f"{len(leaked)} key-shaped strings")

# 3. SUMMARY ###################################

print(f"\n{sum(results)} of {len(results)} checks pass. A reviewer still reads the reason.")
sys.exit(0 if all(results) else 1)
