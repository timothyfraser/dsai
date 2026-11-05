# check_decision.py
# Read a team's DECISION.md and check that the prompt or model choice is complete.
# Course kit, module 3
#
# Topic: Choosing a prompt or a model, and saying what the eval cannot tell you
#
# A reporter that runs and an eval that prints a number are half the lab. The other half is the
# decision: which prompt and which model the team ships, against which alternatives, for what
# reason, on what numbers from your own eval, and what the eval cannot see. This script checks
# that every part is written down and that the numbers you cite are really in your eval files.
# It cannot check that the reasoning is good: a reviewer reads the file for that.
# It calls no model and no server, so it runs anywhere.
#
# No python packages to install: it uses only the standard library.
#
# Run it from this folder:
#   python3 check_decision.py example/DECISION.md       # the saved example, which passes
#   python3 check_decision.py example_bad/DECISION.md   # broken on purpose, to show FAIL
#   python3 check_decision.py path/to/your/DECISION.md  # your team's own file
# The eval files are read from the folder that holds DECISION.md (eval/agreement.csv and
# eval/comparison.txt). Exits 1 if any check fails.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import re  # for finding the sections and the numbers inside them
import sys  # for the file argument and the exit code
from pathlib import Path  # for reading the files

## 0.2 Configuration #################################

PATH = Path(sys.argv[1] if len(sys.argv) > 1 else "DECISION.md")
FOLDER = PATH.resolve().parent

# The six sections the lab asks for, by their headings.
SECTIONS = ["Shipped", "Alternatives", "Reason", "Evidence", "Blind spots", "Key"]
# The trade-offs the module's table compares. A reason names at least two.
TRADE_OFFS = ("privacy", "cost", "latency", "quality", "rate limit", "who can read", "leave the machine", "leaves the machine")
# Words that mean "nobody in particular" when written as a key holder.
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
body = {parts[i].strip().lower(): parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}
def sec(name):
    return body.get(name.lower(), "")
def bullets(s):
    return [l.strip()[1:].strip() for l in s.splitlines() if l.strip().startswith(("-", "*"))]
def numbers(s):
    return set(re.findall(r"\d+\.\d+|\d+", s))
print(f"Read {PATH}: sections {sorted(body)}\n")

# The numbers your own eval wrote, to compare with the numbers you cite.
eval_text = ""
for name in ("agreement.csv", "comparison.txt"):
    p = FOLDER / "eval" / name
    if p.exists():
        eval_text += p.read_text(encoding="utf-8") + "\n"
eval_numbers = numbers(eval_text)

# 2. THE CHECKS ###################################

# D1: every section is there and has words in it.
empty = [s for s in SECTIONS if len(sec(s).split()) < (3 if s == "Shipped" else 4)]
check("D1 all six sections are present and filled in", not empty, f"missing or empty: {empty}")

# D2: one choice, and at least two alternatives that are not the same choice.
shipped = sec("Shipped").splitlines()[0].strip().lower() if sec("Shipped") else ""
alts = bullets(sec("Alternatives"))
same = [a for a in alts if shipped and a.lower().strip() == shipped]
check("D2 one prompt and model shipped, and at least two alternatives considered",
      bool(shipped) and len(alts) >= 2 and not same,
      f"shipped '{shipped}', {len(alts)} alternatives, repeats the choice: {same}")

# D3: the reason names at least two trade-offs, and says where the data goes (local or cloud).
reason = sec("Reason").lower()
named = [t for t in TRADE_OFFS if t in reason]
where = any(w in reason for w in ("local", "cloud", "commercial", "on our machine", "leave"))
check("D3 the reason names two trade-offs and says where the data goes",
      len(named) >= 2 and where, f"trade-offs named: {named}; says where data goes: {where}")

# D4: the reason or evidence cites a number, and that number is in your own eval files.
cited = numbers(sec("Reason") + " " + sec("Evidence"))
shared = sorted(cited & eval_numbers - {"0", "1", "10"})
check("D4 a number you cite is in eval/agreement.csv or eval/comparison.txt",
      bool(shared), "cite a rate or the p-value from your eval, and keep eval/ next to this file")

# D5: the blind spots section says what the eval does not measure.
blind = sec("Blind spots").lower()
check("D5 the blind spots name something the eval cannot see",
      len(blind.split()) >= 12 and any(w in blind for w in ("cannot", "does not", "do not", "not measure", "only")),
      "say what your eval does not measure, in a full sentence")

# D6: a named person holds any key, or the file says no key is used.
key = sec("Key")
line = next((l for l in key.splitlines() if "holder" in l.lower() or "holds" in l.lower()), "")
holder = line.split(":", 1)[1].strip().lower() if ":" in line else ""
no_key = "no key" in key.lower()
check("D6 a named person holds the key, or no key is used",
      no_key or (bool(holder) and not any(holder.startswith(n) for n in NOBODY)),
      f"holder line is '{line.strip()}'")

# D7: no secret in the file. A long run of letters and digits looks like a key.
leaked = re.findall(r"\b[A-Za-z0-9_\-]{32,}\b", text)
check("D7 no key value is written in the file", not leaked, f"{len(leaked)} key-shaped strings")

# 3. SUMMARY ###################################

print(f"\n{sum(results)} of {len(results)} checks pass. A reviewer still reads the reason.")
sys.exit(0 if all(results) else 1)
