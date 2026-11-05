#!/usr/bin/env bash
# check.sh
# Check a team's reporter output folder against the lab's scriptable checks, then check its DECISION.md.
# Course kit, module 03
#
# Copy this folder into your repo, then, from this folder:
#   REPORT_STUB=1 bash check.sh            # no model: checks the bundled example/ folder (C checks only)
#   REPORT_STUB=bad bash check.sh          # checks example_bad/, broken on purpose, to show FAIL (C checks only)
#   DECISION_STUB=1 bash check.sh          # the example folder and its example/DECISION.md (C and D checks)
#   DECISION_STUB=bad bash check.sh        # the example folder, with a DECISION.md broken on purpose
#   bash check.sh path/to/your/folder      # your own reporter folder; it must hold DECISION.md

set -uo pipefail
cd "$(dirname "$0")"
RUN_DECISION=1
case "${DECISION_STUB:-}" in
  1)   FOLDER="example"; DECISION="example/DECISION.md" ;;
  bad) FOLDER="example"; DECISION="example_bad/DECISION.md" ;;
  *)
    case "${REPORT_STUB:-}" in
      1)   FOLDER="example"; RUN_DECISION=0 ;;
      bad) FOLDER="example_bad"; RUN_DECISION=0 ;;
      *)   FOLDER="${1:-.}"; DECISION="$FOLDER/DECISION.md" ;;
    esac ;;
esac

status=0
python3 check_report.py "$FOLDER" || status=1
if [ "$RUN_DECISION" = 1 ]; then
  echo
  python3 check_decision.py "$DECISION" || status=1
fi
exit $status
