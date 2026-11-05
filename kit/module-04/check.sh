#!/usr/bin/env bash
# check.sh
# Run the lab's checks: the live API and page (C3 to C9), then the decision file (D1 to D8).
# Course kit, module 4
#
# Usage, from this folder:
#   API_URL=https://your-server/your-api PAGE_URL=https://your-server/your-page bash check.sh path/to/DECISION.md
#   API_STUB=1 bash check.sh            # no server handy: a local stub stands in, and the saved example decision
#   API_STUB=bad bash check.sh          # the stub, and a decision file broken on purpose, to show FAIL

set -uo pipefail
cd "$(dirname "$0")"

# 1. PICK THE DECISION FILE ###################################
case "${API_STUB:-}" in
  1)   DECISION="example/DECISION.md" ;;
  bad) DECISION="example_bad/DECISION.md" ;;
  *)   DECISION="${1:-DECISION.md}" ;;
esac

# 2. RUN BOTH CHECKS, AND FAIL IF EITHER FAILS ###################################
status=0
python3 check_api.py || status=1
echo
python3 check_decision.py "$DECISION" || status=1
exit $status
