#!/usr/bin/env bash
# check.sh
# Check a retrieval system's answers log against its held-out question set.
# Course kit, module 07
#
# Copy this folder into your repo, then, from this folder:
#   LLM_STUB=1 bash check.sh               # no model: the bundled example/ answers log
#   LLM_STUB=bad bash check.sh             # example_bad/, broken on purpose, to show FAIL
#   bash check.sh store.csv questions.csv answers.jsonl [target]   # your own files

set -euo pipefail
cd "$(dirname "$0")"
case "${LLM_STUB:-}" in
  1)   python3 check_retrieval.py example/store.csv example/questions.csv example/answers.jsonl ;;
  bad) python3 check_retrieval.py example_bad/store.csv example_bad/questions.csv example_bad/answers.jsonl ;;
  *)   python3 check_retrieval.py "$@" ;;
esac
