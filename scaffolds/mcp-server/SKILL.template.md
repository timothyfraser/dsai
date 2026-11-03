---
name: TODO-your-skill-name
description: TODO one paragraph (at most 1,024 characters) telling an agent when to reach for this server's tools - summarize_dataset for quick numeric summaries of mtcars or iris, and TODO_your_tool for TODO. Name the words a person would actually type.
---

# TODO: skill title

Copy this file to `SKILL.md`, replace every TODO, and rename `TODO_your_tool`
to your tool's real name everywhere. check.sh W6 fails while any TODO is left.

## Use when

- Use `summarize_dataset` when someone asks for the mean, sd, min or max of the
  numeric columns in `mtcars` or `iris`.
- Use `TODO_your_tool` when TODO.

## Do not use when

- TODO: the request your tools cannot answer, and what to do instead.

## How to call

- MCP: `tools/call` with `{"name": "summarize_dataset", "arguments": {"dataset_name": "iris"}}`
- CLI: `Rscript mcp_plumber/cli.R call summarize_dataset --args '{"dataset_name":"iris"}'`
  or `python mcp_fastapi/cli.py call summarize_dataset --args '{"dataset_name":"iris"}'`

## Reading the result

TODO: what the text block contains and how an agent should report it.
