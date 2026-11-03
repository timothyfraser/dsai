# cli.py
# Command-line door onto server.py's tools (Python)
# Pairs with mcp_plumber/cli.R
#
# NEW for the push (not part of the 2026 course files): a command-line door
# onto the same run_tool() the MCP server uses.
#
# What this file is:
#   server.py already holds the tools: TOOLS (what the LLM sees) and run_tool()
#   (the actual Python code). The MCP server is one door onto them, over HTTP.
#   This script is a second door onto the SAME tools, from the terminal.
#   It does not copy or change any tool code: it imports server and calls the
#   run_tool() it finds there. So if you add a tool to server.py, this door
#   gets it for free.
#
# How to run (from this folder):
#   python cli.py list
#   python cli.py call summarize_dataset --args '{"dataset_name":"iris"}'
#
# What it prints:
#   list — one tool name per line, straight from TOOLS
#   call — exactly the text run_tool() returns; the same text the MCP server
#          puts in its tools/call content block, byte for byte
#
# Heads-up — server.py downloads its datasets when it is imported:
#   server.py reads mtcars and iris from vincentarelbundock.github.io the
#   moment it loads. With no internet (or behind a proxy that blocks that
#   host), the import fails and this script says so and stops. That is
#   server.py's behaviour, not a CLI bug, and it is left exactly as written.
#
# Packages:
#   Only what server.py itself needs (fastapi, pandas). Arguments use argparse.

import argparse
import json
import os
import sys

# ── Load the tools from server.py ────────────────────────────

# Find server.py next to this script, wherever you run it from.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DATA_HOST = "vincentarelbundock.github.io"

try:
    import server  # defines TOOLS and run_tool(); no server starts (uvicorn does that)
except Exception as e:
    print(
        f"Error: could not load server.py. It downloads mtcars and iris from "
        f"{DATA_HOST} when it is imported, so it needs that host to be reachable. "
        f"Underlying error: {type(e).__name__}: {e}",
        file=sys.stderr,
    )
    sys.exit(3)

# ── Read the command line ────────────────────────────────────

parser = argparse.ArgumentParser(description="Command-line door onto server.py's tools.")
sub = parser.add_subparsers(dest="command", required=True)
sub.add_parser("list", help="print the tool names, one per line")
call = sub.add_parser("call", help="run one tool and print what run_tool() returns")
call.add_argument("tool", help="the tool name, as shown by `list`")
call.add_argument("--args", default="{}", help="the tool's arguments as a JSON object")
opts = parser.parse_args()

# ── list: the tool names, one per line ───────────────────────

if opts.command == "list":
    for tool in server.TOOLS:
        print(tool["name"])
    sys.exit(0)

# ── call: run one tool, print what run_tool() returns ────────

# Errors from run_tool() (unknown tool, unknown dataset) go to stderr with a
# non-zero exit, the way the MCP server returns them as a JSON-RPC error.
try:
    out = server.run_tool(opts.tool, json.loads(opts.args))
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)

# No trailing newline: the bytes match the MCP text block exactly.
sys.stdout.write(out)
