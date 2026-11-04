#!/usr/bin/env bash
# check.sh
# Check a team's app folder against the lab's scriptable checks.
# Course kit, module 02
#
# Copy this folder into your repo, then, from this folder:
#   CONTRACT_STUB=1 bash check.sh          # checks the bundled example/ folder, which passes
#   CONTRACT_STUB=bad bash check.sh        # checks example_bad/, broken on purpose, to show FAIL
#   bash check.sh path/to/your/app         # checks your own team's app folder

set -euo pipefail
cd "$(dirname "$0")"
case "${CONTRACT_STUB:-}" in
  1)   FOLDER="example" ;;
  bad) FOLDER="example_bad" ;;
  *)   FOLDER="${1:-.}" ;;
esac
python3 check_contract.py "$FOLDER"
