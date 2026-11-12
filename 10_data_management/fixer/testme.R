#' @name testme.R
#' @title Smoke test one chat request from the fixer folder (no tools)
#' @author Prof. Tim Fraser
#' @description
#' One POST to **`/chat/completions`** with a tiny user message — verifies **`GEMINI_API_KEY`**,
#' **`LLM_BASE_URL`**, and **`LLM_MODEL`** without tool calling or **`max_tokens`**
#' (helps isolate HTTP 400s from the full **`fixer_csv.R`** loop).

# 0. SETUP ###################################

resolve_fixer_root = function() {
  r = Sys.getenv("FIXER_ROOT", unset = "")
  if (nzchar(r) && dir.exists(r)) {
    return(normalizePath(r, winslash = "/", mustWork = TRUE))
  }
  wd = normalizePath(getwd(), winslash = "/", mustWork = TRUE)
  if (file.exists(file.path(wd, "functions.R"))) {
    return(wd)
  }
  cand = file.path(wd, "10_data_management", "fixer")
  if (file.exists(file.path(cand, "functions.R"))) {
    return(normalizePath(cand, winslash = "/", mustWork = TRUE))
  }
  stop("Run from fixer/, dsai repo root, or set FIXER_ROOT.")
}

FIXER_ROOT = resolve_fixer_root()
env_path = file.path(FIXER_ROOT, ".env")
if (file.exists(env_path)) {
  readRenviron(env_path)
}

LLM_BASE_URL = trimws(Sys.getenv("LLM_BASE_URL", unset = "https://generativelanguage.googleapis.com/v1beta/openai"))
GEMINI_API_KEY = trimws(Sys.getenv("GEMINI_API_KEY", unset = ""))
LLM_MODEL = trimws(Sys.getenv("LLM_MODEL", unset = ""))
if (!nzchar(LLM_MODEL)) {
  LLM_MODEL = "gemini-flash-lite-latest"
}

# A local server (http://localhost...) needs no key.
is_local = startsWith(LLM_BASE_URL, "http://localhost") || startsWith(LLM_BASE_URL, "http://127.0.0.1")
if (!is_local && !nzchar(GEMINI_API_KEY)) {
  stop("Set GEMINI_API_KEY in fixer/.env (copy from .env.example).")
}

source(file.path(FIXER_ROOT, "functions.R"), local = FALSE)

# 1. MINIMAL CHAT (test query) ###################################

# Deliberately tiny: model should answer in a few tokens; no tools, no options.
messages = list(
  list(
    role = "user",
    content = "Reply with exactly one word: pong"
  )
)

cat("Test query: POST ", LLM_BASE_URL, "/chat/completions\n", sep = "")
cat("Model: ", LLM_MODEL, "\n\n", sep = "")

out = tryCatch(
  llm_chat_once(
    LLM_BASE_URL,
    GEMINI_API_KEY,
    LLM_MODEL,
    messages,
    tools = NULL,
    json = FALSE,
    max_output_tokens = NULL
  ),
  error = function(e) {
    lr = tryCatch(httr2::last_response(), error = function(e2) NULL)
    if (!is.null(lr)) {
      cat("HTTP status:", httr2::resp_status(lr), "\n")
      b = tryCatch(httr2::resp_body_string(lr), error = function(e3) "(no body)")
      cat("Response body:\n", b, "\n", sep = "")
    }
    stop(e)
  }
)

cat("Assistant content:\n", out$content, "\n\n", sep = "")
cat("Smoke test OK.\n")
