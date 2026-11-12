# check_decision.py
# Check that DECISION.md is complete, and that its parts agree with each other
# Course kit, module 7
#
# Topic: Retrieval, and choosing how your system finds the right passage
#
# The lab asks your team to decide how your retrieval system stores its documents
# and finds the passage that answers a question: which store, which settings, what
# you turned down, and how you know it works. This script reads that decision,
# DECISION.md, and checks that it is complete and that it agrees with itself: the
# store is one the lab names, the settings are numbers, the hit rate you wrote
# matches the one your answers log gives, and a person read the grounding rows.
# It cannot tell you whether the decision is wise. A reviewer reads the reasons.
#
# Run it:
#   python3 check_decision.py path/to/DECISION.md                       # check your decision
#   python3 check_decision.py DECISION.md answers.jsonl questions.csv   # also recompute the hit rate
#   DECISION_STUB=1 python3 check_decision.py                           # the saved example, which passes
#   DECISION_STUB=bad python3 check_decision.py                         # broken on purpose, to show FAIL
# Exits 1 if any check fails.
#
# Uses only the Python standard library.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import csv  # for the held-out question set
import json  # for the answers log
import os  # for the stub switch
import re  # for pulling lines and numbers out of the text
import sys  # for arguments and the exit code
from pathlib import Path  # for paths beside this script

## 0.2 Configuration #################################

HERE = Path(__file__).resolve().parent
STUB = os.environ.get("DECISION_STUB", "")  # "", "1" or "bad"
SECTIONS = ["store", "alternatives", "settings", "evidence", "grounding"]
STORES = ["text", "csv", "sqlite", "embedding"]
OPTIONS = ["table query", "tool call", "long-context", "long context", "keyword search",
           "embedding search", "fine-tuning", "fine tuning", "hybrid search"]
MIN_WORDS = 8  # a rejected option needs a few words on why it lost
MIN_ROWS = 3  # grounding rows
# Words that mean "the model" when someone types them into a name field.
NOT_A_PERSON = ("model", "ai", "llm", "assistant", "the tool", "system")

## 0.3 Find the Files #################################

ANSWERS = QUESTIONS = None
if STUB == "1":
    PATH = HERE / "example" / "DECISION.md"
    ANSWERS, QUESTIONS = HERE / "example" / "answers.jsonl", HERE / "example" / "questions.csv"
elif STUB == "bad":
    PATH = HERE / "example_bad" / "DECISION.md"
    ANSWERS, QUESTIONS = HERE / "example_bad" / "answers.jsonl", HERE / "example_bad" / "questions.csv"
elif len(sys.argv) > 1:
    PATH = Path(sys.argv[1])
    if len(sys.argv) > 3:
        ANSWERS, QUESTIONS = Path(sys.argv[2]), Path(sys.argv[3])
else:
    print("FAIL  usage: check_decision.py DECISION.md [answers.jsonl questions.csv]")
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
    m = re.search(rf"^{label}:[ \t]*(.+)$", body, re.MULTILINE | re.IGNORECASE)
    return m.group(1).strip() if m else ""


def number_in(value):
    m = re.search(r"-?\d+(?:\.\d+)?", value or "")
    return float(m.group(0)) if m else None


def whole_number(value):
    return int(value) if re.fullmatch(r"\d+", value or "") else None


def computed_hit_rate(answers_path, questions_path):
    """Hits over answerable questions, the same sum check_retrieval.py makes, or None."""
    try:
        with open(questions_path, newline="", encoding="utf-8") as f:
            questions = list(csv.DictReader(f))
        cited = {}
        with open(answers_path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    a = json.loads(line)
                    cited[a["question"]] = (a.get("cited_source") or "").strip()
        answerable = [q for q in questions if q["expected_source"].strip()]
        hits = sum(1 for q in answerable if cited.get(q["question"], "") == q["expected_source"].strip())
        return hits / len(answerable) if answerable else None
    except (OSError, KeyError, ValueError):
        return None


parts = sections_of(text)
print(f"Read {PATH}: sections {sorted(parts)}\n")
settings = parts.get("settings", "")
evidence = parts.get("evidence", "")


# 2. THE CHECKS #################################

results = []

def check(name, ok, detail=""):
    # One PASS or FAIL line per check; the detail only shows when it fails.
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"\n      {detail}" if detail and not ok else ""))

