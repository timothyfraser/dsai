# check_decision.py
# Read a reader's DECISION.md and check that the fence decision is complete.
# Course kit, module 15
#
# Topic: Sizing the fence around an autonomous agent, decided on purpose
#
# An agent that stops at its bounds is half the work. The other half is the
# decision behind the bounds: for which stakeholder, which numbers, which two
# alternatives were turned down, what the numbers trade against, what the agent
# may do alone, and what a real run record says about whether the fence held.
# This script checks that every part is written down and that the parts agree
# with each other (the worst case in the reason is turns times seconds; the
# record ran under the turns you chose). It cannot check that the reasoning is
# good: a reviewer reads the file for that. It calls no server and no model.
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
import re  # for finding the sections and the numbers inside them
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

SECTIONS = ["Stakeholder", "Bounds", "Unattended", "Alternatives", "Reason", "Evidence"]
# The four bounds the module sizes, as the word that starts each bullet.
BOUNDS = [("turns", "Turns"), ("searches", "Web searches"), ("reads", "Skill reads"), ("seconds", "Seconds per model call")]
SERVICE_TURN_CAP = 10  # the service refuses a request for more turns than this
# The four columns of the trade-off table; a reason names at least two.
COLUMNS = {
    "completeness": ("completeness", "complete", "coverage"),
    "cost": ("cost", "spend", "money", "price"),
    "time": ("time to answer", "worst case", "wait", "late"),
    "blast radius": ("blast radius", "harm", "wrong brief", "outside text"),
}

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
def number_after(label, s):
    """The whole number written after a label such as 'Turns:' or 'Turns', or None."""
    m = re.search(re.escape(label) + r"\s*:?\s*(\d+)\b", s, flags=re.I)
    return int(m.group(1)) if m else None
print(f"Read {PATH}: sections {sorted(body)}\n")

# 2. THE CHECKS ###################################

# F1: every section is there and has words in it.
empty = [s for s in SECTIONS if len(sec(s).split()) < 4]
check("F1 all six sections are present and filled in", not empty, f"missing or too short: {empty}")

# F2: the four bounds are whole numbers, and the turns can actually be asked for.
chosen = {key: number_after(label, sec("Bounds")) for key, label in BOUNDS}
missing = [key for key, v in chosen.items() if v is None or v < 1]
over = chosen["turns"] is not None and chosen["turns"] > SERVICE_TURN_CAP
check("F2 the four bounds are numbers, and turns are at most the service cap of 10", not missing and not over,
      f"missing or not a number: {missing}; turns above {SERVICE_TURN_CAP}: {over}")

# F3: at least two alternatives, each with its own four numbers, none the same as the choice.
alts = bullets(sec("Alternatives"))
def four_numbers(line):
    """Turns, searches, reads and seconds in a line such as 'Turns 10, searches 3, reads 8, 120 seconds'."""
    t, se, r = (number_after(w, line) for w in ("Turns", "searches", "reads"))
    m = re.search(r"(\d+)\s*seconds", line, flags=re.I)
    return (t, se, r, int(m.group(1)) if m else None)
mine = tuple(chosen[k] for k in ("turns", "searches", "reads", "seconds"))
alt_sets = [four_numbers(a) for a in alts]
complete = [a for a in alt_sets if None not in a]
distinct = [a for a in complete if a != mine]
check("F3 two alternatives, each with four numbers that differ from the choice",
      len(complete) >= 2 and len(set(distinct)) >= 2,
      f"{len(alts)} alternatives, {len(complete)} with four numbers, {len(set(distinct))} distinct from the choice")

# F4: the reason names at least two columns of the table and shows the worst case in seconds.
reason = sec("Reason").lower()
named = [c for c, words in COLUMNS.items() if any(w in reason for w in words)]
worst = chosen["turns"] * chosen["seconds"] if chosen["turns"] and chosen["seconds"] else None
shown = worst is not None and re.search(rf"\b{worst}\b", reason) is not None
check("F4 the reason names two table columns and gives the worst case in seconds (turns x seconds)",
      len(named) >= 2 and shown, f"columns named {named}; worst case {worst} written: {shown}")

# F5: what the agent may do alone, what needs a person, and who holds the stop switch.
un = sec("Unattended")
alone = next((l for l in bullets(un) if l.lower().startswith("alone")), "")
person = next((l for l in bullets(un) if l.lower().startswith("needs a person")), "")
stop = any(w in un.lower() for w in ("stop switch", "/hooks/control", "stop"))
check("F5 one line for what runs alone, one for what needs a person, and the stop switch named",
      len(alone.split()) >= 5 and len(person.split()) >= 5 and stop,
      f"alone line {len(alone.split())} words, person line {len(person.split())} words, stop switch named {stop}")

# F6: the evidence is a run record that ran under the chosen turns and stayed inside them.
ev = sec("Evidence")
status = re.search(r"status\s*:\s*(ok|paused_for_human|error)\b", ev, flags=re.I)
used, cap = number_after("turns_used", ev), number_after("turn_cap", ev)
ran_under = used is not None and cap is not None and cap == chosen["turns"] and used <= cap
check("F6 the evidence is a run record: status, turns_used, and a turn_cap equal to your turns",
      bool(status) and ran_under, f"status {bool(status)}, turns_used {used}, turn_cap {cap}, chosen turns {chosen['turns']}")

# F7: the reader says whether the fence held, and why.
held = re.search(r"fence held\s*:\s*(yes|no)\b(.{15,})", ev, flags=re.I | re.S)
check("F7 the evidence says 'Fence held: yes' or 'no' and gives a reason", bool(held),
      "write the line 'Fence held: yes' or 'no' followed by the reason")

# F8: no secret in the file. A long run of letters and digits looks like a key.
leaked = re.findall(r"\b[A-Za-z0-9_\-]{32,}\b", text)
check("F8 no key value is written in the file", not leaked, f"{len(leaked)} key-shaped strings")

# 3. SUMMARY ###################################

print(f"\n{sum(results)} of {len(results)} checks pass. A reviewer still reads the reason.")
sys.exit(0 if all(results) else 1)
