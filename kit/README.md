# Course kit

This folder holds the course kit: small scripts, check scripts and example files written for the course book, one folder per module. The rest of this repository is the instructor's course material; the kit sits beside it and does not change it.

Each module page in the book prints its kit files in full and tells you to save them under `kit/module-NN/` in your own course folder. If you cloned this repository, they are already here.

## What is in a module folder

- **A check script** (`check.sh`, `check.py` or `check.mjs`). It runs the module's lab or practice checks and prints one line for each, starting with `PASS` or `FAIL`.
- **A stub mode.** Most check scripts read an environment variable such as `API_STUB=1`, `LLM_STUB=1` or `EDGE_STUB=1`. With it set, the script checks a small example built into the kit instead of your own work, so you can see every check pass before you start. Where a script also accepts `=bad`, it checks an example broken on purpose, so you can see a failure.
- **Example files** the module's steps use: sample data, a toy project, or a fixture folder.

Every file starts with a comment that names its module. Read that comment and the module page before you run anything.

## The folders

| Folder | Module and what its checks do |
|---|---|
| `module-01/` | Module 1: Set up, and query your first API. Checks: a decision file check: the entry names a real option and gives a reason a reviewer can read. |
| `module-02/` | Module 2: Productivity with AI. Checks: a contract check against your API, a React-over-API check, and a decision file check. |
| `module-03/` | Module 3: AI as an API, and evals. Checks: scripted report checks on a saved run folder, plus a decision file check. |
| `module-04/` | Module 4: Deployment. Checks: live API checks (status, shape, health) plus a decision file check. |
| `module-05/` | Module 5: Function calling, agents with tools, and your first MCP server. Checks: a decision file check for the tool-or-agent choice. |
| `module-06/` | Module 6: Data management. Checks: repair checks on a messy table, run on the module's data folder. |
| `module-07/` | Module 7: RAG: retrieval-augmented generation, and alternatives. Checks: retrieval checks on a good and a deliberately broken example. |
| `module-08/` | Module 8: Agents: prompts, roles, rules, many agents. Checks: a decision file check for the agent-design choice. |
| `module-09/` | Module 9: Pipelines and cron. Checks: pipeline checks (rows stored today, no duplicate minutes) and a decision file check. |
| `module-10/` | Module 10: AI in the browser. Checks: browser-model checks driven by a headless browser, with a fake model in stub mode. |
| `module-11/` | Module 11: Evaluation. Checks: verification and validation checks from `checks.yaml` on saved outputs, plus a decision file check. |
| `module-12/` | Module 12: Better user interfaces. Checks: interface checks on the page and its API link, with a finished and a half-done example. |
| `module-13/` | Module 13: Decision support. Checks: a decision check on the module's example decision. |
| `module-14/` | Module 14: Hackathon. Checks: a decision file check and an example decision for the hackathon. |
| `module-15/` | Module 15: A bounded autonomous agent over HTTP. Checks: a decision file check for the bounded-agent choice. |
| `module-16/` | Module 16: Local agents: a small model, a strict contract, a real job. Checks: job checks on the toy project, with a pinned fingerprint of its files. |
| `module-17/` | Module 17: Vision models. Checks: checks that the photo-to-record tool returns a valid record from a stub reply, plus a decision file check. |
| `module-18/` | Module 18: Audio models: listen, transcribe, speak. Checks: a decision file check for the audio pipeline choice. |
| `module-19/` | Module 19: Geo LLMs: addresses, parcels, places. Checks: geo pipeline checks on saved replies, plus a decision file check. |
| `module-20/` | Module 20: Models on your phone. Checks: phone-model checks driven by a headless browser, with a fake model in stub mode. |
| `module-21/` | Module 21: APIs that sleep: scale to zero. Checks: scale-to-zero checks against a pretend host (cold start, cache route, cost estimate), plus a decision file check. |
| `module-22/` | Module 22: Data architecture: where each piece of data lives. Checks: architecture, contract, dictionary, lineage and no-keys checks on a worked example team folder. |
| `module-23/` | Module 23: Finale. Checks: finale checks on the saved example, plus a decision file check. |

Every module has a kit folder. A module whose folder holds only a decision check has no run-it-yourself lab script; the check reads your `DECISION.md`.
