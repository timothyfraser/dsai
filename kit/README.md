# Course kit

This folder holds the course kit: small scripts, check scripts and example files written for the course book, one folder per module. The rest of this repository is the instructor's course material; the kit sits beside it and does not change it.

Each module page in the book prints its kit files in full and tells you to save them under `kit/module-NN/` in your own course folder. If you cloned this repository, they are already here.

## What is in a module folder

- **A check script** (`check.sh`, `check.py` or `check.mjs`). It runs the module's lab or practice checks and prints one line for each, starting with `PASS` or `FAIL`.
- **A stub mode.** Most check scripts read an environment variable such as `API_STUB=1`, `LLM_STUB=1` or `EDGE_STUB=1`. With it set, the script checks a small example built into the kit instead of your own work, so you can see every check pass before you start. Where a script also accepts `=bad`, it checks an example broken on purpose, so you can see a failure.
- **Example files** the module's steps use: sample data, a toy project, or a fixture folder.

Every file starts with a comment that names its module. Read that comment and the module page before you run anything.

## The folders

| Folder | Module |
|---|---|
| `module-02/` | Module 2: The loop and the contract |
| `module-03/` | Module 3: AI as an API, and evals |
| `module-04/` | Module 4: Ship an API and a React app |
| `module-06/` | Module 6: Where the data lives |
| `module-07/` | Module 7: Retrieval and its alternatives |
| `module-09/` | Module 9: Pipelines and cron |
| `module-10/` | Module 10: Edge and browser |
| `module-11/` | Module 11: V&V for AI systems |
| `module-12/` | Module 12: Interfaces |
| `module-13/` | Module 13: Decision support |
| `module-17/` | Module 17: Vision models |
| `module-18/` | Module 18: Audio models: listen, transcribe, speak |
| `module-19/` | Module 19: Geo LLMs: addresses, parcels, places |
| `module-20/` | Module 20: Models on your phone |

Modules 1, 5, 8, 14 and 15 have no kit folder: their steps use the instructor's own files only. Module 16 is added once its review is complete.