# D1: all five sections are there and none is empty.
missing = [s for s in SECTIONS if not parts.get(s, "").strip()]
check("D1 all five sections are present and filled in", not missing, f"missing or empty: {missing}")

# D2: the store is one of the four the lab names.
store_line = line_value(parts.get("store", ""), "Store")
store = store_line.lower().split(" ")[0].strip(".,;") if store_line else ""
check("D2 the store is text, csv, sqlite or embedding", store in STORES,
      f"write 'Store: one of {STORES}'; found '{store_line}'")

# D3: at least two rejected options, each a bullet that names one and says why it lost.
bullets = [l.strip()[2:].strip() for l in parts.get("alternatives", "").splitlines()
           if l.strip().startswith("- ")]
good = [b for b in bullets if any(o in b.lower() for o in OPTIONS) and len(b.split()) >= MIN_WORDS]
check("D3 at least two rejected options, each named with why it lost", len(good) >= 2,
      f"{len(good)} usable bullet(s) of {len(bullets)}; name one of {OPTIONS} and say why it lost")

# D4: k and chunk are whole numbers (chunk may be n/a when the store is not an embedding index).
k = whole_number(line_value(settings, "k"))
chunk_text = line_value(settings, "chunk").lower()
chunk_ok = whole_number(chunk_text) is not None or chunk_text == "n/a"
check("D4 Settings gives k and chunk as whole numbers (chunk may be n/a)",
      k is not None and chunk_ok, "write 'k: 3' and 'chunk: 200' (or 'chunk: n/a')")

# D5: the hit rate is between 0 and 1, it is stated at the k you set, and it matches your files.
rate = number_in(line_value(evidence, "Hit rate"))
at_k = whole_number(line_value(evidence, "At k"))
ok = rate is not None and 0 <= rate <= 1 and k is not None and at_k == k
detail = "write 'Hit rate: 0.80' (0 to 1) and 'At k:' equal to the k in Settings"
if ok and ANSWERS and QUESTIONS:
    real = computed_hit_rate(ANSWERS, QUESTIONS)
    ok = real is not None and abs(real - rate) < 0.005 + 1e-9
    shown = "nothing" if real is None else f"{real:.2f}"
    detail = f"your files give {shown}; the evidence says {rate}"
check("D5 Evidence gives a hit rate at the same k, and it matches your files", ok, detail)

# D6: at least three grounding rows, each read by a named person.
rows, bad_rows = [], []
for line in parts.get("grounding", "").splitlines():
    cells = [c.strip() for c in line.strip().lstrip("-").split("|")]
    if len(cells) != 3:
        continue
    supported = re.sub(r"(?i)^supported:\s*", "", cells[1]).lower()
    reader = re.sub(r"(?i)^read by:\s*", "", cells[2]).strip()
    reader = re.sub(r"(?i)^(the|a|an)\s+", "", reader) if reader.lower() != "the tool" else reader
    rows.append(cells)
    if not (cells[0] and supported in ("yes", "no") and reader and reader.lower() not in NOT_A_PERSON):
        bad_rows.append(cells[0] or line)
check("D6 at least three grounding rows, each read by a named person",
      len(rows) >= MIN_ROWS and not bad_rows,
      f"{len(rows)} row(s); each is 'question | supported: yes or no | read by: a name', "
      f"never {NOT_A_PERSON}; bad rows: {bad_rows}")


# 3. PRINT THE SUMMARY #################################

passed = sum(results)
print(f"\n{passed} of {len(results)} checks pass." +
      (" A reviewer still reads the reasons." if passed == len(results) else ""))
sys.exit(0 if all(results) else 1)
