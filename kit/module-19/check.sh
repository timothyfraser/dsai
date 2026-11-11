#!/usr/bin/env bash
# check.sh
# Run the geo-cleaning pipeline, then run the lab's checks on what it wrote.
# Course kit, module 19
#
# Usage, from this folder:
#   LLM_STUB=1 bash check.sh            # no model: saved replies, proves the pipeline and checks
#   bash check.sh                       # a live model (GEMINI_API_KEY, or LLM_BASE_URL and LLM_MODEL for local Ollama)
#   CHECK_LANG=r LLM_STUB=1 bash check.sh   # the R script instead of the Python one

set -euo pipefail
cd "$(dirname "$0")"

# 0. CLEAR OLD OUTPUT ###################################
rm -f output/addresses_clean.csv output/changes.jsonl

# 1. RUN THE PIPELINE ###################################
if [ "${CHECK_LANG:-python}" = "r" ]; then
  Rscript geo_clean.R
else
  python3 geo_clean.py
fi

# 2. RUN THE CHECKS ###################################
python3 check_geo.py

# 3. RUN THE DECISION CHECK ###################################
# DECISION_STUB=1 checks the saved example, DECISION_STUB=bad a saved bad one (it must fail).
# With LLM_STUB=1 and no DECISION_STUB set, the saved example is used; otherwise your DECISION.md.
if [ "${LLM_STUB:-0}" = "1" ] && [ -z "${DECISION_STUB:-}" ]; then
  export DECISION_STUB=1
fi
python3 check_decision.py
