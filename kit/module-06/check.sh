#!/usr/bin/env bash
# check.sh
# Run the repair pipeline, then run the lab's checks on what it wrote.
# Course kit, module 6
#
# Usage, from this folder:
#   LLM_STUB=1 bash check.sh            # no model: saved proposals, proves the pipeline and checks
#   bash check.sh                       # your model through Ollama (OLLAMA_HOST, OLLAMA_MODEL)

set -euo pipefail
cd "$(dirname "$0")"

# 0. CLEAR OLD OUTPUT ###################################
rm -f output/inventory.db output/audit.jsonl

# 1. RUN THE PIPELINE ###################################
python3 repair_table.py

# 2. RUN THE CHECKS ###################################
python3 check_repair.py
