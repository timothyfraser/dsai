#' @name 03_voice_note_to_work_order.R
#' @title From a voice note to a filed work order: transcribe, extract, validate, write
#' @description
#' Course kit, module 18
#' Topic: Audio models in a real workflow
#'
#' A field technician records a voice note. This script:
#' 1. transcribes it (speech-to-text, local),
#' 2. asks a local model to fill a work-order form, shaped by a JSON schema,
#' 3. checks the answer against that schema in plain code,
#' 4. writes one row to a CSV file, marked "draft" until a person confirms it.
#'
#' Stub mode, for testing with no model installed:
#' AUDIO_STUB=1 skips Whisper and uses a fixed transcript.
#' LLM_STUB=1 skips Ollama and uses a fixed JSON answer.

# If you haven't already, install these packages...
# install.packages(c("httr2", "jsonlite", "reticulate"))
# reticulate::py_install(c("faster-whisper", "av<19"))  # av 19 breaks faster-whisper 1.2.1
# and pull the model in Ollama: ollama pull granite4:3b

# 0. SETUP ###################################

## 0.1 Load Packages #################################

library(httr2) # for HTTP requests to Ollama
library(jsonlite) # for JSON handling

## 0.2 Settings ###################################

# Run this script from the top of the course repo, so the audio path resolves.
AUDIO_PATH = Sys.getenv("AUDIO_PATH", "06_agents/06_jfk_short.wav")
WORK_ORDERS_CSV = Sys.getenv("WORK_ORDERS_CSV", "work_orders.csv")
OLLAMA_URL = Sys.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
MODEL = Sys.getenv("MODEL", "granite4:3b")
AUDIO_STUB = Sys.getenv("AUDIO_STUB") == "1"
LLM_STUB = Sys.getenv("LLM_STUB") == "1"

## 0.3 The contract: a JSON schema for one work order ###################################

# A JSON schema is a description of the shape an answer must have:
# which fields, what type each one is, and which values are allowed.
# The model sees this schema. Your code checks the answer against it. Both matter.
WORK_ORDER_SCHEMA = list(
  type = "object",
  properties = list(
    asset = list(type = "string"), # the thing that needs work, e.g. "Pump 3"
    location = list(type = "string"), # where it is
    problem = list(type = "string"), # what is wrong, in one sentence
    priority = list(type = "string", enum = c("low", "medium", "high")),
    safety_hazard = list(type = "boolean"), # is anyone at risk right now?
    action_requested = list(type = "string") # what the technician asked for
  ),
  required = c("asset", "location", "problem", "priority", "safety_hazard", "action_requested")
)

# The fixed answers used in stub mode. They are test values, not real model output.
STUB_TRANSCRIPT = paste0(
  "This is the night operator at the north lift station. Pump three is leaking oil ",
  "from the seal, and there is a slick on the floor by the stairs. I would call it high ",
  "priority. Please send a mechanic to replace the seal before the next shift."
)
STUB_JSON = paste0(
  '{"asset": "Pump 3", "location": "North lift station", ',
  '"problem": "Oil is leaking from the pump seal onto the floor", "priority": "high", ',
  '"safety_hazard": true, "action_requested": "Send a mechanic to replace the seal before the next shift"}'
)
# The check script swaps in a broken answer here, to prove the validator rejects it.
STUB_JSON = Sys.getenv("LLM_STUB_JSON", STUB_JSON)


# 1. TRANSCRIBE THE VOICE NOTE #####################################

transcribe = function(audio_path) {
  if (!file.exists(audio_path)) { stop(paste0("Audio file not found: ", audio_path)) }
  if (AUDIO_STUB) { return(STUB_TRANSCRIPT) }
  # Same call as 01_transcribe.R, kept inline so this script stands alone.
  fw = reticulate::import("faster_whisper")
  model = fw$WhisperModel("base.en", device = "cpu", compute_type = "int8")
  result = model$transcribe(audio_path, beam_size = 5L)
  segments = reticulate::iterate(result[[1]])
  paste(trimws(sapply(segments, function(s) s$text)), collapse = " ")
}


