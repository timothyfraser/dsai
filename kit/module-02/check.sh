#!/usr/bin/env bash
# check.sh
# Check a team's app folder against the lab's scriptable checks.
# Course kit, module 02
#
# It runs three scripts in turn: check_contract.py (the contract, the rules and the docs),
# check_decision.py (DECISION.md), and react_api_check.sh (the running API and the built page).
#
# Copy this folder into your repo, then, from this folder:
#   CONTRACT_STUB=1 bash check.sh          # the bundled example/ folder and a stub API: passes
#   CONTRACT_STUB=bad bash check.sh        # example_bad/, broken on purpose, to show FAIL
#   API_URL=http://127.0.0.1:8000 bash check.sh path/to/your/app   # your own team's app

set -uo pipefail
cd "$(dirname "$0")"
case "${CONTRACT_STUB:-}" in
  1)   FOLDER="example";     export APP_STUB=1 ;;
  bad) FOLDER="example_bad"; export APP_STUB=bad ;;
  *)   FOLDER="${1:-.}";     export WEB_DIR="${WEB_DIR:-$FOLDER/web}" ;;
esac
status=0
python3 check_contract.py "$FOLDER" || status=1
echo "----"
python3 check_decision.py "$FOLDER/DECISION.md" || status=1
echo "----"
bash react_api_check.sh || status=1
exit $status
