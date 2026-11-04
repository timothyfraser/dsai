#!/usr/bin/env bash
# check.sh
# Run the bounded job's checks.
# Course kit, module 16
#
# Usage, from this folder:
#   AGENT_STUB=1 bash check.sh     # no model: a known-good fix on a scratch copy; all pass
#   AGENT_STUB=bad bash check.sh   # no model: a fix that also edits the test; C2 fails
#   bash check.sh                  # your agent's real job/ folder, after run_job.sh

set -euo pipefail
cd "$(dirname "$0")"

# 1. RUN THE CHECKS ###################################
python3 check_job.py
