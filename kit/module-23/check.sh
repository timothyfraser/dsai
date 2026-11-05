#!/usr/bin/env bash
# check.sh
# Run the Finale lab's checks on a finished team repo.
# Course kit, module 23
#
# Usage, from the top of the course repo:
#   FINALE_STUB=1 bash kit/module-23/check.sh          # the saved example: every check passes
#   FINALE_STUB=broken bash kit/module-23/check.sh     # a broken copy: the checks must fail
#   bash kit/module-23/check.sh /path/to/your/repo     # your team's own repo

set -euo pipefail
START="$PWD"
cd "$(dirname "$0")"

# 1. PICK THE FOLDER ###################################
case "${FINALE_STUB:-0}" in
  1)
    FOLDER=example ;;
  broken)
    # A scratch copy with five things a hand-off gets wrong. The example itself is never touched.
    FOLDER="$(mktemp -d)/broken"
    cp -r example "$FOLDER"
    sed -i 's/^Instead of: .*//' "$FOLDER/ARCHITECTURE.md"                # a box with no rejected alternative
    sed -i '/^## D2/,/^## D3/{/^Evidence:/d}' "$FOLDER/DECISIONS.md"      # a decision with no evidence
    sed -i 's/our model/the AI/' "$FOLDER/STANDUP.md"                      # the work handed to a tool
    printf 'OPENAI_API_KEY=sk-%s\n' "$(printf 'x%.0s' $(seq 1 40))" > "$FOLDER/.env"  # a fake key, left behind
    rm -rf "$FOLDER/runs"                                                  # no run records
    ;;
  *)
    FOLDER="$(cd "$START" && cd "${1:-.}" && pwd)" ;;   # your path, read from where you ran it
esac

# 2. RUN THE CHECKS ###################################
python3 check_decision.py "$FOLDER"
