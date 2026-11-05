# check_decision.py
# The lab's decision check: does DECISION.md say what you chose, what you turned down, and why?
# Course kit, module 02
#
# Topic: Checking that a decision was written down
#
# This script reads your team's DECISION.md and checks that its parts are there: the
# development model you chose, two you rejected with a reason each, the split between what
# the agent did and what you checked, and the evidence. It cannot tell whether a reason is
# a good one. A reviewer reads that; this script only makes sure there is something to read.
#
# Run it from this folder:
#   python3 check_decision.py path/to/your/app/DECISION.md
# Prints one PASS or FAIL line per check and exits 1 if any check fails.
# Standard library only: nothing to install.

# 0. SETUP ###################################

import re  # for finding headings and list items
import sys  # for the exit code
from pathlib import Path  # for paths that work on every system

## 0.1 Settings #################################

FILE = Path(sys.argv[1] if len(sys.argv) > 1 else "DECISION.md")
SECTIONS = ["model chosen", "models rejected", "who does what", "evidence"]  # the headings
MODELS = ["spec-driven", "test-driven", "evaluation-driven", "closed-loop", "closed loop",
          "contract-driven", "plan-then-act", "vertical slice", "design-first",
          "docs as single source", "index-driven", "skill scaffold"]  # the page's table
MIN_WORDS = 8  # a reason shorter than this is a label, not a reason

results = []
def check(name, ok, detail=""):
    # One PASS or FAIL line per check; the detail only shows when it fails.
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))

def section(text, title):
    # The text under one ## heading, up to the next heading.
    m = re.search(rf"^#+\s*{title}\s*$(.*?)(?=^#+\s|\Z)", text, re.M | re.I | re.S)
    return m.group(1) if m else ""

def items(text):
    return re.findall(r"^\s*(?:[-*]|\d+\.)\s+(.+)$", text, re.M)

# 1. THE CHECKS ###################################

text = FILE.read_text(encoding="utf-8", errors="replace") if FILE.is_file() else ""
check("D1 DECISION.md exists", text != "", f"not found: {FILE}")
heads = [h.strip().lower() for h in re.findall(r"^#+\s*(.+)$", text, re.M)]
missing = [s for s in SECTIONS if s not in heads]
check("D2 DECISION.md has Model chosen, Models rejected, Who does what and Evidence",
      not missing, "missing: " + ", ".join(missing))

chosen = section(text, "model chosen").lower()
check("D3 the chosen model is one from the page's table", any(m in chosen for m in MODELS),
      "name it the way the table does, such as spec-driven development")

# We ask for two rejected models because one alternative is easy to knock down.
rejected = [i for i in items(section(text, "models rejected")) if len(i.split()) >= MIN_WORDS]
check(f"D4 at least two rejected models, each with a reason of {MIN_WORDS} words or more",
      len(rejected) >= 2, f"found {len(rejected)}")

split = section(text, "who does what").lower()
check("D5 Who does what names the agent's work and the checks a person makes",
      "agent" in split and bool(re.search(r"\b(we check|check|person|human)\b", split)),
      "say what the agent does and what you check yourself")

evidence = section(text, "evidence")
check("D6 Evidence points at a file, a command or a screenshot",
      bool(re.search(r"`[^`]+`|\.\w{2,4}\b|screenshot", evidence, re.I)), "nothing to look at")

# 2. SUMMARY ###################################

print(f"{sum(results)} of {len(results)} decision checks pass.")
print("A reviewer reads whether the reasons hold: that the rejected models lose for this job, "
      "not in general (lab check 7).")
sys.exit(0 if all(results) else 1)
