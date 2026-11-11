# 04_agent_query.R
# Agent with REST Tool Call
# Tim Fraser
# Launch the API, then run:
# Rscript 12_end/04_agent_query.R

# 0. SETUP ###################################

library(httr2)
library(jsonlite)

# 1. CONFIG ###################################

if (file.exists("12_end/.env")) readRenviron("12_end/.env")

ENDPOINT_URL = trimws(Sys.getenv("API_PUBLIC_URL", unset = "http://localhost:8000"))
ENDPOINT_URL = sub("/$", "", ENDPOINT_URL)
# Cloud (free Gemini tier) by default. For local Ollama, set
# LLM_BASE_URL=http://localhost:11434/v1 and LLM_MODEL=granite4:3b
LLM_BASE_URL = Sys.getenv("LLM_BASE_URL", unset = "https://generativelanguage.googleapis.com/v1beta/openai")
LLM_MODEL = Sys.getenv("LLM_MODEL", unset = "gemini-flash-lite-latest")
GEMINI_API_KEY = Sys.getenv("GEMINI_API_KEY", unset = "")

# The free tier may use your prompts to improve Google's products, so send only public or made-up data.
is_local = grepl("^http://(localhost|127[.]0[.]0[.]1)", LLM_BASE_URL)
if (!is_local && !nzchar(trimws(GEMINI_API_KEY))) {
  stop("Set GEMINI_API_KEY in your environment or .env file before running this script.")
}

# 2. DEFINE TOOL FUNCTION ###################################

predict_vehicle_count = function(day_of_week, hours_of_day) {
  hours = as.integer(hours_of_day)
  hours = hours[!is.na(hours) & hours >= 0 & hours <= 23]
  if (length(hours) == 0) stop("hours_of_day must contain at least one integer between 0 and 23.")

  preds = lapply(hours, function(h) {
    resp = request(ENDPOINT_URL) |>
      req_url_path_append("predict") |>
      req_url_query(
        day_of_week = day_of_week,
        hour_of_day = h
      ) |>
      req_perform() |>
      resp_body_json()
    list(hour_of_day = h, predicted_vehicle_count = as.numeric(resp$predicted_vehicle_count[[1]]))
  })

  list(
    day_of_week = as.integer(day_of_week),
    unit = "vehicles_observed_in_one_minute",
    interval = "1m_t1",
    note = "Each prediction is for one representative minute within that hour and day of week.",
    predictions = preds
  )
}

# 3. CHAT COMPLETIONS HELPERS ###################################

chat_once = function(base_url, api_key, model, messages, tools = NULL) {
  url = paste0(sub("/$", "", base_url), "/chat/completions")
  body = list(model = model, messages = messages)
  if (!is.null(tools) && length(tools) > 0L) body$tools = tools
  key = if (grepl("^http://(localhost|127[.]0[.]0[.]1)", base_url)) "ollama" else trimws(api_key)

  req = httr2::request(url) |>
    httr2::req_headers("Content-Type" = "application/json") |>
    httr2::req_headers(Authorization = paste("Bearer", key)) |>
    httr2::req_body_json(body) |>
    httr2::req_timeout(120) |>
    httr2::req_retry(max_tries = 3, is_transient = function(r) httr2::resp_status(r) %in% c(429, 500, 503))

  resp = httr2::req_perform(req)
  data = httr2::resp_body_json(resp, simplifyVector = FALSE, simplifyDataFrame = FALSE)

  msg = if (length(data$choices) == 0L) list() else data$choices[[1]]$message
  content = if (is.null(msg$content)) "" else as.character(msg$content)

  list(content = trimws(paste(content, collapse = "")), message = msg, raw = data)
}

parse_function_arguments = function(raw) {
  if (is.null(raw)) return(list())
  if (is.list(raw) && !is.character(raw)) return(raw)
  if (!is.character(raw)) return(list())

  s = trimws(raw)
  if (!nzchar(s)) return(list())

  parsed = tryCatch(jsonlite::fromJSON(s, simplifyVector = FALSE), error = function(e) list())
  if (is.list(parsed)) parsed else list()
}

