#!/usr/bin/env bash
# check.sh
# Run the team's verification and validation plan: every machine check in checks.yaml, then the lab's checks.
# Course kit, module 11
#
# Copy this folder into your repo, put your checks.yaml next to this file, then:
#   VV_STUB=1 bash check.sh            # no model: check the outputs already on disk
#   bash check.sh                      # run your system first, then check
#   VV_STUB=bad bash check.sh          # check the outputs you broke on purpose

set -euo pipefail
cd "$(dirname "$0")"
python3 check_vv.py "${1:-checks.yaml}"
