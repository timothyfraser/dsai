# mcp-server — the Push 4 scaffold

Two doors onto one tool layer. The tools live in the course's own MCP server
(`TOOLS` and `run_tool()`); the MCP server is one door onto them over HTTP, and
a new command-line file is a second door onto the same `run_tool()`.

## What is the course's (copied unchanged)

These two folders are exact copies of the course files, byte for byte, with
every comment kept:

| Folder | Course source |
|---|---|
| [`mcp_plumber/`](mcp_plumber/) | [`dsai/08_function_calling/mcp_plumber/`](https://github.com/timothyfraser/dsai/tree/92b59abe5694f953e31d3d94985a13e7ef7bc03f/08_function_calling/mcp_plumber) — `plumber.R`, `testme.R`, `deployme.R`, `runme.R`, `pingme.sh`, `README.md`, `manifest.json` |
| [`mcp_fastapi/`](mcp_fastapi/) | [`dsai/08_function_calling/mcp_fastapi/`](https://github.com/timothyfraser/dsai/tree/92b59abe5694f953e31d3d94985a13e7ef7bc03f/08_function_calling/mcp_fastapi) — `server.py`, `testme.py`, `deployme.py`, `runme.py`, `requirements.txt`, `README.md`, `manifest.json` |

Read each folder's own `README.md` first: it explains the server. The one edit
your team makes in these folders is adding your tool to `TOOLS` and
`run_tool()` in your copy of `plumber.R` (or `server.py`), in the same style
(`CONTRACT.yaml` T1).

## What is new for the push

| File | What it is |
|---|---|
| `mcp_plumber/cli.R`, `mcp_fastapi/cli.py` | **New.** The command-line door. It loads the course's server file as is and calls its `run_tool()`; `list` prints the tool names, `call` prints exactly what the MCP server puts in its text block. |
| `check.sh` | **New.** Starts the course's server the way its README does, and prints the eight waypoints W1-W8 as PASS, FAIL or SKIP. |
| `SPEC.md`, `CONTRACT.yaml` | **New.** Your team's spec and the four tasks. |
| `SKILL.template.md`, `docs/log-entry.md` | **New.** Templates for the skill and the log entry. |
| `check-args.json` | **New.** Example arguments for each tool; add one for yours. |
| `.env.example`, `.gitignore`, `data/` | **New.** Key names only (never values), ignore rules, and local copies of `mtcars` and `iris`. |

## Run it

From this folder:

```bash
bash check.sh --lang r        # R: mcp_plumber/
bash check.sh --lang python   # Python: mcp_fastapi/
```

The CLI door on its own:

```bash
Rscript mcp_plumber/cli.R call summarize_dataset --args '{"dataset_name":"iris"}'
python mcp_fastapi/cli.py call summarize_dataset --args '{"dataset_name":"iris"}'
```

## Two notes

- **R before 4.4.** `plumber.R` uses the `%||%` operator, which is part of base
  R only from R 4.4. On an older R, `cli.R` and `check.sh` define it before
  loading `plumber.R`, so the course file never changes. If you start the server
  by hand on an older R, define it in the same command:
  `Rscript -e "\`%||%\` <- function(x, y) if (is.null(x)) y else x; plumber::plumb('plumber.R')$run(port=8000)"`.
- **Python needs the internet at start-up.** `server.py` downloads `mtcars` and
  `iris` from `vincentarelbundock.github.io` the moment it is imported. With no
  internet, or behind a proxy that blocks that host, neither the server nor
  `cli.py` can start: `cli.py` prints an error naming the host, and `check.sh`
  marks W1-W3 SKIP with that reason instead of FAIL.
