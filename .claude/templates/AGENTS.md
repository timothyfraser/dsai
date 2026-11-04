# AGENTS.md: <tool name>

Read before doing anything: `SPEC.md` (what the tool is) and `CONTRACT.yaml` (what is being done).
For Codex, Cursor, Copilot, Gemini and any agent that reads AGENTS.md. Claude Code reads `CLAUDE.md`;
keep the two in step.

## How work happens here
- **One task at a time.** Nothing gets built that is not a task in `CONTRACT.yaml`. No task? Propose one
  and wait for a human to agree.
- Check the task out before starting; check it in (`status: done` + a one-line `result`) in the same
  commit as the work. Write only inside the task's `owns` paths.
- **Verify, don't claim.** Run the task's `definition_of_done` and quote what it printed. If it failed,
  the task is not done. Say so.
- Keep each change small enough for a human to read the whole diff.

## Logic comes first
- State the rule in words (SPEC section 4) before writing code for it.
- Write the logic as a plain function first; wrap it in an API route and a page only after its test passes.
- Every function gets a test against a known answer (a recorded response, a stub reply, a known query result or a hand calculation) and a
  degenerate case (empty input, one item, missing values).
- Never invent data and present it as real. Test data lives in `data/` with a codebook.
- Say which assumptions the logic needs (types, ranges, non-empty input) and how the tool checks them.
- The page never holds a key; the API does. Anything named `VITE_` is public.
- If you are unsure a rule is right, say so and show the source. Do not guess quietly.

## Hard rules
- Never write a password, token or API key into a file, commit, log or chat. Secrets live in `.env`
  (gitignored) or your deploy host's secret store.
- Stage explicit paths: `git add <files>`, never `git add -A` or `git add .`.
- Do not add a dependency, framework or feature the SPEC does not ask for.

## Commands
- Run locally: `<./testme.sh or Rscript testme.R>`
- Test: `<pytest or Rscript -e "testthat::test_dir('tests')">`
- Deploy: `<./deployme.sh or Rscript deployme.R>`
