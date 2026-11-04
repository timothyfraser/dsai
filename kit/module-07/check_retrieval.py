# check_retrieval.py
# The lab's checks: is the retrieval system trustworthy on questions it has not seen?
# Course kit, module 07
#
# Topic: Checking retrieval with a held-out question set and a hit rate
#
# Your system writes answers.jsonl, one line per question, with the fields
# question, answer and cited_source. This script reads it next to your held-out
# questions.csv (question, expected_source) and your store.csv (id, text), computes
# the hit rate, and prints one PASS or FAIL line per check.
#
# Run it from this folder:
#   python3 check_retrieval.py store.csv questions.csv answers.jsonl [target]
# No model handy? LLM_STUB=1 bash check.sh uses the bundled example/ files instead.
# The target is a number between 0 and 1; the default is 0.7. State yours before you run.
# Exits 1 if any check fails. Standard library only: nothing to install.

# 0. SETUP ###################################

import csv  # for the store and the question set
import json  # for the answers log
import sys  # for arguments and the exit code

## 0.1 Settings #################################

if len(sys.argv) < 4:
    print("FAIL  usage: check_retrieval.py store.csv questions.csv answers.jsonl [target]")
    sys.exit(1)
STORE, QUESTIONS, ANSWERS = sys.argv[1:4]
TARGET = float(sys.argv[4]) if len(sys.argv) > 4 else 0.7  # the pass mark for the hit rate
MIN_QUESTIONS = 10  # the lab asks for at least ten questions
MIN_UNANSWERABLE = 2  # and at least two the documents cannot answer
UNKNOWN = ("don't know", "do not know", "dont know")  # phrases that count as a refusal

results = []
def check(name, ok, detail=""):
    # One PASS or FAIL line per check; the detail only shows when it fails.
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))

def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

## 0.2 Load the three files #################################

try:
    store_ids = {r["id"] for r in read_csv(STORE)}
    questions = read_csv(QUESTIONS)
    answers = {}
    with open(ANSWERS, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                a = json.loads(line)
                answers[a["question"]] = a
except (OSError, KeyError, json.JSONDecodeError) as err:
    print(f"FAIL  could not read the input files: {err}")
    sys.exit(1)

# The held-out file marks an unanswerable question by leaving expected_source empty.
answerable = [q for q in questions if q["expected_source"].strip()]
unanswerable = [q for q in questions if not q["expected_source"].strip()]

def cites(q):
    return (answers.get(q["question"], {}).get("cited_source") or "").strip()

def refuses(q):
    # A refusal is an answer that says it does not know AND cites nothing.
    text = answers.get(q["question"], {}).get("answer", "").lower()
    return any(p in text for p in UNKNOWN) and not cites(q)

# 1. THE CHECKS ###################################

# C1: every question has an answer, and every answer cites a source or says "I don't know".
bad = [q["question"] for q in questions
       if q["question"] not in answers or not (cites(q) or refuses(q))]
check("C1 every answer cites a source or says it does not know", not bad, f"{bad}")

# C2: the held-out set is big enough, and has questions that cannot be answered.
check(f"C2 at least {MIN_QUESTIONS} questions, {MIN_UNANSWERABLE} unanswerable",
      len(questions) >= MIN_QUESTIONS and len(unanswerable) >= MIN_UNANSWERABLE,
      f"{len(questions)} questions, {len(unanswerable)} unanswerable")

# C3: the hit rate over the answerable questions: hits divided by questions.
hits = sum(1 for q in answerable if cites(q) == q["expected_source"].strip())
rate = hits / len(answerable) if answerable else 0.0
check(f"C3 hit rate {hits}/{len(answerable)} = {rate:.2f} reaches the target {TARGET:.2f}",
      rate >= TARGET)

# C4: for each unanswerable question the system refuses, with no citation.
wrong = [q["question"] for q in unanswerable if not refuses(q)]
check("C4 every unanswerable question gets \"I don't know\"", bool(unanswerable) and not wrong,
      f"{wrong}")

# C5: a citation must be an id that is in the store. This is the test for a made-up source.
invented = sorted({cites(q) for q in questions if cites(q) and cites(q) not in store_ids})
check("C5 every cited id is found in the store", not invented, f"not in store: {invented}")

# 2. RESULT ###################################

print(f"{sum(results)} of {len(results)} checks pass.")
sys.exit(0 if all(results) else 1)
