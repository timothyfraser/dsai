# R/ollama_chat.R
# Single-round chat-completions call (OpenAI-compatible) via httr2
# Default: Google's free Gemini tier. Local path: Ollama at http://localhost:11434/v1
# Tim Fraser

llm_chat_once = function(
  base_url,
  api_key,
  model,
  messages,
  tools,
  max_output_tokens = NULL
) {
  url = paste0(sub("/$", "", base_url), "/chat/completions")
  body = list(
    model = model,
    messages = messages,
    tools = tools
  )
  if (!is.null(max_output_tokens)) {
    body$max_tokens = as.integer(max_output_tokens)
  }

  # The local path does not need a real key; Ollama ignores it.
  ak = trimws(as.character(api_key %||% ""))
  if (!nzchar(ak)) {
    ak = "ollama"
  }

  resp = httr2::request(url) |>
    httr2::req_headers(Authorization = paste("Bearer", ak)) |>
    httr2::req_body_json(body, auto_unbox = TRUE, null = "null") |>
    httr2::req_retry(
      max_tries = 3,
      is_transient = function(r) httr2::resp_status(r) %in% c(429, 500, 503),
      backoff = function(i) 2^i
    ) |>
    httr2::req_timeout(120) |>
    httr2::req_perform()

  data = httr2::resp_body_json(resp, simplifyVector = FALSE, simplifyDataFrame = FALSE)
  msg = data$choices[[1L]]$message %||% list()
  # Keep tool_calls as an array on the way back; an empty content must be "" not null.
  if (is.null(msg$content)) {
    msg$content = ""
  }
  content = msg$content
  if (!is.character(content)) {
    content = as.character(content)
  }
  content = trimws(paste(content, collapse = ""))
  list(content = content, message = msg, raw = data)
}
