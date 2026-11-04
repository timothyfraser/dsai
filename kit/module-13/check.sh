#!/usr/bin/env bash
# check.sh
# Run the lab's checks on a decision record and its audit log.
# Course kit, module 13
#
# Usage, from this folder:
#   LLM_STUB=1 bash check.sh     # no model, no team files: checks the saved example
#   bash check.sh                # checks your team's decision/ folder

set -euo pipefail
cd "$(dirname "$0")"

# 1. PICK THE FOLDER ###################################
if [ "${LLM_STUB:-0}" = "1" ]; then
  FOLDER=example
else
  FOLDER=decision
fi

# 2. RUN THE CHECKS ###################################
python3 check_decision.py "$FOLDER"
