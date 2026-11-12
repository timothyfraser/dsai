# geo_clean.R
# Standardise messy addresses with a model, then geocode them with a lookup, never with the model.
# Course kit, module 19

# Run from the folder that holds this file:  Rscript geo_clean.R
# Set LLM_STUB=1 to use the saved replies in data/stub_replies.json instead of a model.

# 0. SETUP ###################################

library(dplyr)
library(readr)
library(jsonlite)

# Use the right-hand value when the left one is missing (built into R 4.4 and later).
`%||%` = function(a, b) { if (is.null(a)) b else a }

# Work inside this script's own folder, so data/ and output/ resolve.
# (Rscript passes the file path; in an IDE, set the working directory to this folder first.)
args_all = commandArgs(trailingOnly = FALSE)
file_arg = sub("^--file=", "", args_all[grepl("^--file=", args_all)])
if (length(file_arg) == 1) { setwd(dirname(normalizePath(file_arg))) }

RAW_PATH = "data/addresses_raw.csv"
GAZETTEER_PATH = "data/gazetteer.csv"
STUB_PATH = "data/stub_replies.json"
OUT_CSV = "output/addresses_clean.csv"
CHANGES_PATH = "output/changes.jsonl"
dir.create("output", showWarnings = FALSE)

# Which model to ask. The default is Google's free Gemini tier. The free tier may use your prompts
# to improve Google's products, so send only public or made-up data.
# To use your own computer instead: LLM_BASE_URL=http://localhost:11434/v1 and LLM_MODEL=granite4:3b
# (run `ollama pull granite4:3b` first). The local path needs no key.
LLM_BASE_URL = Sys.getenv("LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai")
LLM_MODEL = Sys.getenv("LLM_MODEL", "gemini-flash-lite-latest")
GEMINI_API_KEY = Sys.getenv("GEMINI_API_KEY", "")
LLM_STUB = Sys.getenv("LLM_STUB", "") == "1"

# The model may fill these five text fields and nothing else.
FIELDS = c("house_number", "street", "unit", "city", "state")

# Below this confidence (1 = low, 2 = medium, 3 = high) we do not trust the model's fields.
MIN_CONFIDENCE = 2

# Tell the model its job, and tell it plainly that coordinates are not its job.
SYSTEM_PROMPT = paste0(
  "You standardise one US street address at a time. Reply with JSON only, with the keys ",
  "house_number, street, unit, city, state, confidence, reason. Use upper case. Write street ",
  "types and directions in their short form (ST, AVE, RD, WAY, N, S, E, W). Put an apartment ",
  "or suite in unit. confidence is 1 (low), 2 (medium) or 3 (high). reason is one short ",
  "sentence saying what you changed and why. If the text is not an address, leave ",
  "house_number and street empty and set confidence to 1. Never give a latitude, a longitude ",
  "or a zip code you were not shown."
)

# 1. LOAD DATA ###################################

raw_rows = read_csv(RAW_PATH, col_types = cols(.default = "c"))

# The gazetteer stands in for a real geocoding service: a known address goes in,
# a measured coordinate comes out. Its key is house number + street + city + state.
gazetteer = read_csv(GAZETTEER_PATH, col_types = cols(.default = "c")) %>%
  mutate(key = paste(house_number, street, city, state, sep = "|"))

cat("Loaded", nrow(raw_rows), "addresses and", nrow(gazetteer), "gazetteer entries.\n")

# 2. ASK THE MODEL ###################################

ask_model = function(row_id, address_raw) {
  # Stub mode: the saved reply for this row, so the checks run without a model.
  if (LLM_STUB) { return(fromJSON(STUB_PATH)[[row_id]]) }
  library(httr2)
  local = startsWith(LLM_BASE_URL, "http://localhost") || startsWith(LLM_BASE_URL, "http://127.0.0.1")
  if (!local && !nzchar(GEMINI_API_KEY)) {
    stop("Set GEMINI_API_KEY, or set LLM_BASE_URL to a local Ollama address.")
  }
  body = list(
    model = LLM_MODEL, temperature = 0,
    messages = list(
      list(role = "system", content = SYSTEM_PROMPT),
      list(role = "user", content = address_raw)
    )
  )
  reply = request(paste0(LLM_BASE_URL, "/chat/completions")) %>%
    req_auth_bearer_token(if (local) "ollama" else GEMINI_API_KEY) %>%
    req_body_json(body) %>%
    req_timeout(120) %>%
    req_retry(max_tries = 3, backoff = function(i) 2^i,
              is_transient = function(r) resp_status(r) %in% c(429, 500, 503)) %>%
    req_perform() %>%
    resp_body_json()
  text = trimws(reply$choices[[1]]$message$content)
  text = trimws(sub("```$", "", sub("^```(json)?", "", text)))
  fromJSON(text)
}

