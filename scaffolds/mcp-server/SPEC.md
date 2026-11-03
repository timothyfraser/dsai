# SPEC — our MCP server (Push 4)

Fill in every `FILL-IN` line before you write code. `CONTRACT.yaml` turns this
spec into four tasks; `check.sh` proves the waypoints.

## Need
FILL-IN: who needs this, and what they cannot do today without it (one sentence).

## Goal
FILL-IN: what an agent can do once both doors are live (one sentence).

## Our tool
- Name: FILL-IN (snake_case; added beside `summarize_dataset`)
- Reads: FILL-IN (the data source — your Push 3 API is a fine one)
- Inputs: FILL-IN (each argument, its type, and whether it is required)
- Returns: FILL-IN (the shape of the text block)
- Use when: FILL-IN (the sentence that goes in its `description`)

## Acceptance test
FILL-IN: the one argument set in `check-args.json` that must work, and what the
text block should contain when it does.

## Fixed (do not change)
- The course's MCP server files (`mcp_plumber/`, `mcp_fastapi/`) start as exact
  copies. The one edit you make is adding your tool to `TOOLS` and `run_tool()`
  in your own copy of `plumber.R` (or `server.py`), in the same style.
- One tool layer: `run_tool()` is the only place with logic.
- Two doors: the MCP door (`plumber.R` / `server.py`) and the CLI door
  (`cli.R` / `cli.py`, new for the push). `call` prints the MCP text block byte for byte.
- At least two tools: `summarize_dataset` and yours.
- No key in git: `.env` stays ignored; `.env.example` holds names only.
