# check_decision.py
# The lab's decision check: read DECISION.md and test that it is complete and consistent.
# Course kit, module 18
#
# Topic: Deciding which fields a person confirms
#
# A person writes DECISION.md. This script does not judge whether the decision is wise.
# It tests that the decision is whole: every field of the form is sorted, the costs are
# stated, two alternatives are rejected with reasons, and the reason cites a word error
# rate the team measured. A reviewer then reads the file and asks whether the reasons hold.
# It calls no model, so it runs anywhere.

# Run from the top of the course repo:
#   DECISION_STUB=1 python3 kit/module-18/check_decision.py      # the saved good example
#   DECISION_STUB=bad python3 kit/module-18/check_decision.py    # the saved bad example: must fail
#   python3 kit/module-18/check_decision.py DECISION.md          # your team's file
# Set FORM_FIELDS="a,b,c" if your form is not the work order.
# Exits 1 if any check fails.

# 0. SETUP ###################################

import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUB = os.getenv("DECISION_STUB", "")
if STUB == "1":
    PATH = HERE / "example" / "DECISION.md"
elif STUB == "bad":
    PATH = HERE / "example" / "DECISION_bad.md"
else:
    PATH = Path(sys.argv[1] if len(sys.argv) > 1 else "DECISION.md")

# The fields of the kit's work order, plus the one field only a person may write.
FORM_FIELDS = [f.strip() for f in os.getenv(
    "FORM_FIELDS", "asset,location,problem,priority,safety_hazard,action_requested,confirmed_by").split(",")]
BUCKETS = ("model-drafts", "person-confirms", "never-automated")
COSTS = ("low", "medium", "high")

results = []
def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))

if not PATH.exists():
    print(f"FAIL  {PATH} not found")
    sys.exit(1)
text = PATH.read_text(encoding="utf-8")

# 1. SPLIT THE FILE INTO ITS SECTIONS ###################################

sections = {}
current = None
for line in text.splitlines():
    if line.startswith("## "):
        current = line[3:].strip().lower()
        sections[current] = []
    elif current:
        sections[current].append(line)
body = {k: "\n".join(v).strip() for k, v in sections.items()}
print(f"Read {PATH.name}: sections {sorted(body)}")

# 2. THE CHECKS ###################################

# D1: all four sections are there and not empty.
needed = ["field sorting", "alternatives rejected", "reason", "evidence"]
missing = [s for s in needed if not body.get(s)]
check("D1 the four sections are present and not empty", not missing, f"missing: {missing}")

# D2: every field of the form is sorted into a bucket, with a cost and a reason.
rows = {}
for line in body.get("field sorting", "").splitlines():
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cells) >= 4 and cells[0] in FORM_FIELDS:
        rows[cells[0]] = cells[1:4]
unsorted = [f for f in FORM_FIELDS if f not in rows]
badrow = [f for f, (b, c, why) in rows.items() if b not in BUCKETS or c not in COSTS or len(why.split()) < 6]
check("D2 every field is sorted, with a bucket, a cost and a reason of six words or more",
      not unsorted and not badrow, f"not sorted: {unsorted}; incomplete: {badrow}")

# D3: the rule is followed. A high-cost field is never left to the model alone.
risky = [f for f, (b, c, _) in rows.items() if c == "high" and b == "model-drafts"]
check("D3 no high-cost field is left as model-drafts", not risky, f"model-drafts but high cost: {risky}")

# D4: the sort is a decision. At least one field in person-confirms, and not all of them.
used = {b for b, _, _ in rows.values()}
check("D4 the sort uses person-confirms and at least one other bucket",
      "person-confirms" in used and len(used) >= 2, f"buckets used: {sorted(used)}")

# D5: two alternatives, each with the word "rejected" and a reason after it.
alts = [l for l in body.get("alternatives rejected", "").splitlines() if l.strip().startswith(("-", "*"))]
good_alts = [l for l in alts if re.search(r"rejected:?\s+\S+(\s+\S+){4,}", l, re.I)]
check("D5 two alternatives are rejected, each with a reason", len(good_alts) >= 2,
      f"{len(good_alts)} alternatives with a reason")

# D6: the reason cites a measured word error rate: the term, and at least one number with percent.
reason = body.get("reason", "")
cites_wer = "word error rate" in reason.lower() and bool(re.search(r"\d+(\.\d+)?\s*(percent|%)", reason))
check("D6 the reason cites a word error rate as a number", cites_wer,
      "name the word error rate and give the number, such as 21 percent")

# D7: the reason names the transcriber chosen.
named = bool(re.search(r"(tiny|base|small)\.en|cloud", reason, re.I))
check("D7 the reason names the transcriber chosen", named, "say tiny.en, base.en, small.en or cloud")

# D8: the evidence points at files: at least two, by name.
files = re.findall(r"[\w./-]+\.(?:csv|wav|txt|md|sh|py|R)\b", body.get("evidence", ""))
check("D8 the evidence names at least two files", len(set(files)) >= 2, f"files named: {sorted(set(files))}")

# 3. SUMMARY ###################################

print(f"{sum(results)} of {len(results)} checks pass.")
sys.exit(0 if all(results) else 1)
