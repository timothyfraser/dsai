#' @name photo_to_record.R
#' @title Turn a photo into one checked row of a CSV, with a vision model
#' @description
#' Pairs with photo_to_record.py
#' Course kit, module 17
#'
#' Topic: Visual Language Models
#'
#' In 05_vlms_cloud.R, we asked a vision model for a JSON string
#' and hoped it came back clean. This script stops hoping.
#' It sends a photo plus a schema (a list of the fields we want, and their types),
#' then checks every field of the reply before it writes anything.
#' A reply that breaks the schema is refused, and no row is written.
#'
#' Run it from the top of the course repo, so the image path resolves:
#'   Rscript photo_to_record.R 06_agents/05_coffeeshop_small.jpg records.csv
#'
#' No model handy? Set VLM_STUB=1 and the script uses a fixed reply instead.
#'   VLM_STUB=1 Rscript photo_to_record.R 06_agents/05_coffeeshop_small.jpg records.csv
#' VLM_STUB=guess and VLM_STUB=mismatch send two broken replies, to show the refusal.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

library(httr2) # for HTTP requests
library(jsonlite) # for reading the schema and parsing the reply

## 0.2 Configuration #################################

# The photo to read, and the CSV to add a row to.
# You can pass both on the command line instead.
args = commandArgs(trailingOnly = TRUE)
IMAGE_PATH = if (length(args) >= 1) args[1] else "06_agents/05_coffeeshop_small.jpg"
CSV_PATH = if (length(args) >= 2) args[2] else "records.csv"

# The schema sits next to this script. Edit it to ask for your own fields.
script_dir = function() {
  file_arg = grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
  if (length(file_arg) == 0) { return(getwd()) }
  dirname(normalizePath(sub("^--file=", "", file_arg[1])))
}
SCHEMA_PATH = Sys.getenv("RECORD_SCHEMA", file.path(script_dir(), "record_schema.json"))

# Local by default (llava through Ollama). Set VLM_CLOUD=1 to use Ollama Cloud.
USE_CLOUD = Sys.getenv("VLM_CLOUD") == "1"
MODEL = Sys.getenv("VLM_MODEL", if (USE_CLOUD) "gemma3:4b" else "llava")
STUB = Sys.getenv("VLM_STUB")

if (!file.exists(IMAGE_PATH)) { stop(paste0("Image not found: ", IMAGE_PATH)) }

# simplifyVector = FALSE keeps each field as a list, the same shape as the JSON file
schema = fromJSON(SCHEMA_PATH, simplifyVector = FALSE)


# 1. WRITE THE PROMPT FROM THE SCHEMA #######################

# We never type the field list twice. The prompt is built from the schema,
# so the model is asked for exactly the fields the checker will check.
build_prompt = function(schema){
  lines = c(
    "Look at this photo and fill in a JSON object with these fields.",
    "Output only the JSON object. Do not include any other text.",
    "Do not include any extra formatting like '```json' in your response.",
    "If you cannot see something clearly, write \"unknown\". Do not guess.",
    ""
  )
  for (field in schema$fields) {
    if (field$type == "integer") {
      kind = paste0("a whole number", if (isTRUE(field$allow_unknown)) ", or \"unknown\"" else "")
    } else if (field$type == "choice") {
      kind = paste0("one of: ", paste0("\"", unlist(field$choices), "\"", collapse = ", "))
    } else {
      kind = "a short text"
    }
    lines = c(lines, paste0("\"", field$name, "\": ", kind, ". (", field$description, ")"))
  }
  paste(lines, collapse = "\n")
}

PROMPT = build_prompt(schema)
cat("Prompt sent with the photo:\n", PROMPT, "\n\n", sep = "")


# 2. ASK THE MODEL #################################

