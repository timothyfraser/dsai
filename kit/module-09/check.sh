#!/usr/bin/env bash
# check.sh
# Check a team's pipeline folder: the lab's checks C1 to C8.
# Course kit, module 09
#
# Usage, from this folder:
#   PIPE_DIR=../../my-pipeline API_URL=https://your-server/your-api bash check.sh
#   PIPE_STUB=1 bash check.sh     # no server handy: an example folder and a stub stand in,
#                                 # then each planted flaw is tried and must fail

set -euo pipefail
cd "$(dirname "$0")"

if [ -z "${PIPE_STUB:-}" ]; then
  python3 -B check_pipeline.py
  exit $?
fi

# Stub mode: the good example must pass, and every planted flaw must fail.
python3 -B check_pipeline.py
bad=0
for flaw in duplicates stale_rows metric_range uncited_answer no_model api_down; do
  echo
  echo "--- planted flaw: $flaw (this run must fail) ---"
  if PIPE_FLAW=$flaw python3 -B check_pipeline.py; then
    echo "UNEXPECTED: the flaw '$flaw' was not caught"
    bad=1
  fi
done
echo
if [ "$bad" -eq 0 ]; then echo "every planted flaw was caught"; fi
exit $bad
