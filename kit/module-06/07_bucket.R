#' @name 07_bucket.R
#' @title Keep the raw file and the audit log in a private Supabase Storage bucket, and share one by a signed URL
#' @description
#' Pairs with 07_bucket.py
#' Course kit, module 6
#'
#' Topic: Buckets
#'
#' The table now lives in Postgres. Two files do not belong in a table: the raw CSV exactly as
#' it arrived, and the audit log that explains every change. This script puts both in a private
#' bucket, a folder of files on Supabase Storage that nobody can read without a key, then mints
#' a signed URL: a web address for one file that stops working after ten minutes. It talks to
#' the Storage API (/storage/v1) directly with httr2.
#'
#' If you haven't already, install these packages...
#' install.packages(c("httr2", "jsonlite"))
#'
#' Run it from the folder that holds this file, after the repair:
#'   LLM_STUB=1 python3 repair_table.py
#'   Rscript 07_bucket.R
#'
#' It reads two settings from the environment, never from this file:
#'   SUPABASE_URL   your project's address
#'   SUPABASE_KEY   the project's SECRET key (sb_secret_...). Server-side only.
#' No project yet? Leave them unset and the script runs in STUB mode: it prints every request
#' it would make, sends nothing, and exits 0.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

library(httr2) # for HTTP requests to Supabase Storage
library(jsonlite) # for reading the bucket list

## 0.2 Configuration #################################

# Work inside the module-06 folder, so data/ and output/ resolve: the script's own folder,
# the folder you are in, or module-06/ under it, whichever holds data/inventory_raw.csv.
script_arg = grep("^--file=", commandArgs(FALSE), value = TRUE)
here = if (length(script_arg) == 1) dirname(normalizePath(sub("^--file=", "", script_arg))) else getwd()
for (dir in c(here, getwd(), "module-06")) {
  if (file.exists(file.path(dir, "data", "inventory_raw.csv"))) { setwd(dir); break }
}

BUCKET = "inventory-files"
EXPIRES_IN = 600 # seconds a signed URL keeps working: ten minutes

SUPABASE_URL = Sys.getenv("SUPABASE_URL")
SUPABASE_KEY = Sys.getenv("SUPABASE_KEY")

# No address or no key means STUB mode: say so loudly, and send nothing.
STUB = SUPABASE_URL == "" || SUPABASE_KEY == ""
if (STUB) {
  cat(strrep("=", 60), "\n")
  cat("STUB MODE: SUPABASE_URL and SUPABASE_KEY are not set.\n")
  cat("Nothing is sent to Supabase. This prints what the script would do.\n")
  cat(strrep("=", 60), "\n")
}

# Every request carries the key on the apikey header only. Supabase's docs say to "Send
# publishable and secret keys on the apikey header only": these keys are not JWTs, so
# Supabase rejects them as a Bearer token on the Authorization header.
storage_request = function(path, key = SUPABASE_KEY){
  request(paste0(SUPABASE_URL, "/storage/v1", path)) %>%
    req_headers("apikey" = key)
}

# 1. PICK WHAT GOES IN THE BUCKET ###################################

# Files go in the bucket whole. Rows you query go in the table.
# The raw CSV is evidence: kept exactly as it arrived, never edited, so the audit can replay.
FILES = list(
  "raw/inventory_raw.csv" = list(path = file.path("data", "inventory_raw.csv"), type = "text/csv"),
  "audit/audit.jsonl" = list(path = file.path("output", "audit.jsonl"), type = "application/x-ndjson")
)
for (name in names(FILES)) {
  path = FILES[[name]]$path
  if (!file.exists(path)) {
    stop("No ", basename(path), " yet. Run  LLM_STUB=1 python3 repair_table.py  first.")
  }
  cat(name, ": ", file.size(path), " bytes\n", sep = "")
}

# 2. MAKE SURE THE BUCKET IS PRIVATE ###################################

# A public bucket serves every file to anyone who guesses the name. Ours is private.
if (STUB) {
  cat("STUB: would create bucket", BUCKET, "with public = FALSE, if it does not exist yet.\n")
} else {
  buckets = storage_request("/bucket") %>% req_perform() %>% resp_body_json()
  if (!BUCKET %in% sapply(buckets, function(b) b$name)) {
    storage_request("/bucket") %>%
      req_body_json(list(id = BUCKET, name = BUCKET, public = FALSE)) %>%
      req_perform()
    cat("Created private bucket", BUCKET, "\n")
  } else {
    cat("Bucket", BUCKET, "already exists.\n")
  }
}

# 3. UPLOAD THE TWO FILES ###################################

# x-upsert: true replaces a file of the same name, so a second run does not fail.
for (name in names(FILES)) {
  f = FILES[[name]]
  if (STUB) {
    cat("STUB: would POST ", basename(f$path), " to /storage/v1/object/", BUCKET, "/", name, "\n", sep = "")
  } else {
    storage_request(paste0("/object/", BUCKET, "/", name)) %>%
      req_headers(`x-upsert` = "true") %>%
      req_body_multipart(file = curl::form_file(f$path, type = f$type)) %>%
      req_perform()
    cat("Uploaded", name, "\n")
  }
}

# 4. MINT A SIGNED URL ###################################

# A signed URL lets one person fetch one file without a key, until it expires.
# Send the link, never the key.
if (STUB) {
  cat("STUB: would POST to /storage/v1/object/sign/", BUCKET, "/raw/inventory_raw.csv\n", sep = "")
  cat("      with expiresIn =", EXPIRES_IN, "and print the link it returns.\n")
} else {
  signed = storage_request(paste0("/object/sign/", BUCKET, "/raw/inventory_raw.csv")) %>%
    req_body_json(list(expiresIn = EXPIRES_IN)) %>%
    req_perform() %>%
    resp_body_json()
  # The answer is a path that starts at /object/sign; the full link adds the project address.
  cat("Signed URL, good for", EXPIRES_IN / 60, "minutes:\n")
  cat(paste0(SUPABASE_URL, "/storage/v1", signed$signedURL), "\n")
}
