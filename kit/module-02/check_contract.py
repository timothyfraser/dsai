# check_contract.py
# The lab's checks: does a team's app folder hold the contract, the rules and the docs?
# Course kit, module 02
#
# Topic: Checking a contract folder with a script
#
# This script reads your team's app folder and checks the parts of the lab a script can see:
# a rules file, a SPEC.md with its sections, a docs/ folder, a README that says how to run
# the app, a Mermaid block, and no key-shaped strings. Whether the app really starts, whether
# the diagram renders, whether the README follows the rules and who committed what are for
# a reviewer to read; this script says so at the end.
#
# Run it from this folder:
#   python3 check_contract.py path/to/your/app
# No app handy? CONTRACT_STUB=1 bash check.sh checks the bundled example/ folder instead.
# Prints one PASS or FAIL line per check and exits 1 if any check fails.
# Standard library only: nothing to install.

# 0. SETUP ###################################

import re  # for finding headings, run commands and key patterns
import sys  # for the exit code
from pathlib import Path  # for paths that work on every system

## 0.1 Settings #################################

FOLDER = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
SPEC_SECTIONS = ["goal", "who it is for", "contract", "owners"]  # headings SPEC.md must have
DOC_FILES = ["README.md", "SCHEMA.md", "WORKFLOW.md"]  # the least the docs/ folder holds
MIN_LINES = 4  # the lab asks for four to six contract lines
KEY_PATTERNS = [  # shapes that real keys take; a match anywhere in the folder fails
    r"sk-[A-Za-z0-9_-]{16,}",
    r"AIza[0-9A-Za-z_-]{20,}",
    r"(?i)(api[_-]?key|token|secret)\s*[=:]\s*['\"]?[A-Za-z0-9_-]{16,}",
]

results = []
def check(name, ok, detail=""):
    # One PASS or FAIL line per check; the detail only shows when it fails.
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))

def read(path):
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""

if not FOLDER.is_dir():
    print(f"FAIL  {FOLDER} is not a folder: pass your team's app folder")
    sys.exit(1)

# 1. THE CHECKS ###################################

## 1.1 Rules file #################################

rules = [p for p in FOLDER.rglob("*") if p.is_file() and
         (p.suffix == ".mdc" or p.name in ("CLAUDE.md", "AGENTS.md", ".cursorrules"))]
check("R1 a rules file is in the project", len(rules) > 0, "no .mdc, CLAUDE.md or AGENTS.md found")

## 1.2 SPEC.md #################################

spec = read(FOLDER / "SPEC.md")
check("R2 SPEC.md exists", spec != "", "no SPEC.md at the top of the folder")
headings = [h.strip().lower() for h in re.findall(r"^#+\s*(.+)$", spec, re.M)]
missing = [s for s in SPEC_SECTIONS if not any(s in h for h in headings)]
check("R3 SPEC.md has Goal, Who it is for, Contract and Owners sections", not missing,
      "missing: " + ", ".join(missing))
lines = re.findall(r"^\s*(?:[-*]|\d+\.)\s*\[[ xX]\]\s*.+$|^\s*(?:[-*]|\d+\.)\s+.+\b(?:yes|no)\b\s*$",
                   spec, re.M | re.I)
check(f"R4 SPEC.md has at least {MIN_LINES} contract lines, each with a yes or no mark",
      len(lines) >= MIN_LINES, f"found {len(lines)}")

## 1.3 docs/ folder #################################

docs = FOLDER / "docs"
absent = [f for f in DOC_FILES if not (docs / f).is_file()]
check("R5 docs/ holds " + ", ".join(DOC_FILES), not absent, "missing: " + ", ".join(absent))
mermaid = any("```mermaid" in read(p) for p in docs.glob("*.md")) if docs.is_dir() else False
check("R6 a docs/ file holds a Mermaid block (a person checks that it renders)", mermaid,
      "no ```mermaid fence in docs/")

## 1.4 README #################################

readme = read(FOLDER / "README.md")
runs = re.search(r"(?i)(Rscript|shiny::runApp|runApp|python3?\s+\S+|shiny run)", readme)
check("R7 README.md names the command that runs the app", bool(runs), "no run command found")
check("R8 README.md says which API key the app needs",
      bool(re.search(r"(?i)\b(api[_ -]?key|env(ironment)? variable|\.env)\b", readme)),
      "no mention of a key or .env")

## 1.5 No keys #################################

hits = []
for p in FOLDER.rglob("*"):
    if p.is_file() and ".git" not in p.parts:
        text = read(p)
        if any(re.search(k, text) for k in KEY_PATTERNS):
            hits.append(str(p.relative_to(FOLDER)))
check("R9 no key-shaped string anywhere in the folder", not hits, "in: " + ", ".join(hits))

# 2. SUMMARY ###################################

print(f"{sum(results)} of {len(results)} checks pass.")
print("A reviewer reads the rest: the app starts (lab check 1), real rows (2), a failure shows a "
      "message (3), the README follows two rules (6), the diagram renders (7), "
      "every teammate has a commit (8).")
sys.exit(0 if all(results) else 1)
