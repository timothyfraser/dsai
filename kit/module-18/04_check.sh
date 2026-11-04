#!/usr/bin/env bash
# 04_check.sh
# The lab's checks, from a terminal: bash kit/module-18/04_check.sh
# Course kit, module 18
#
# Runs 04_check.py, which prints one PASS / FAIL / SKIP line per check.
# Run it from the top of the course repo, so 06_agents/06_jfk_short.wav resolves.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${PYTHON:-python3}" "$HERE/04_check.py" "$@"
