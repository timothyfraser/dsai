# check_decision.py
# Check that DECISION.md is complete, and that its verdict follows from its numbers
# Course kit, module 17
#
# Topic: Visual Language Models
#
# The lab asks you to decide when a model's reading may draft a row and when a
# person must look. This script reads that decision, DECISION.md, and checks that
# it is complete and that it agrees with itself. It cannot tell you whether the
# decision is wise. It can tell you that you wrote one: a rule with a threshold,
# alternatives, a reason that cites your agreement column, and a place for
# local or cloud. A person reads the reason.
#
# Run it from the top of the course repo:
#   python check_decision.py DECISION.md             # check your decision
#   python check_decision.py DECISION.md five.csv    # also read your agreement column
#   DECISION_STUB=1 python check_decision.py         # check the sample decision, no files of yours
#   DECISION_STUB=bad python check_decision.py       # check a sample broken on purpose; must fail
# Exits 1 if any check fails.
#
# Uses only the Python standard library.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import csv  # for reading your agreement column
import json  # for reading the schema, to see every field is placed
import os  # for paths and the stub switch
import re  # for pulling the numbers out of the text
import sys  # for arguments and the exit code

## 0.2 Configuration #################################

HERE = os.path.dirname(os.path.abspath(__file__))
STUB = os.environ.get("DECISION_STUB", "")  # "", "1" or "bad"
MIN_PHOTOS = 5  # the lab asks for five photos; fewer cannot support any threshold
SECTIONS = ["The job", "The rule", "Alternatives", "The reason", "Local or cloud"]
SCHEMA_PATH = os.environ.get("RECORD_SCHEMA", os.path.join(HERE, "record_schema.json"))

## 0.3 Find the Text #################################

if STUB:
    with open(os.path.join(HERE, "DECISION.example.md"), encoding="utf-8") as f:
        text = f.read()
    if STUB == "bad":
        # Break it on purpose: a 3 of 5 agreement rate cannot reach an 80% threshold,
        # yet the verdict still says "draft". A good check must notice.
        text = text.replace("Agreement: 4 of 5", "Agreement: 3 of 5")
    csv_path = None
else:
    path = sys.argv[1] if len(sys.argv) > 1 else "DECISION.md"
    if not os.path.exists(path):
        sys.exit(f"FAIL  {path} is not here. Run this from the folder that holds your DECISION.md.")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    csv_path = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("AGREEMENT_CSV")


# 1. SPLIT THE TEXT INTO SECTIONS #################################

def sections_of(md):
    """Return {heading: body} for every '## ' heading."""
    found, name = {}, None
    for line in md.splitlines():
        if line.startswith("## "):
            name = line[3:].strip()
            found[name] = ""
        elif name:
            found[name] += line + "\n"
    return found


def line_value(body, label):
    """The text after 'Label:' on its own line, or None."""
    m = re.search(rf"^{label}:[ \t]*(.+)$", body, re.MULTILINE | re.IGNORECASE)
    return m.group(1).strip() if m else None


def names_in(value):
    return [n.strip() for n in (value or "").split(",") if n.strip() and n.strip().lower() != "none"]


parts = sections_of(text)
rule = parts.get("The rule", "")
reason = parts.get("The reason", "")


# 2. THE CHECKS #################################

results = []

# D1: all five sections are there and none is empty.
missing = [s for s in SECTIONS if not parts.get(s, "").strip()]
results.append(("D1", "all five sections are present and not empty", not missing,
                f"missing or empty: {missing}"))

# D2: the rule has a threshold, a number between 50 and 100 percent.
threshold = line_value(rule, "Threshold")
t = re.search(r"(\d+(?:\.\d+)?)\s*%", threshold or "")
t_value = float(t.group(1)) if t else None
results.append(("D2", "the rule states a threshold between 50% and 100%",
                t_value is not None and 50 <= t_value <= 100,
                "write a line 'Threshold: 80%' in the section The rule"))

# D3: every field of the schema is placed, in Draft or in Person decides.
drafted = names_in(line_value(rule, "Draft"))
decided = names_in(line_value(rule, "Person decides"))
try:
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        field_names = [x["name"] for x in json.load(f)["fields"]]
except (OSError, ValueError, KeyError) as err:
    field_names = []
    schema_error = f"could not read the schema {SCHEMA_PATH}: {err}"
else:
    schema_error = ""
unplaced = [n for n in field_names if n not in drafted + decided]
both = [n for n in drafted if n in decided]
results.append(("D3", "every schema field is placed once: drafted by the model or decided by a person",
                bool(field_names) and not unplaced and not both and bool(decided),
                schema_error or f"not placed: {unplaced}; placed twice: {both}; "
                                f"'Person decides:' must name at least one field"))

# D4: at least two alternatives, one bullet each.
bullets = [l for l in parts.get("Alternatives", "").splitlines() if l.strip().startswith("- ")]
results.append(("D4", "at least two alternatives are named", len(bullets) >= 2,
                f"found {len(bullets)} bullet(s) in Alternatives"))

# D5: the reason cites the agreement column as 'Agreement: k of n', with n large enough.
cited = re.search(r"^Agreement:\s*(\d+)\s+of\s+(\d+)", reason, re.MULTILINE | re.IGNORECASE)
k, n = (int(cited.group(1)), int(cited.group(2))) if cited else (None, None)
results.append(("D5", f"the reason cites the agreement column on at least {MIN_PHOTOS} photos",
                cited is not None and n >= MIN_PHOTOS and k <= n,
                "write a line 'Agreement: 4 of 5' in the section The reason"))

# D6: if you gave your agreement CSV, the numbers you cite are the numbers in it.
if csv_path:
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    col = next((c for c in (rows[0].keys() if rows else []) if "agree" in c.lower()), None)
    yes = sum(1 for r in rows if col and r[col].strip().lower() in ("yes", "y", "true", "1"))
    results.append(("D6", "the agreement you cite matches your CSV",
                    col is not None and cited is not None and (k, n) == (yes, len(rows)),
                    f"the CSV has {yes} of {len(rows)} (column {col}); the reason says {k} of {n}"))

# D7: the verdict follows from the numbers. At or above the threshold: draft. Below it: person looks.
verdict = (line_value(reason, "Verdict") or "").lower()
if cited and t_value is not None and n:
    expected = "draft" if 100 * k / n >= t_value else "person looks"
else:
    expected = None
results.append(("D7", "the verdict follows from the agreement and the threshold",
                expected is not None and verdict == expected,
                f"agreement {k} of {n} against threshold {t_value}% means 'Verdict: {expected}', "
                f"but the file says '{verdict}'"))

# D8: local or cloud is chosen, with a reason about the photos or the time.
choice = parts.get("Local or cloud", "")
chose = re.match(r"\s*(local|cloud)\b", choice, re.IGNORECASE) is not None
why = re.search(r"\b(privacy|people|faces|private|cost|seconds|minutes|key|provider)\b", choice, re.IGNORECASE)
results.append(("D8", "local or cloud is chosen first, with a reason", chose and why is not None,
                "start the section with the word Local or Cloud, then say why"))


# 3. PRINT ONE LINE PER CHECK #################################

failed = 0
for cid, label, ok, detail in results:
    print(f"{'PASS' if ok else 'FAIL'}  {cid} {label}")
    if not ok:
        failed += 1
        print("      " + detail)

print(f"\n{'Decision file complete.' if failed == 0 else str(failed) + ' decision check(s) failed.'}")
sys.exit(1 if failed else 0)
