#!/usr/bin/env bash
# run_job.sh
# Set up one bounded job and hand it to a small model in OpenCode.
# Course kit, module 16
#
# Usage, from this folder, with your Gemini key loaded (Step 3):
#   bash run_job.sh
#   MODEL=ollama/ministral-3:8b-32k bash run_job.sh   # optional step up for a 16 GB laptop, with Ollama running
#
# It copies toy/ into a fresh job/ folder, so the agent never edits the kit's
# own copy. It deletes nothing: if job/ already exists it stops and tells you.
# Only the toy project's code goes to the model; it is public course code.

set -euo pipefail
cd "$(dirname "$0")"
MODEL="${MODEL:-google/gemini-flash-lite-latest}"

# 0. CHECK THE TOOLS AND THE KEY ARE THERE ###################################
for tool in opencode git python3; do
  command -v "$tool" >/dev/null || { echo "Missing: $tool. Install it first (Step 3)."; exit 1; }
done
case "$MODEL" in
  google/*)
    # OpenCode reads the key under this name; the course keeps it as GEMINI_API_KEY.
    export GOOGLE_GENERATIVE_AI_API_KEY="${GOOGLE_GENERATIVE_AI_API_KEY:-${GEMINI_API_KEY:-}}"
    [ -n "$GOOGLE_GENERATIVE_AI_API_KEY" ] || { echo "Missing: GEMINI_API_KEY. Load your key first (Step 3)."; exit 1; } ;;
  ollama/*)
    command -v ollama >/dev/null || { echo "Missing: ollama. Install it first (Module 3)."; exit 1; } ;;
esac

# 1. MAKE A FRESH COPY OF THE TOY PROJECT ###################################
# A copy, not the original: the check compares the copy against toy.sha256.
if [ -e job ]; then
  echo "job/ already exists. Move it aside (mv job job_old) and run this again."
  exit 1
fi
cp -R toy job
cp AGENTS.md opencode.json job/
# A git baseline, so the contract's `git diff` shows exactly what the agent changed.
( cd job && git init -q && git add -A && \
  git -c user.name=kit -c user.email=kit@localhost commit -q -m "baseline" )

# 2. SAY WHAT IS ABOUT TO HAPPEN ###################################
echo "1. The agent reads job/AGENTS.md: one goal, one file, three commands."
echo "2. Model: $MODEL"
echo "3. Its reply goes to job_reply.txt. Then run: bash check.sh"

# 3. START THE AGENT ON THE JOB ###################################
# One short prompt: the contract carries the rest, so the prompt stays tiny.
# --standalone runs a private OpenCode server for this job, and --title skips a
# model call that names the session. The two settings keep OpenCode from adding
# your other agent files and from fetching its model list. Each one cuts startup time.
start=$(date +%s)
( cd job && OPENCODE_DISABLE_CLAUDE_CODE=1 OPENCODE_DISABLE_MODELS_FETCH=1 \
  opencode run --standalone --title m16 --agent lean --model "$MODEL" "Do the task in AGENTS.md." ) | tee job_reply.txt
echo "Wall time: $(( $(date +%s) - start )) s"
