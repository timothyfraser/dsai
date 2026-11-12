# check_decision.py
# Check that DECISION.md is complete, and that its parts agree with each other
# Course kit, module 16
#
# Topic: Bounded jobs for a small coding model
#
# The lab asks your team to choose the next job to hand a small coding model, and
# to say why. This script reads that decision, DECISION.md, and checks that it is
# complete: the job is named, two jobs were turned down with a reason, the
# evidence comes from your three runs, local or cloud is stated, and the new
# job has a task contract with the same five fields as AGENTS.md. It cannot tell
# you whether the choice is wise. A reviewer reads the reason.
#
# Run it:
#   python3 check_decision.py path/to/DECISION.md   # check your decision
#   DECISION_STUB=1 python3 check_decision.py       # the saved example, which passes
#   DECISION_STUB=bad python3 check_decision.py     # broken on purpose, to show FAIL
# Exits 1 if any check fails.
#
# Uses only the Python standard library.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import os  # for the stub switch
import re  # for pulling lines and numbers out of the text
import sys  # for arguments and the exit code
from pathlib import Path  # for paths beside this script

## 0.2 Configuration #################################

HERE = Path(__file__).resolve().parent
STUB = os.environ.get("DECISION_STUB", "")  # "", "1" or "bad"
SECTIONS = ["next job", "rejected", "reason", "evidence", "local or cloud"]
CONTRACT = HERE / "AGENTS.md"  # the task contract whose field names we copy

## 0.3 Find the File #################################

if STUB == "1":
    PATH = HERE / "example" / "DECISION.md"
elif STUB == "bad":
    PATH = HERE / "example_bad" / "DECISION.md"
elif len(sys.argv) > 1:
    PATH = Path(sys.argv[1])
else:
    print("Usage: python3 check_decision.py path/to/DECISION.md  (or DECISION_STUB=1 for the example)")
    sys.exit(1)

if not PATH.exists():
    print(f"FAIL  no file at {PATH}: copy example/DECISION.md and fill it in")
    sys.exit(1)
text = PATH.read_text(encoding="utf-8")


# 1. SPLIT THE TEXT INTO SECTIONS #################################

def sections_of(md):
    """Return {lowercased heading: body} for every '## ' heading."""
    found, name = {}, None
    for line in md.splitlines():
        if line.startswith("## "):
            name = line[3:].strip().lower()
            found[name] = ""
        elif name:
            found[name] += line + "\n"
    return found


def line_value(body, label):
    """The text after 'Label:' at the start of a line, or ''."""
    m = re.search(rf"^{re.escape(label)}:[ \t]*(.+)$", body, re.MULTILINE | re.IGNORECASE)
    return m.group(1).strip() if m else ""


def task_fields(body):
    """Return {FIELD NAME: value} for every '- NAME: value' line, in order."""
    found = {}
    for line in body.splitlines():
        m = re.match(r"^\s*[-*]\s+([A-Z][A-Z ]+?):\s*(.*)$", line)
        if m:
            found[m.group(1).strip()] = m.group(2).strip()
    return found


parts = sections_of(text)
print(f"Read {PATH}: sections {sorted(parts)}\n")
evidence = parts.get("evidence", "")
where = parts.get("local or cloud", "")

# The five field names come from AGENTS.md, not from this script.
if CONTRACT.exists():
    contract_fields = task_fields(sections_of(CONTRACT.read_text(encoding="utf-8")).get("task", ""))
else:
    contract_fields = {}
FIELDS = list(contract_fields)


# 2. THE CHECKS #################################

results = []

# D1: all five sections are there and none is empty.
missing = [s for s in SECTIONS if not parts.get(s, "").strip()]
results.append(("D1", "all five sections are present and filled in", not missing,
                f"missing or empty: {missing}; the sections are {SECTIONS}"))

# D2: two jobs were turned down, each a bullet that names the job and why the contract cannot bound it yet.
bullets = [l.strip()[2:].strip() for l in parts.get("rejected", "").splitlines() if l.strip().startswith("- ")]
long_enough = [b for b in bullets if len(b.split()) >= 8]
results.append(("D2", "Rejected has two bullets, each a job and why the contract cannot bound it yet",
                len(bullets) >= 2 and len(long_enough) >= 2,
                f"found {len(bullets)} bullet(s), {len(long_enough)} with a job and a reason (8 words or more)"))

# D3: three run lines with a result and seconds, and one line for the run without the TASK block.
run_lines = {n: line_value(evidence, f"run {n}") for n in (1, 2, 3)}
run_ok = all(re.search(r"\b(PASS|FAIL)\b", v) and re.search(r"\d+(?:\.\d+)?\s*s\b", v) for v in run_lines.values())
bare = line_value(evidence, "without TASK block")
results.append(("D3", "Evidence has run 1 to run 3 with PASS or FAIL and seconds, and a 'without TASK block:' line",
                bool(run_ok and bare),
                "write 'run 1: PASS, 38 s' for each of three runs, and 'without TASK block: FAIL, 41 s'"))

# D4: local or cloud is stated, with one reason.
choice = line_value(where, "Choice").lower()
because = line_value(where, "Because")
results.append(("D4", "Local or cloud says 'Choice:' local or cloud, and one 'Because:' line",
                choice in ("local", "cloud") and bool(because),
                "write 'Choice: local' (or cloud) and 'Because: one sentence'"))

# D5: the file holds a TASK section with the five field names from AGENTS.md, and one file to edit.
mine = task_fields(parts.get("task", ""))
lacking = [f for f in FIELDS if not mine.get(f)]
edit = mine.get("FILE YOU MAY EDIT", "").strip("`").strip()
one_path = bool(edit) and not re.search(r"[\s,;]|\band\b", edit)
results.append(("D5", "a '## TASK' section has the five field names from AGENTS.md, and FILE YOU MAY EDIT is one path",
                len(FIELDS) == 5 and not lacking and one_path,
                f"AGENTS.md gives {len(FIELDS)} field(s) {FIELDS}; missing or empty here: {lacking}; "
                f"FILE YOU MAY EDIT must be one path, found '{edit}'"))


# 3. PRINT ONE LINE PER CHECK #################################

failed = 0
for cid, label, ok, why in results:
    print(f"{'PASS' if ok else 'FAIL'}  {cid} {label}")
    if not ok:
        failed += 1
        print("      " + why)

passed = len(results) - failed
print(f"\n{passed} of {len(results)} checks pass." +
      (" A reviewer still reads the reason." if failed == 0 else ""))
sys.exit(1 if failed else 0)
