---
description: "Build ONE CONTRACT task (e.g. /build P-03): reads SPEC.md first, writes tests then code, never commits. Review is a separate step: /new, then /review P-03"
agent: build
model: google/gemini-3.1-flash-lite
---
Task id: $1
If the task id above is blank, list the todo tasks in CONTRACT.yaml and ask me which one. Do not guess.

You build exactly this ONE task from CONTRACT.yaml. You are the IMPLEMENTER only. Do not launch subagents or any other agent, and do not review your own work: the review is a separate step that I run in a fresh session (/new, then /review with this task id).

1. Before anything else, read SPEC.md completely (section 4 is the method and the known-answer check), docs/plan.md if it exists, and this task's block in CONTRACT.yaml.
2. In one sentence, restate the rule this task implements, exactly as SPEC.md section 4 states it. Stop and ask me if SPEC.md section 4 still says FILL IN, or if its known-answer check has no concrete numbers (the input data AND the expected values). A known-answer check with no concrete numbers counts as FILL IN. Never invent a rule or a known answer.
3. If you do not know my name for the owner field, ask me once. Get the time by running this command: date "+%Y-%m-%d %H:%M" (if it fails, run: python -c "import datetime; print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M'))"). Load the contract-ledger skill and check the task out: status: in_progress, owner, and started_at = the time the command printed, pasted (never a time you made up). Never delete a field. Quote any value that contains a colon.
4. If the task computes a result, load the logic-first-steering skill. Write the tests first, then the code:
   - a known-answer test whose data and expected numbers are copied from SPEC.md section 4, never made up;
   - a degenerate case (empty input, one item, or a wrong type): the code must raise a clear error or return a message saying what is wrong. A confident-looking answer (0, inf, an empty result) is wrong, and a test that accepts one is wrong.
5. Deliver EVERY function and route SPEC.md names, not just the first one. For a React page over an API that means: the logic in its own file with no web framework imported, the route that calls it, and the health route.
6. Stay inside the task's owns list:
   - Edit only the paths in its owns list, plus this task's block in CONTRACT.yaml.
   - Never delete, move or rename a file. Never create a file outside the owns list; scratch checks go in tests/ (or another folder on the owns list), never at the repo root.
   - Every third-party package you import (numpy, pandas, scipy, ...) goes into the requirements file (for example api/requirements.txt) in the same step. If that file is not on the owns list, stop and tell me the exact line to add.
   - Use absolute package imports (from logic import ...), never relative ones (from .qc import ...). The app and every script must start from the repo root with one command.
   - If you need any other file, stop and ask me.
7. Never run a server, testme.sh or any other long-running command in the foreground: it hangs the session. Start it in the background with a time limit (for example: timeout 120 bash api/testme.sh &), or ask me to run it. Stop only the process you started, by its PID. Never kill processes by name (taskkill /IM, pkill, killall, Stop-Process -Name).
8. Work in small steps. After each step run the tests and read the real output.
9. Run the task's definition_of_done exactly as written. For an API or app task, start the app in the background (step 7), call the endpoint (or open the page) on one data/ file, and paste the real response.
10. If you get a 429, quota or rate-limit error, stop and tell me. Do not retry in a loop.
11. Do not commit, do not push, do not check the task in, and do not start another task.

End your final message with these parts, pasted, not summarized:
RULE: the one sentence from step 2
RESULTS: every result SPEC.md names, one per line, with its value on the known-answer data. A missing one means the task is NOT DONE.
FILES: every file you created or changed
RUN: the one command, run from the repo root, that starts the app
TESTS: the test command and its real output
DEFINITION OF DONE: the definition_of_done command and its real output
NEXT: type /new, then /review with this task id
