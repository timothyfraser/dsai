---
name: kit-checks
description: How to run and read the check scripts in kit/module-NN (check.sh, check.py, check.mjs). Each prints one PASS or FAIL line per check and exits 1 on any FAIL. Covers the stub modes (API_STUB=1, LLM_STUB=1, EDGE_STUB=1, AGENT_STUB=1 and the others), the =bad runs that are broken on purpose, and what to do with a FAIL. Use when someone asks to run a module check, reads a PASS/FAIL line, or wants to see a check fail on purpose.
---

# Running the kit's check scripts

`kit/README.md` explains the folder. This skill is how to run one and read what it says. Every
module folder `kit/module-NN/` has a check script: `check.sh`, `check.py` or `check.mjs`. Read the
comment at the top of the script first; it names the module and prints the exact usage.

## What a run looks like

One line per check, starting with `PASS` or `FAIL`, then a short reason in brackets, then a
summary line. Real output from `API_STUB=1 bash kit/module-04/check.sh`:

```
PASS  C3 /health answers 200  (got 200)
PASS  C4 /health is JSON and says ok  ({'status': 'ok'})
PASS  C5 /greetings/en returns the documented shape  (keys ['lang', 'text'])
PASS  C6 the smoke test fails on a wrong address
PASS  C7 the app answers 200  (got 200)

5 passed, 0 failed, 0 skipped
```

The script exits 0 when nothing failed and 1 when any check failed, so you can chain it:
`bash check.sh && echo ready`. A check number (C3, R9) matches the numbered checks on the module page.
Some checks cannot be scripted (does the page look right, did every teammate commit); the summary
line says which ones a reviewer reads by hand. A script saying "9 of 9 pass" does not mean the lab is done.

## Stub modes: see it pass before you start

Most scripts read an environment variable that swaps your work for a small example built into the
kit, so no server, key or model is needed. Set it on the same line as the command:

| Variable | Used for | What `=1` does |
|---|---|---|
| `CONTRACT_STUB` | module 02, the repo contract | checks `example/`, which passes |
| `REPORT_STUB` | module 03, the evals report | checks `example/`, which passes |
| `API_STUB` | module 04, a deployed API | starts a tiny local server that answers like a healthy one |
| `LLM_STUB` | modules that call a model (6, 7, 13, 19 and others) | a stand-in replies instead of a real model: no key, no tokens, the same answer every time |
| `PIPE_STUB` | module 09, pipelines | an example folder and a stub stand in for your pipeline |
| `EDGE_STUB` | module 10, edge and browser | fakes the on-device model, no download |
| `VV_STUB` | module 11, V&V | checks the outputs already on disk |
| `AGENT_STUB` | module 16, local agents | applies a known-good fix on a scratch copy |
| `VLM_STUB`, `AUDIO_STUB` | modules 17 and 18 | a stand-in for the vision or audio model |

Not every script has every variable: open the script and read its header.

## `=bad`: broken on purpose

Where a script accepts `bad` (for example `REPORT_STUB=bad`, `CONTRACT_STUB=bad`, `LLM_STUB=bad`,
`AGENT_STUB=bad`), it checks an example that was broken on purpose so you can see what a FAIL
looks like and which line names the problem. Real output from `REPORT_STUB=bad bash kit/module-03/check.sh`:

```
FAIL  C3 runs/ holds at least 10 saved runs  (found 6)
FAIL  C2 every run uses the same field labels  (missing ['run_03.txt:Count'])
...
0 of 6 scripted checks pass. C1, C5, C9 and the git-history part of C8 are for a reviewer.
```

Run the `=1` version first (all PASS), then the `=bad` version (several FAIL), then your own. Only a
script you have watched fail can be trusted when it says PASS.

The bad example folder (for example `kit/module-03/example_bad`) holds a fake key-shaped string on
purpose, to trigger the key check. Do not copy it, and do not "fix" it.

## Running it on your own work

```bash
bash kit/module-04/check.sh                            # your API, from API_URL and APP_URL
API_URL=https://your-server/your-api APP_URL=https://your-server/your-app bash kit/module-04/check.sh
bash kit/module-03/check.sh path/to/your/folder        # a folder argument, where the header says so
```

Run from the repo root or from the module folder; the scripts `cd` to their own folder. They use only
the standard library (or Node and Playwright for `check.mjs`: install once with `npm install playwright`
then `npx playwright install chromium`).

## When a line says FAIL

1. Read the bracket after the line: it says what the script saw.
2. Fix one thing, run again. Do not change the check script to make it pass.
3. If a check seems wrong, show the FAIL line to the instructor; do not edit the script.
4. Never put a key in a file to get past a check. The key check exists to catch exactly that.
5. Quote the final PASS/FAIL output when you tell anyone the task is done.

An agent must paste the real output of the check, not a summary, before it says a check passes.
