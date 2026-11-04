# check_report.py
# The lab's checks: does a team's reporter output folder hold up?
# Course kit, module 03
#
# Topic: Checking a reporter and its eval with a script
#
# This script reads the folder your reporter and eval scripts wrote and checks the parts
# of the lab a script can verify. The rest (a live API call, git history, the written
# log entry) a reviewer checks by hand.
#
# Run it from this folder:
#   python3 check_report.py path/to/your/folder
# No model handy? REPORT_STUB=1 bash check.sh checks the bundled example/ folder instead.
# Prints one PASS or FAIL line per check and exits 1 if any check fails.
# Standard library only: nothing to install.

# 0. SETUP ###################################

import csv  # for reading eval/agreement.csv
import re  # for finding field labels, p-values and key patterns
import sys  # for the exit code
import zipfile  # for telling a real .docx from an empty file
from collections import Counter  # for the most common answer
from pathlib import Path  # for paths that work on every system

## 0.1 Settings #################################

FOLDER = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
MIN_RUNS = 10  # the lab says N is at least 10
TOLERANCE = 0.01  # how far the agreement rate may differ from our own count
REPORT_FORMATS = [".txt", ".md", ".html", ".docx"]  # the four formats from Step 4
KEY_PATTERNS = [  # shapes that real keys take; a match anywhere in the folder fails C8
    r"sk-[A-Za-z0-9_-]{16,}",
    r"AIza[0-9A-Za-z_-]{20,}",
    r"(?i)(api[_-]?key|token|secret)\s*[=:]\s*['\"]?[A-Za-z0-9_-]{16,}",
]

results = []
def check(name, ok, detail=""):
    # One PASS or FAIL line per check; the detail only shows when it fails.
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))

if not FOLDER.is_dir():
    print(f"FAIL  {FOLDER} is not a folder: pass the folder your reporter wrote")
    sys.exit(1)

## 0.2 Read the runs #################################

run_files = sorted((FOLDER / "runs").glob("*.txt")) if (FOLDER / "runs").is_dir() else []
runs = [p.read_text(encoding="utf-8") for p in run_files]

def field_values(text):
    # A field is a line written "Label: value". We never type the label list twice:
    # the labels come from the first column of agreement.csv.
    return {m.group(1).strip(): m.group(2).strip()
            for m in re.finditer(r"^([^:\n]+):[ \t]*(.*)$", text, re.M)}

agreement = []
agreement_path = FOLDER / "eval" / "agreement.csv"
if agreement_path.exists():
    with open(agreement_path, newline="", encoding="utf-8") as f:
        agreement = list(csv.DictReader(f))
labels = [row["field"] for row in agreement if "field" in row]

# 1. THE CHECKS ###################################

# C3: one reply per file in runs/, and at least MIN_RUNS of them.
check(f"C3 runs/ holds at least {MIN_RUNS} saved runs", len(runs) >= MIN_RUNS,
      f"found {len(runs)}")

# C2: every run carries every field label that the eval reports on.
lacking = []
for p, text in zip(run_files, runs):
    have = field_values(text)
    lacking += [f"{p.name}:{lab}" for lab in labels if lab not in have]
check("C2 every run uses the same field labels", bool(labels) and not lacking,
      "no labels (is eval/agreement.csv missing?)" if not labels else f"missing {lacking}")

# C4: agreement.csv exists and each rate is the share of runs that match the most
# common answer. We recompute it from the runs instead of trusting the file.
problems = []
for row in agreement:
    vals = [field_values(t).get(row.get("field", "")) for t in runs]
    vals = [v for v in vals if v is not None]
    if not vals:
        problems.append(f"{row.get('field')}: no values in runs")
        continue
    ours = Counter(vals).most_common(1)[0][1] / len(vals)
    try:
        theirs = float(row["rate"])
    except (KeyError, ValueError):
        problems.append(f"{row.get('field')}: no numeric rate")
        continue
    if abs(ours - theirs) > TOLERANCE:
        problems.append(f"{row['field']}: file says {theirs}, runs give {ours:.2f}")
check("C4 eval/agreement.csv exists and its rates match the runs",
      bool(agreement) and not problems,
      "eval/agreement.csv not found" if not agreement else "; ".join(problems))

# C6: comparison.txt names a test and gives a p-value between 0 and 1.
comp_path = FOLDER / "eval" / "comparison.txt"
comp = comp_path.read_text(encoding="utf-8") if comp_path.exists() else ""
test_named = re.search(r"(?i)t-test|anova|welch|mann-whitney|chi-square", comp)
p_match = re.search(r"(?i)\bp(?:[- ]?value)?\s*[=<:]\s*([0-9]*\.?[0-9]+(?:e-?[0-9]+)?)", comp)
p_ok = bool(p_match) and 0 <= float(p_match.group(1)) <= 1
check("C6 eval/comparison.txt names a test and a p-value", bool(test_named) and p_ok,
      "file missing" if not comp else f"test named: {bool(test_named)}, p-value found: {p_ok}")

# C7: the report exists in at least one of the four formats, and is not empty.
def report_ok(path):
    if path.suffix == ".docx":
        return zipfile.is_zipfile(path)
    return path.stat().st_size > 0
found = [p.name for ext in REPORT_FORMATS for p in FOLDER.glob("report" + ext) if report_ok(p)]
check("C7 a report file exists (report.txt, .md, .html or .docx)", bool(found))

# C8 (part): no key pattern anywhere in the folder. Git history is the reviewer's job.
hits = []
for p in FOLDER.rglob("*"):
    if p.is_file() and p.suffix != ".docx":
        text = p.read_text(encoding="utf-8", errors="ignore")
        if any(re.search(pat, text) for pat in KEY_PATTERNS):
            hits.append(str(p.relative_to(FOLDER)))
check("C8 no API key pattern in the folder", not hits, f"found in {hits}")

# 2. RESULT ###################################

print(f"{sum(results)} of {len(results)} scripted checks pass. "
      "C1, C5, C9 and the git-history part of C8 are for a reviewer.")
sys.exit(0 if all(results) else 1)
