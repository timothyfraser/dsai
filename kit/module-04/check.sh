#!/usr/bin/env bash
# check.sh
# Check a deployed API and app from the outside: the lab's live checks C3 to C7.
# Course kit, module 4
#
# Usage, from this folder:
#   API_URL=https://your-server/your-api APP_URL=https://your-server/your-app bash check.sh
#   API_STUB=1 bash check.sh            # no server handy: a small local stub stands in

set -euo pipefail
cd "$(dirname "$0")"
python3 check_api.py
