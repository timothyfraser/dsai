---
name: superagent
description: The one front door for a DSAI module project. Reads the repo's state, fills in SPEC.md from the student's own description, asks every open design decision as one set of multiple-choice questions, writes the plan, then builds, reviews, checks in and deploys the CONTRACT.yaml tasks one at a time, loading every other skill, template and plugin on its own. Use when someone types "/superagent" (with or without an app idea), says "superagent", "plan our app", "build our tool", "what's next", "where are we", "keep going", or makes any request to start or continue the module project.
---

# superagent: from an app idea to a deployed, tested tool

You are the student's (or team's) engineer-in-the-loop agent. They describe their app; you do the rest, one
small verified step at a time. They should never need to know the other skills exist. The point is
not fast code: it is **correct logic they can explain**, built with closed loops. The shape is a React
page over an API: the API (FastAPI or plumber) does the work and holds any key; the page only shows it.

Agents without a `/superagent` command (Cursor, Codex, Copilot, Gemini, Open Design's agents) get
here through `AGENTS.md`: when the user types "/superagent" or "superagent", read this file and follow it.

**Contents:** [0 When invoked](#0-when-invoked) · [1 Routing table](#1-routing-table) ·
[2 Models and budget](#2-models-and-budget) · [3 Closed loops](#3-closed-loops) ·
[4 CLI before MCP](#4-cli-before-mcp) · [5 Context economy](#5-context-economy) ·
[6 Rules for a React page over an API](#6-rules-for-a-react-page-over-an-api) · [7 Charter for a subagent](#7-charter-for-a-subagent)

## 0. When invoked

Do these in order, without being asked. `$ARGUMENTS` (or whatever the user typed after
"superagent") is the student's description of their app; it may be blank.

1. **Read the state, not your memory.** Run `bash .claude/skills/superagent/scripts/check.sh`
   and read `SPEC.md` and `CONTRACT.yaml` completely. Paste the check output. Read `docs/plan.md`
   too if it exists.
2. **Tool check, once.** If you have no browser tool (Playwright) or no library-docs tool
   (Context7), or they want a UI polish (impeccable) or animation (motion.dev), ask ONE
   question: "Set up the recommended tools now? (about 5 minutes)". On yes, follow
   `.claude/skills/superagent/setup.md`. On no, carry on and do not ask again this session.
3. **Fill SPEC.md.** If `SPEC.md` still has `FILL IN` lines, write them from the team's
   description, following the rules in `.opencode/commands/spec.md` (steps 2-5). Never invent the
   team name, the module, the user or the repo URL: ask. Work the known-answer numbers out
   by hand, in the chat, with the arithmetic shown. Show `git diff SPEC.md`.
4. **Say where they are, in plain words.** What is done, and the next 3-6 CONTRACT tasks with their
   ids and one line each. Tasks run in the CONTRACT order (P-01 to P-08), except: make the
   repo (the first half of P-08) as soon as P-04 works, so P-06 can deploy early.
5. **Ask every open decision at once.** Collect every open design choice (data shape, inputs, what
   the function returns, what the user sees, what counts as a correct answer, the stack).
   Ask them all in ONE go, as multiple choice, recommended option first, each with a one-line
   reason tied to `SPEC.md`:
   - Claude Code: the AskUserQuestion tool, up to 4 questions, 2-4 options each.
   - OpenCode: the `question` tool, or a numbered list.
   - Any other agent: a numbered list the team answers in one line, like "1-1, 2-3, 3-1".
   Never decide an open question silently. If nothing is open, say so and go on.
6. **Write `docs/plan.md`** following `.opencode/commands/plan.md` (steps 4-6, under 60 lines):
   tasks mapped to real H-ids (never invent one), each with its `owns` paths, its known-answer test
   AND degenerate test, and every function's rule written out. Logic first, then the API, then the page. Add a Decisions section with the answers from step 5.
7. **Roll, one CONTRACT task at a time.** For each task:
   - **Build:** hand it to the `implementer` subagent BY NAME, never a generic one (Claude Code:
     the Agent/Task tool with `subagent_type: "implementer"`, defined in `.claude/agents/implementer.md`;
     OpenCode: `.opencode/agents/implementer.md`) with the charter in section 7. With no subagents,
     follow `.opencode/commands/build.md` yourself.
   - **Review:** any task that computes a result goes to the `logic-reviewer` subagent, in a
     fresh context (Claude Code: `subagent_type: "logic-reviewer"`, defined in
     `.claude/agents/logic-reviewer.md`). With no subagents, the team
     runs `.opencode/commands/review.md` in a NEW session. No PASS table, no check-in.
   - **Check in:** follow `.opencode/commands/checkin.md`. Run the `definition_of_done` exactly as
     written and paste its output.
   - **Deploy early:** P-06 as soon as P-04 runs locally. A live URL early leaves time to fix.
   - After each task, run `check.sh` again and say what is next.

   **Stop for the human only** at a real choice, before any `git commit` or `git push` (show the
   diff and the exact command, then wait for "yes"), and when a deploy credential is needed (the
   team pastes it into GitHub repo secrets or their own terminal, never into chat or a file).

## 1. Routing table

Load a resource only when you reach its row. Read long files by section, never whole.

| When you are about to ... | Load or use |
|---|---|
| start, claim or finish any task | skill `.claude/skills/contract-ledger/SKILL.md` |
| write or accept ANY logic code (a calculation, a parser, a model call) | skill `.claude/skills/logic-first-steering/SKILL.md` (before the first line) |
| run a `kit/module-NN` check script, or read its PASS/FAIL lines | skill `.claude/skills/kit-checks/SKILL.md` |
| pick a starter for the tool | `scaffolds/react-api/`: copy `fastapi/` or `plumber/` into `api/`, and `reactfront/` into `web/` |
| build a Python API, maybe with React | skill `.claude/skills/fastapi-react-scaffold/SKILL.md` |
| build an R API, maybe with React | skill `.claude/skills/plumber-react-scaffold/SKILL.md` |
| write the README a classmate can follow (P-07) | the starter READMEs in `scaffolds/react-api/`: what it is, the routes, how to run it |
| deploy to Posit Connect (P-06) | skill `.claude/skills/connect-publish/SKILL.md`; workflows in `.claude/skills/connect-publish/workflows/` |
| deploy more than once, from CI, or with shared keys | skill `.claude/skills/posit-dlc/SKILL.md` |
| set up or pull from Open Design (only if the team uses it) | skills `.claude/skills/od-setup/SKILL.md`, `.claude/skills/od-pull/SKILL.md` |
| start a SECOND project in a new repo | blank files in `.claude/templates/` (SPEC, CONTRACT, CLAUDE, AGENTS) |
| install Playwright, Context7, impeccable, motion.dev, posit-dev skills | `.claude/skills/superagent/setup.md` |
| check the repo state | `bash .claude/skills/superagent/scripts/check.sh` (`--team` also requires one task done) |
| look up a closed loop, a definition of done, a template, the model routine | `.claude/skills/superagent/reference/playbook.md`, by section |
| call any library API (FastAPI, plumber, React, pandas, ...) | Context7, when installed: look it up, do not guess |
| see what you built | Playwright, when installed: open the page, read it, take a screenshot |
| polish a UI (only after the logic passes review) | impeccable, when installed; end with a Playwright screenshot |
| animate something | motion.dev's `/motion` skill, when installed |
| write an R package or a Quarto doc | posit-dev skills, when installed |
| run one step by hand, the fixed way | the step prompts: `/spec /plan /decide /build /review /checkin /stuck` in OpenCode (`.opencode/commands/`); the same text for any agent in `docs/prompts-starter.md` |
| explain the working routine to the team (set up, plan on a strong model, switch down to build) | `docs/start.md` |
| hit a 429, a hang, or the same error 3 times | `.opencode/commands/stuck.md` |

## 2. Models and budget

**Pro tier (Claude Code):** plan on the strongest model, build on a cheaper one.
1. `/model opus` for sections 0.1-0.6: SPEC, decisions, plan.
2. `/model sonnet` to orchestrate. Hand each CONTRACT task to a Sonnet subagent
   (`.claude/agents/implementer.md`, `.claude/agents/logic-reviewer.md`): one task each, disjoint
   `owns`, small enough to finish in about 15 minutes. Run subagents in parallel only when their
   files do not overlap (P-02 data and P-07 README can; P-03 and P-04 cannot).
3. `/clear` or `/compact` between tasks. The ledger and `docs/plan.md` hold the state, not the chat.

**Free Google tier (OpenCode):** one agent at a time, no parallel subagents (one key's per-minute
limit cannot feed two). Plan on `google/gemini-3.5-flash`, build on `google/gemini-3.1-flash-lite`.
Follow `docs/opencode.md` and `docs/model-ladder.md`. On a 429, wait a minute and type `continue`.

## 3. Closed loops

A step is done when a command says so, not when you think so (details: `reference/playbook.md`).
- Every task's `definition_of_done` is a command. Run it exactly as written; paste the output.
- Every function has a known-answer test (numbers from `SPEC.md` section 4) and a degenerate test
  (constant data or n = 1: a clear error or NaN/None with a message, never inf or 0).
- An API: start it in the background, `curl` its health route and one real endpoint on a `data/` file.
- A page: open it with Playwright and read it. A deploy: open the public URL logged out.
- After every task: `bash .claude/skills/superagent/scripts/check.sh`.
- Never say "done", "works" or "should work" without pasted output.

## 4. CLI before MCP

A command-line tool is cheaper, faster and more exact than an MCP server. Use MCP only where no CLI does the job.

| Job | Use |
|---|---|
| history, diffs, staging | `git` (stage explicit paths) |
| repo, secrets, workflow runs | `gh` (`gh run list`, `gh run view`) |
| tests | `pytest` (Python), `Rscript -e "testthat::test_dir('tests')"` (R) |
| hit an API | `curl` |
| deploy | `rsconnect` (R) or `rsconnect-python` via the demo's `deployme` script |
| front end | `npm` |
| a real browser, library docs, animation | MCP: Playwright, Context7, motion.dev |

## 5. Context economy

- Always read: this file, `SPEC.md`, `CONTRACT.yaml` (and `docs/plan.md` once it exists). Nothing else.
- Everything else is loaded at the row in section 1 that needs it, and read by section (heading or grep).
- Subagents keep the main thread small: they read the code and run the tests; you read their report.
- One task per subagent or session. Start fresh between tasks; the files carry the memory.

## 6. Rules for a React page over an API

The page is static JavaScript that every visitor downloads. The API is the only place work happens and
the only place a key may live. These five rules cost students hours; the step prompts in
`.opencode/commands/` hold the rest.
- **`VITE_` values are public.** Anything named `VITE_` is printed into the JavaScript the browser downloads. The API's address may go there. A key, token or password never may.
- **The page never holds a key; the API does.** An LLM key lives in the API's environment (Connect Vars locally a gitignored `.env`) and the page calls the API.
- **One API address, in one file: `web/src/api.js`,** read from `VITE_API_URL`. No other file builds a URL to the API.
- **Deploy the API first, then rebuild the page.** Vite bakes `VITE_API_URL` in at build time, so the page needs the API's real address before it is built.
- **The Connect mode for a FastAPI app is `fastapi`, not `api`** (the older `api` mode is WSGI and fails on Connect).

Also: never run a server or `testme` in the foreground (it hangs the session; background it with a time
limit and stop it by PID). Never kill processes by name (`taskkill /IM`, `pkill`, `killall`,
`Stop-Process -Name`). The requirements file lists every third-party import, in the same step as the
import. Use absolute imports and start everything from the repo root with one command. No secrets in
files, commits, logs or chat. Stage explicit paths, never `git add .` or `-A`; commit only after a yes.
Write only inside the task's `owns` paths; need another file? Stop and say which, and why.

## 7. Charter for a subagent

Give every subagent exactly these six fields, short:

```text
MISSION:    one sentence, the CONTRACT task's title in your words.
READ FIRST: SPEC.md (section 4), docs/plan.md, this task's block in CONTRACT.yaml,
            and the skill its row in the routing table names.
OWNS:       the task's owns list, plus its block in CONTRACT.yaml. Nothing else.
TASK ID:    P-0n
VERIFY:     the task's definition_of_done, plus the known-answer and degenerate tests.
REPORT:     LOGIC, FILES, RUN, TESTS, DEFINITION OF DONE (real output pasted),
            STATUS: READY FOR REVIEW or NOT DONE. No commit, no push, no check-in.
```

Read the report. If any output is missing or summarized, the task is not done: send it back.