build_tool_message = function(tool_call) {
  fn_obj = tool_call[["function"]]
  fn = if (is.null(fn_obj$name)) "" else fn_obj$name
  args = parse_function_arguments(fn_obj$arguments)
  day_of_week = as.integer(args$day_of_week)
  hours_of_day = as.integer(unlist(args$hours_of_day))

  if (identical(fn, "predict_vehicle_count") && !is.na(day_of_week) && length(hours_of_day) > 0L) {
    pred = predict_vehicle_count(day_of_week = day_of_week, hours_of_day = hours_of_day)
    tool_content = jsonlite::toJSON(
      pred,
      auto_unbox = TRUE
    )
  } else {
    tool_content = jsonlite::toJSON(list(error = "Invalid tool call or arguments"), auto_unbox = TRUE)
  }

  tool_message = list(role = "tool", content = tool_content)
  if (!is.null(tool_call$id)) tool_message$tool_call_id = tool_call$id
  if (nzchar(fn)) {
    tool_message$name = fn
  }
  tool_message
}

# 4. DEFINE TOOL METADATA ###################################

tool_predict_vehicle_count = list(
  type = "function",
  "function" = list(
    name        = "predict_vehicle_count",
    description = paste(
      "Predict Brussels vehicle count for a specific day of week and vector of hours.",
      "Returns one estimated vehicle count per requested hour.",
      "Each value is for one representative minute (1m/t1 interval) within that hour and day of week."
    ),
    parameters  = list(
      type     = "object",
      required = list("day_of_week", "hours_of_day"),
      properties = list(
        day_of_week = list(type = "integer", description = "Day of week (1=Monday, ..., 7=Sunday)"),
        hours_of_day = list(
          type = "array",
          description = "Vector of hours to predict (0-23), e.g. [0,1,2,...,23].",
          items = list(type = "integer")
        )
      )
    )
  )
)

# 5. RUN TOOL-CALLING LOOP ###################################

messages = list(
  list(
    role = "system",
    content = paste(
      "You are a Brussels traffic assistant.",
      "When prediction data is needed, call predict_vehicle_count with day_of_week and hours_of_day vector.",
      "Always state units clearly: vehicles observed in one representative minute (1m/t1 interval)",
      "within the requested hour and day of week."
    )
  ),
  list(role = "user", content = "Predict Brussels vehicle count for Monday for every hour (0 through 23).")
)

tools = list(tool_predict_vehicle_count)
chat_result = chat_once(
  base_url = LLM_BASE_URL,
  api_key = GEMINI_API_KEY,
  model = LLM_MODEL,
  messages = messages,
  tools = tools
)

assistant_msg = chat_result$message
messages[[length(messages) + 1L]] = list(
  role = "assistant",
  content = if (is.null(assistant_msg$content)) "" else assistant_msg$content,
  tool_calls = assistant_msg$tool_calls
)

tool_calls = if (is.null(assistant_msg$tool_calls)) list() else assistant_msg$tool_calls
if (length(tool_calls) > 0L) {
  # Keep this tutorial simple: execute the first requested tool call.
  messages[[length(messages) + 1L]] = build_tool_message(tool_calls[[1]])
}

final_result = chat_once(
  base_url = LLM_BASE_URL,
  api_key = GEMINI_API_KEY,
  model = LLM_MODEL,
  messages = messages,
  tools = tools
)

cat("Agent result:", final_result$content, "\n")

# 6. VERIFY ###################################

direct = predict_vehicle_count(day_of_week = 1, hours_of_day = 0:23)
cat("Direct API call predictions returned:", length(direct$predictions), "\n")
cat("Sample one-minute vehicle count:", direct$predictions[[9]]$predicted_vehicle_count, "(1m/t1 at Monday 08:00)\n")
cat("Tool calls used:", length(tool_calls), "\n")