# Same request as 05_vlms_local.R and 05_vlms_cloud.R:
# the image goes in as base64 text, next to the prompt.
query = function(IMAGE_PATH, PROMPT, MODEL){

  # Read the image and base64-encode it for the API
  raw_bytes = readBin(IMAGE_PATH, "raw", file.info(IMAGE_PATH)$size)
  image_base64 = jsonlite::base64_enc(raw_bytes)

  # Stub mode: no model is called. These fixed replies let you test the checks.
  if (STUB == "1") {
    return(paste0('{"n_people": 9, "n_sitting": 6, "n_standing": 3, "exit_sign_visible": "unknown", ',
                  '"walkway_blocked": "no", "confidence": "medium", ',
                  '"notes": "People at the back are partly hidden."}'))
  }
  if (STUB == "guess") {
    return('```json\n{"n_people": "about 9", "n_sitting": 6, "n_standing": 3}\n```')
  }
  if (STUB == "mismatch") {
    return(paste0('{"n_people": 12, "n_sitting": 6, "n_standing": 3, "exit_sign_visible": "no", ',
                  '"walkway_blocked": "no", "confidence": "high", "notes": "unknown"}'))
  }

  body = list(
    model = MODEL,
    messages = list(
      list(role = "user", content = PROMPT, images = list(image_base64))
    ),
    stream = FALSE
  )

  if (USE_CLOUD) {
    if (file.exists(".env")) { readRenviron(".env") }
    OLLAMA_API_KEY = Sys.getenv("OLLAMA_API_KEY")
    if (OLLAMA_API_KEY == "") { stop("OLLAMA_API_KEY not found. Put it in .env for the cloud.") }
    req = request("https://ollama.com/api/chat") |>
      req_headers("Authorization" = paste0("Bearer ", OLLAMA_API_KEY))
  } else {
    req = request("http://127.0.0.1:11434/api/chat")
  }

  res = req |>
    req_body_json(body, auto_unbox = TRUE) |>
    req_timeout(600) |>
    req_perform()

  resp_body_json(res)$message$content
}

REPLY = query(IMAGE_PATH, PROMPT, MODEL)
cat("Raw reply:\n", REPLY, "\n\n", sep = "")


# 3. PARSE THE REPLY #################################

# Models often wrap JSON in ```json fences even when told not to.
# We strip the fences, then parse. Anything else that fails to parse is refused.
parse_reply = function(text){
  text = trimws(text)
  text = sub("^```(json)?", "", text)
  text = sub("```$", "", text)
  fromJSON(text, simplifyVector = FALSE)
}

record = tryCatch(parse_reply(REPLY), error = function(e) NULL)
if (is.null(record)) {
  cat("REFUSED: the reply is not JSON. No row written.\n")
  quit(status = 1)
}


# 4. VALIDATE AGAINST THE SCHEMA #######################

# Each field is checked by its type. A problem is a sentence, so the person
# reading the output knows exactly which field failed and why.
is_whole = function(x) { is.numeric(x) && length(x) == 1 && x == round(x) && x >= 0 }

validate = function(record, schema){
  problems = c()
  if (!is.list(record) || is.null(names(record))) { return("the reply is not a JSON object") }
  names_in_schema = sapply(schema$fields, function(f) f$name)
  for (field in schema$fields) {
    name = field$name
    if (!(name %in% names(record))) {
      problems = c(problems, paste0(name, ": missing"))
      next
    }
    value = record[[name]]
    if (isTRUE(field$allow_unknown) && identical(value, "unknown")) { next }
    if (field$type == "integer") {
      if (!is_whole(value)) {
        problems = c(problems, paste0(name, ": '", value, "' is not a whole number or \"unknown\""))
      }
    } else if (field$type == "choice") {
      if (!(is.character(value) && value %in% unlist(field$choices))) {
        problems = c(problems, paste0(name, ": '", value, "' is not one of ",
                                      paste(unlist(field$choices), collapse = ", ")))
      }
    } else if (!is.character(value)) {
      problems = c(problems, paste0(name, ": '", value, "' is not text"))
    }
  }
  for (k in setdiff(names(record), names_in_schema)) {
    problems = c(problems, paste0(k, ": not in the schema"))
  }

  # A rule the schema cannot say by itself: the parts must add up to the total.
  counts = list(record$n_people, record$n_sitting, record$n_standing)
  if (all(sapply(counts, is_whole))) {
    if (counts[[2]] + counts[[3]] != counts[[1]]) {
      problems = c(problems, paste0("counts: ", counts[[2]], " sitting + ", counts[[3]],
                                    " standing is not ", counts[[1]], " people"))
    }
  }
  problems
}

problems = validate(record, schema)
if (length(problems) > 0) {
  cat("REFUSED: the reply breaks the schema. No row written.\n")
  cat(paste0("  - ", problems, "\n"), sep = "")
  quit(status = 1)
}


# 5. WRITE THE CSV ROW #################################

# The photo and model columns come from us, not from the model.
# We write the header only when the file is new.
columns = c("photo", "model", sapply(schema$fields, function(f) f$name))
row = c(list(photo = basename(IMAGE_PATH), model = if (STUB != "") "stub" else MODEL),
        record[sapply(schema$fields, function(f) f$name)])
row = as.data.frame(lapply(row, as.character), stringsAsFactors = FALSE)[, columns]

is_new = !file.exists(CSV_PATH)
write.table(row, CSV_PATH, sep = ",", row.names = FALSE, col.names = is_new,
            append = !is_new, qmethod = "double")

cat("OK: one row written to ", CSV_PATH, "\n", sep = "")
print(row)

# An ethical system keeps the row and deletes the photo when it is done.
# Here we leave the photo alone: it is course material.