# 2. ASK A MODEL TO FILL THE FORM #####################################

extract_work_order = function(transcript) {
  if (LLM_STUB) { return(STUB_JSON) }

  prompt = paste0(
    "You file maintenance work orders. Read the technician's voice note below and fill ",
    "every field of the work order. Use only facts in the note. If the note does not say ",
    "how urgent it is, use \"medium\". Return only JSON.\n\n",
    "Voice note: ", transcript
  )
  body = list(
    model = MODEL,
    messages = list(list(role = "user", content = prompt)),
    # Passing the schema as "format" asks Ollama to only produce JSON of this shape.
    format = WORK_ORDER_SCHEMA,
    stream = FALSE,
    options = list(temperature = 0) # the same note should give the same form
  )
  resp = request(OLLAMA_URL) |>
    req_body_json(body, auto_unbox = TRUE) |>
    req_perform()
  resp_body_json(resp)$message$content
}


# 3. CHECK THE ANSWER AGAINST THE SCHEMA #####################################

validate_work_order = function(record) {
  # Return a vector of problems. An empty vector means the record fits the schema.
  problems = c()
  for (field in WORK_ORDER_SCHEMA$required) {
    if (is.null(record[[field]])) { problems = c(problems, paste0("missing field: ", field)); next }
    rule = WORK_ORDER_SCHEMA$properties[[field]]
    value = record[[field]]
    ok_type = if (rule$type == "string") is.character(value) && length(value) == 1 else is.logical(value) && length(value) == 1
    if (!ok_type) {
      problems = c(problems, paste0(field, " should be a ", rule$type))
    } else if (rule$type == "string" && trimws(value) == "") {
      problems = c(problems, paste0(field, " is empty"))
    } else if (!is.null(rule$enum) && !(value %in% rule$enum)) {
      problems = c(problems, paste0(field, " must be one of ", paste(rule$enum, collapse = ", "), ", got ", value))
    }
  }
  # Fields the schema does not name are a sign the model drifted from the contract.
  extra = setdiff(names(record), names(WORK_ORDER_SCHEMA$properties))
  if (length(extra) > 0) { problems = c(problems, paste0("unexpected field: ", extra)) }
  return(problems)
}


# 4. WRITE ONE ROW TO THE CSV #####################################

write_row = function(record, transcript, audio_path, csv_path = WORK_ORDERS_CSV) {
  row = data.frame(
    recorded_at = format(Sys.time(), "%Y-%m-%dT%H:%M:%S%z"),
    audio_file = basename(audio_path),
    transcript = transcript,
    record[WORK_ORDER_SCHEMA$required],
    # A machine filled this form. It stays a draft until a person reads it and confirms.
    status = "draft",
    stringsAsFactors = FALSE
  )
  # Booleans are written the same way in both languages: "True" / "False".
  row$safety_hazard = ifelse(row$safety_hazard, "True", "False")
  new_file = !file.exists(csv_path)
  write.table(row, csv_path, sep = ",", row.names = FALSE, col.names = new_file,
              append = !new_file, qmethod = "double", fileEncoding = "UTF-8")
  return(row)
}


# 5. RUN THE WHOLE PIPELINE #####################################

transcript = transcribe(AUDIO_PATH)
cat("Transcript:\n", transcript, "\n")

answer = extract_work_order(transcript)
record = fromJSON(answer) # fails loudly if the model returned something that is not JSON

problems = validate_work_order(record)
if (length(problems) > 0) {
  # Do not file a record that breaks the contract. Show why, and stop.
  stop(paste0("Work order rejected: ", paste(problems, collapse = "; ")))
}

row = write_row(record, transcript, AUDIO_PATH)
cat("\nFiled a draft work order in ", WORK_ORDERS_CSV, ":\n")
str(as.list(row))
