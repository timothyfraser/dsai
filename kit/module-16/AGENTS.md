# AGENTS.md (task contract)

You are a small local model working on ONE task. Follow this file exactly.
Keep this file short; every line here is re-read on every turn.

## TASK

- GOAL: make tests/test_convert.py::test_psi_to_kpa pass
- FILE YOU MAY EDIT: convert.py
- FILES YOU MAY READ: convert.py and tests/test_convert.py, nothing else
- CHECK COMMAND: python3 -m unittest tests.test_convert
- DONE WHEN: the CHECK COMMAND exits 0.

## Allowed commands

You may run only these, exactly as written:

1. The CHECK COMMAND.
2. `cat <a file you may read>`
3. `git diff`

Do not install packages. Do not use the network. Do not create new files.
Do not touch any file not named in the TASK block, including tests.

## How to work

1. Run the CHECK COMMAND once and read the error.
2. Read the FILE YOU MAY EDIT.
3. Make the smallest edit that fixes the error. One edit at a time.
4. Run the CHECK COMMAND again.
5. Repeat steps 3 and 4.

## Stop rule

Stop and write your report when ANY of these is true:

- The CHECK COMMAND exits 0.
- You have run the CHECK COMMAND 4 times and it still fails.
- The fix needs a file you are not allowed to edit.
- You are unsure what the task means.

Do not keep going after you stop. Do not start a second task.

## Report format

Reply with exactly these four lines and nothing else:

```
STATUS: PASS | FAIL | BLOCKED
CHANGED: <path>:<line numbers>, or none
CHECK: <last line of the CHECK COMMAND output>
NOTE: <one sentence: what you changed, or why you stopped>
```
