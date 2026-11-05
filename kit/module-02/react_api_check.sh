#!/usr/bin/env bash
# react_api_check.sh
# Check a running API and a built React page: the lab's live checks.
# Course kit, module 02
#
# From this folder:
#   APP_STUB=1 bash react_api_check.sh      # a stub API and the bundled example/web, which pass
#   APP_STUB=bad bash react_api_check.sh    # a stub and example_bad/web, broken on purpose
#   API_URL=http://127.0.0.1:8000 WEB_DIR=path/to/your/web bash react_api_check.sh

set -euo pipefail
cd "$(dirname "$0")"
python3 check_react_api.py
