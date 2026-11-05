#!/usr/bin/env bash
# check.sh
# Run the lab's nine checks
# Course kit, module 21
#
# Usage, from your lab folder:
#   API_URL=https://connect.example.com/content/abc bash check.sh
#   CHECK_STUB=1 bash check.sh        # the kit's example files against the pretend host
#   CHECK_STUB=broken bash check.sh   # the same, broken on purpose: watch the checks fail

set -euo pipefail
python3 "$(dirname "$0")/check.py"
