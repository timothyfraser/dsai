# cli.R
# Command-line door onto plumber.R's tools (R)
# Pairs with mcp_fastapi/cli.py
#
# NEW for the push (not part of the 2026 course files): a command-line door
# onto the same run_tool() the MCP server uses.
#
# What this file is:
#   plumber.R already holds the tools: TOOLS (what the LLM sees) and run_tool()
#   (the actual R code). The MCP server is one door onto them, over HTTP.
#   This script is a second door onto the SAME tools, from the terminal.
#   It does not copy or change any tool code: it source()s plumber.R and calls
#   the run_tool() it finds there. So if you add a tool to plumber.R, this
#   door gets it for free.
#
# How to run (from this folder):
#   Rscript cli.R list
#   Rscript cli.R call summarize_dataset --args '{"dataset_name":"iris"}'
#
# What it prints:
#   list — one tool name per line, straight from TOOLS
#   call — exactly the text run_tool() returns; the same text the MCP server
#          puts in its tools/call content block, byte for byte
#
# Packages:
#   Only what plumber.R itself loads (plumber, dplyr, jsonlite, tidyr).
#   The command-line arguments are read with base R's commandArgs().

# ── R < 4.4 shim ─────────────────────────────────────────────

# plumber.R uses the `%||%` operator ("this, or else that if it is NULL").
# It is part of base R only from R 4.4. On an older R we define it here,
# before sourcing, so plumber.R itself never has to change.
if (!exists("%||%", mode = "function")) {
  `%||%` <- function(x, y) if (is.null(x)) y else x
}

# ── Load the tools from plumber.R ────────────────────────────

# Find plumber.R next to this script, wherever you run it from.
script_arg <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
here <- if (length(script_arg) > 0) dirname(sub("^--file=", "", script_arg[1])) else "."

# source() into its own environment. The #* endpoint functions in plumber.R
# are anonymous (nobody gives them a name), so sourcing only defines TOOLS,
# run_tool(), empty_json_object() and handle_jsonrpc(). No server starts:
# a server only starts when plumber::plumb(...)$run() is called.
tools_env <- new.env()
suppressPackageStartupMessages(
  source(file.path(here, "plumber.R"), local = tools_env)
)

# ── Read the command line ────────────────────────────────────

args <- commandArgs(trailingOnly = TRUE)

usage <- function() {
  cat("Usage:\n",
      "  Rscript cli.R list\n",
      "  Rscript cli.R call <tool> --args '<json>'\n", sep = "")
}

if (length(args) == 0) {
  usage()
  quit(status = 2)
}

command <- args[1]

# ── list: the tool names, one per line ───────────────────────

if (command == "list") {
  for (tool in tools_env$TOOLS) cat(tool$name, "\n", sep = "")
  quit(status = 0)
}

# ── call: run one tool, print what run_tool() returns ────────

if (command == "call") {
  if (length(args) < 2) {
    usage()
    quit(status = 2)
  }
  tool_name <- args[2]

  # --args '<json>' is optional; no args means an empty argument list.
  # simplifyVector = FALSE parses the JSON the same way handle_jsonrpc() does,
  # so run_tool() receives the same R list it gets over MCP.
  tool_args <- list()
  flag <- which(args == "--args")
  if (length(flag) > 0) {
    if (flag[1] == length(args)) {
      cat("--args needs a JSON object, e.g. --args '{\"dataset_name\":\"iris\"}'\n", file = stderr())
      quit(status = 2)
    }
    tool_args <- jsonlite::fromJSON(args[flag[1] + 1], simplifyVector = FALSE)
  }

  # Errors from run_tool() (unknown tool, unknown dataset) go to stderr with a
  # non-zero exit, the way the MCP server returns them as a JSON-RPC error.
  out <- tryCatch(
    tools_env$run_tool(tool_name, tool_args),
    error = function(e) {
      cat("Error:", conditionMessage(e), "\n", file = stderr())
      quit(status = 1)
    }
  )

  # cat() with no trailing newline: the bytes match the MCP text block exactly.
  cat(as.character(out))
  quit(status = 0)
}

usage()
quit(status = 2)
