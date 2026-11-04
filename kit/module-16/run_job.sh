#!/usr/bin/env bash
# run_job.sh
# Set up one bounded job and hand it to a local agent in OpenCode.
# Course kit, module 16
#
# Usage, from this folder, with Ollama running and the 32k model created:
#   bash run_job.sh
#   MODEL=ollama/qwen3:8b bash run_job.sh     # try the second-choice model
#
# It copies toy/ into a fresh job/ folder, so the agent never edits the kit's
# own copy. It deletes nothing: if job/ already exists it stops and tells you.

set -euo pipefail
cd "$(dirname "$0")"
MODEL="${MODEL:-ollama/ministral-3:8b-32k}"

# 0. CHECK THE TOOLS ARE THERE ###################################
for tool in ollama opencode git python3; do
  command -v "$tool" >/dev/null || { echo "Missing: $tool. Install it first (Step 3)."; exit 1; }
done

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
start=$(date +%s)
( cd job && opencode run --agent lean --model "$MODEL" "Do the task in AGENTS.md." ) | tee job_reply.txt
echo "Wall time: $(( $(date +%s) - start )) s"
