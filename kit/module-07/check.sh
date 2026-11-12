#!/usr/bin/env bash
# check.sh
# Check a retrieval system's answers log against its held-out question set.
# Course kit, module 07
#
# Copy this folder into your repo, then, from this folder:
#   LLM_STUB=1 bash check.sh               # no model: the bundled example/ answers log
#   LLM_STUB=bad bash check.sh             # example_bad/, broken on purpose, to show FAIL
#   bash check.sh store.csv questions.csv answers.jsonl [target]   # your own files
# Your own run also reads DECISION.md in this folder (or DECISION_FILE=path/to/DECISION.md).

set -euo pipefail
cd "$(dirname "$0")"
# Each mode runs the retrieval checks (C1 to C5), then the decision checks (D1 to D6).
# Both run even if the first fails, so one run shows every problem.
rc=0
case "${LLM_STUB:-}" in
  1)   python3 check_retrieval.py example/store.csv example/questions.csv example/answers.jsonl || rc=1
       echo
       python3 check_decision.py example/DECISION.md example/answers.jsonl example/questions.csv || rc=1 ;;
  bad) python3 check_retrieval.py example_bad/store.csv example_bad/questions.csv example_bad/answers.jsonl || rc=1
       echo
       python3 check_decision.py example_bad/DECISION.md example_bad/answers.jsonl example_bad/questions.csv || rc=1 ;;
  *)   python3 check_retrieval.py "$@" || rc=1
       echo
       python3 check_decision.py "${DECISION_FILE:-DECISION.md}" "${3:-answers.jsonl}" "${2:-questions.csv}" || rc=1 ;;
esac
exit $rc
