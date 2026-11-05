# measure_cold_start.R
# Measure a cold start and warm requests on your deployed API
# Pairs with measure_cold_start.py
# Course kit, module 21
#
# Topic: APIs that sleep
#
# A host that scales to zero stops your API after an idle timeout. This script waits
# longer than that, sends one request and times it (a cold trial), then sends a run of
# requests back to back and times those (warm). It repeats the cold trial, then writes
# everything to measurements.json for cost_estimate and the lab's checks.
#
# Run it from your lab folder:
#   API_URL=https://connect.example.com/content/abc Rscript measure_cold_start.R
# No server handy? Set M21_STUB=1 and it measures stub_host.py, a pretend host, instead.
#
# install.packages(c("httr2", "jsonlite"))

# 0. SETUP ###################################

library(httr2) # for HTTP requests
library(jsonlite) # for writing measurements.json

## 0.1 Configuration #################################

API_URL = sub("/$", "", Sys.getenv("API_URL", ""))
ROUTE = Sys.getenv("ROUTE", "/health")
HOST = Sys.getenv("HOST_NAME", "posit-connect")
IDLE_TIMEOUT_S = as.numeric(Sys.getenv("IDLE_TIMEOUT_S", "5")) # Connect's default; the module page cites the source
COLD_TRIALS = as.integer(Sys.getenv("COLD_TRIALS", "3"))
WARM_COUNT = as.integer(Sys.getenv("WARM_COUNT", "20"))
CLIENT_TIMEOUT_S = as.numeric(Sys.getenv("CLIENT_TIMEOUT_S", "30"))
OUT = Sys.getenv("OUT", "measurements.json")
KEY = Sys.getenv("CONNECT_VIEWER_KEY", "")
STUB = !(Sys.getenv("M21_STUB", "") %in% c("", "0"))

if (STUB) {
  # Start the pretend host in the background; it is a Python file in this folder.
  here = dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE)[1]))
  system2("python3", c(file.path(here, "stub_host.py"), "--port", "8772"), wait = FALSE, stdout = FALSE)
  Sys.sleep(1)
  API_URL = "http://127.0.0.1:8772"
  HOST = "stub (pretend host)"
  IDLE_TIMEOUT_S = 1
}

if (API_URL == "") stop("API_URL not set. Set it to your deployed base URL, or set M21_STUB=1.")

# Wait longer than the idle timeout, or the "cold" trial may land on a warm process.
IDLE_WAIT_S = IDLE_TIMEOUT_S * 2 + 1

# 1. TIME ONE REQUEST ###################################

timed_get = function(path) {
  req = request(paste0(API_URL, path)) |>
    req_timeout(CLIENT_TIMEOUT_S) |>
    req_error(is_error = function(resp) FALSE)
  if (KEY != "") req = req_headers(req, Authorization = paste("Key", KEY))
  start = Sys.time()
  status = tryCatch(resp_status(req_perform(req)), error = function(e) 0L)
  ms = round(as.numeric(difftime(Sys.time(), start, units = "secs")) * 1000, 1)
  list(ms = ms, status = status)
}

# 2. COLD TRIALS AND WARM RUNS ###################################

cold_ms = c(); warm_ms = c(); statuses = c()
per_trial = max(1, WARM_COUNT %/% COLD_TRIALS + 1)
for (trial in seq_len(COLD_TRIALS)) {
  cat("cold trial", trial, "of", COLD_TRIALS, ": waiting", IDLE_WAIT_S, "s so the host can stop the process\n")
  Sys.sleep(IDLE_WAIT_S)
  r = timed_get(ROUTE)
  cold_ms = c(cold_ms, r$ms); statuses = c(statuses, r$status)
  # Right after the cold request the process is warm: time a few in a row.
  for (i in seq_len(per_trial)) {
    if (length(warm_ms) >= WARM_COUNT) break
    r = timed_get(ROUTE)
    warm_ms = c(warm_ms, r$ms); statuses = c(statuses, r$status)
  }
}

# 3. SUMMARISE AND SAVE ###################################

# p95: the time that 95 of every 100 requests beat; the slow end users remember.
ordered = sort(warm_ms)
p95 = ordered[min(length(ordered), round(0.95 * (length(ordered) - 1)) + 1)]

record = list(
  example = STUB, host = HOST, url = API_URL, route = ROUTE,
  measured_at = format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ", tz = "UTC"),
  idle_timeout_s = IDLE_TIMEOUT_S, idle_wait_s = IDLE_WAIT_S, client_timeout_s = CLIENT_TIMEOUT_S,
  cold_ms = cold_ms, warm_ms = warm_ms,
  cold_median_ms = median(cold_ms), warm_median_ms = median(warm_ms), warm_p95_ms = p95,
  statuses = sort(unique(statuses))
)

# Keep anything else already in the file (the load results, the memory you wrote in).
if (file.exists(OUT)) {
  old = fromJSON(OUT, simplifyVector = FALSE)
  old[names(record)] = record
  record = old
}
write_json(record, OUT, auto_unbox = TRUE, pretty = TRUE, digits = NA)

cat("cold median", record$cold_median_ms, "ms, warm median", record$warm_median_ms, "ms, warm p95", p95, "ms\n")
cat("wrote", OUT, "\n")
if (STUB) system("pkill -f 'stub_host.py --port 8772'")
