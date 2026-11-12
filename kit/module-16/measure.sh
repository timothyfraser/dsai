#!/usr/bin/env bash
# measure.sh
# Optional: measure how fast your laptop reads a prompt and writes an answer.
# Course kit, module 16
#
# Only for the optional local step up (Step 7). The default path runs on Gemini.
# Usage, from this folder, with Ollama running:
#   bash measure.sh                         # the optional local model
#   MODEL=granite4:3b bash measure.sh       # any model you have pulled
#
# Read two numbers from the --verbose block: "prompt eval rate" is how fast the
# model reads (prefill), and "eval rate" is how fast it writes. Both are tokens/s.

set -euo pipefail
cd "$(dirname "$0")"
MODEL="${MODEL:-ministral-3:8b-32k}"  # optional step up for a 16 GB laptop

# 0. WHAT IS LOADED, AND WHERE ###################################
# Load the model first with a one-word reply, so ollama ps has something to show.
ollama run "$MODEL" "Reply with one word: ok." > /dev/null
# PROCESSOR says 100% GPU on a Mac; CPU is much slower.
ollama ps

# 1. A FIXED PROMPT, SO EVERYONE MEASURES THE SAME THING ###################################
# The contract plus the toy code: about the size of one real agent turn.
PROMPT="$(cat AGENTS.md toy/convert.py toy/tests/test_convert.py)
Reply with one word: ready."

# 2. TIME IT ###################################
ollama run "$MODEL" --verbose "$PROMPT"

# 3. DO THE ARITHMETIC ###################################
# seconds to read a preamble = preamble tokens / prompt eval rate.
# Try 3,000 (a lean agent), 7,000 and 33,000 (two default agents) with your rate.