# 3. GUARD THE REPLY ###################################

changes = list() # one entry per changed field, written to output/changes.jsonl

log_change = function(row_id, field, old, new, reason, by) {
  changes[[length(changes) + 1]] <<- list(row_id = row_id, field = field, old = old,
                                          new = new, reason = reason, by = by)
}

guard = function(row_id, address_raw, reply) {
  # The model is not allowed to place a point on the map. Drop any coordinate it offers.
  for (key in c("lat", "lon", "latitude", "longitude", "zip")) {
    if (!is.null(reply[[key]])) {
      log_change(row_id, key, "", as.character(reply[[key]]),
                 "Dropped: coordinates and zip codes come from the geocoder, not the model.",
                 "guard")
    }
  }
  confidence = suppressWarnings(as.integer(reply$confidence))
  if (length(confidence) != 1 || is.na(confidence)) { confidence = 1L }
  reason = trimws(as.character(reply$reason %||% ""))
  if (!nzchar(reason)) { reason = "The model gave no reason." }
  fields = sapply(FIELDS, function(k) toupper(trimws(as.character(reply[[k]] %||% ""))))
  list(fields = fields, confidence = confidence, reason = reason)
}

# 4. GEOCODE WITH A LOOKUP, NOT THE MODEL ###################################

out_rows = list()
for (i in seq_len(nrow(raw_rows))) {
  row_id = raw_rows$row_id[i]
  address_raw = raw_rows$address_raw[i]
  g = guard(row_id, address_raw, ask_model(row_id, address_raw))
  f = g$fields
  out = list(row_id = row_id, address_raw = address_raw, address_std = "",
             house_number = "", street = "", unit = "", city = "", state = "",
             confidence = g$confidence, status = "unresolved", lat = "", lon = "",
             geocode_source = "", reason = g$reason)

  # Too unsure, or no street to look up: keep the row, mark it unresolved, guess nothing.
  if (g$confidence < MIN_CONFIDENCE || !nzchar(f[["house_number"]]) || !nzchar(f[["street"]])) {
    out$reason = paste0("Unresolved (confidence ", g$confidence, "). ", g$reason)
    out_rows[[i]] = out
    next
  }

  # Accept the model's text fields, and log each one with the model's reason.
  for (k in FIELDS) {
    if (nzchar(f[[k]])) {
      out[[k]] = f[[k]]
      log_change(row_id, k, address_raw, f[[k]], g$reason, "model")
    }
  }
  line1 = paste(Filter(nzchar, c(f[["house_number"]], f[["street"]], f[["unit"]])), collapse = " ")
  out$address_std = paste0(line1, ", ", f[["city"]], ", ", f[["state"]])

  # The coordinate comes only from the gazetteer. No match means no coordinate.
  key = paste(f[["house_number"]], f[["street"]], f[["city"]], f[["state"]], sep = "|")
  hit = gazetteer %>% filter(key == !!key)
  if (nrow(hit) == 1) {
    out$lat = hit$lat
    out$lon = hit$lon
    out$status = "resolved"
    out$geocode_source = "gazetteer"
    log_change(row_id, "lat,lon", "", paste0(hit$lat, ",", hit$lon),
               "Matched the gazetteer on house number, street, city and state.", "geocoder")
  } else {
    out$reason = paste0("Unresolved: no gazetteer match. ", g$reason)
  }
  out_rows[[i]] = out
}

# 5. WRITE OUTPUT + CHANGE LOG ###################################

out_df = bind_rows(out_rows) %>%
  select(row_id, address_raw, address_std, all_of(FIELDS), confidence, status,
         lat, lon, geocode_source, reason)
write_csv(out_df, OUT_CSV, na = "")
writeLines(sapply(changes, function(x) toJSON(x, auto_unbox = TRUE)), CHANGES_PATH)

n_resolved = sum(out_df$status == "resolved")
cat("Wrote addresses_clean.csv:", n_resolved, "resolved,", nrow(out_df) - n_resolved, "unresolved.\n")
cat("Wrote changes.jsonl:", length(changes), "logged changes.\n")
