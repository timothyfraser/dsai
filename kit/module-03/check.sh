#!/usr/bin/env bash
# check.sh
# Check a team's reporter output folder against the lab's scriptable checks.
# Course kit, module 03
#
# Copy this folder into your repo, then, from this folder:
#   REPORT_STUB=1 bash check.sh            # no model: checks the bundled example/ folder
#   REPORT_STUB=bad bash check.sh          # checks example_bad/, broken on purpose, to show FAIL
#   bash check.sh path/to/your/folder      # checks your own reporter output folder

set -euo pipefail
cd "$(dirname "$0")"
case "${REPORT_STUB:-}" in
  1)   FOLDER="example" ;;
  bad) FOLDER="example_bad" ;;
  *)   FOLDER="${1:-.}" ;;
esac
python3 check_report.py "$FOLDER"
