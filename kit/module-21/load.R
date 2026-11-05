# load.R
# Send a small, capped burst of requests and record what came back
# Pairs with load.py
# Course kit, module 21
#
# Topic: APIs that sleep
#
# A burst of callers is how you learn whether your API says "slow down" (429, 503 with a
# Retry-After) or quietly falls over (500, timeouts). This script sends COUNT requests at
# RATE per second, one at a time, and adds a "load" block to measurements.json.
#
# The caps are hard: a class of teams load-testing one shared server is its own outage.
#   API_URL=https://connect.example.com/content/abc Rscript load.R
#
# install.packages(c("httr2", "jsonlite"))

# 0. SETUP ###################################

library(httr2) # for HTTP requests
library(jsonlite) # for measurements.json

## 0.1 Configuration #################################

API_URL = sub("/$", "", Sys.getenv("API_URL", ""))
ROUTE = Sys.getenv("ROUTE", "/health")
MAX_COUNT = 50; MAX_RATE = 2 # the hard caps: never more than 50 requests, 2 a second
COUNT = min(as.integer(Sys.getenv("COUNT", "20")), MAX_COUNT)
RATE = min(as.numeric(Sys.getenv("RATE", "1")), MAX_RATE)
CLIENT_TIMEOUT_S = as.numeric(Sys.getenv("CLIENT_TIMEOUT_S", "30"))
OUT = Sys.getenv("OUT", "measurements.json")
if (API_URL == "") stop("API_URL not set. Set it to your deployed base URL.")

# 1. SEND THE BURST ###################################

results = list()
for (i in seq_len(COUNT)) {
  start = Sys.time()
  resp = tryCatch(
    request(paste0(API_URL, ROUTE)) |> req_timeout(CLIENT_TIMEOUT_S) |>
      req_error(is_error = function(r) FALSE) |> req_perform(),
    error = function(e) NULL)
  ms = round(as.numeric(difftime(Sys.time(), start, units = "secs")) * 1000, 1)
  status = if (is.null(resp)) 0L else resp_status(resp) # 0 is a timeout or a refused connection
  retry_after = if (is.null(resp)) NULL else resp_header(resp, "Retry-After")
  results[[i]] = list(status = status, ms = ms, retry_after = retry_after)
  Sys.sleep(max(0, 1 / RATE - ms / 1000))
}

# 2. SAVE ###################################

counts = as.list(table(sapply(results, function(r) as.character(r$status))))
record = if (file.exists(OUT)) fromJSON(OUT, simplifyVector = FALSE) else list()
# A 5xx other than 503, or a 429 or 503 with no Retry-After, needs a line in "explained".
explained = if (is.null(record$load$explained)) setNames(list(), character(0)) else record$load$explained
record$load = list(route = ROUTE, count = COUNT, rate_per_s = RATE,
                   status_counts = counts, requests = results, explained = explained)
write_json(record, OUT, auto_unbox = TRUE, pretty = TRUE, null = "null", digits = NA)
cat("sent", COUNT, "at", RATE, "per second\n")
