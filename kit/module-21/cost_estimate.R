# cost_estimate.R
# Turn your measurements and a host's published prices into a monthly bill at three traffic levels
# Pairs with cost_estimate.py
# Course kit, module 21
#
# Topic: APIs that sleep
#
# It reads measurements.json (what you measured) and prices.json (what the vendor pages
# say, each with its URL and the day you read it) and writes cost.json. It types no
# number of its own: run it twice on the same two files and cost.json is byte for byte
# the same, which is how the lab's check C7 knows nobody edited a figure by hand.
#
# Run it from your lab folder:
#   Rscript cost_estimate.R
#
# install.packages(c("jsonlite", "digest"))

# 0. SETUP ###################################

library(jsonlite) # for reading and writing
library(digest) # for fingerprints of the two input files

MEASUREMENTS = Sys.getenv("MEASUREMENTS", "measurements.json")
PRICES = Sys.getenv("PRICES", "prices.json")
OUT = Sys.getenv("OUT", "cost.json")
LEVELS = c(100, 10000, 100000) # requests a day: a class once a day, steady, busy
DAYS = 30

# 1. READ, AND REFUSE INCOMPLETE INPUTS ###################################

m = fromJSON(MEASUREMENTS, simplifyVector = FALSE)
p = fromJSON(PRICES, simplifyVector = FALSE)
sha = function(path) substr(digest(file = path, algo = "sha256"), 1, 16)

needed = c("cold_median_ms", "warm_median_ms", "idle_timeout_s", "memory_gb", "vcpu", "model_calls_per_request")
missing = setdiff(needed, names(m))
if (length(missing) > 0) stop("measurements.json is missing ", paste(missing, collapse = ", "),
                              ". Measure first, then write memory_gb, vcpu and model_calls_per_request in.")

priced = c(p$hosts, list(model = p$model))
for (name in names(priced)) {
  e = priced[[name]]
  if (!startsWith(as.character(if (is.null(e$source_url)) "" else e$source_url), "https://") || is.null(e$accessed))
    stop("prices.json: '", name, "' needs a source_url (https://) and an accessed date.")
}

# A number, or NULL when the price is 'see vendor page'.
price = function(entry, key) if (is.numeric(entry[[key]])) entry[[key]] else NULL

# 2. HOW MANY REQUESTS ARE COLD ###################################

# If requests arrive at random, the chance that the gap before one is longer than the
# idle timeout is exp(-idle_timeout / mean_gap). Those requests meet a cold start.
# This is an assumption about your traffic, and cost.json says so.

level_row = function(per_day) {
  per_month = per_day * DAYS
  mean_gap_s = 86400 / per_day
  cold_fraction = exp(-m$idle_timeout_s / mean_gap_s)
  cold_starts = per_month * cold_fraction
  gb_s = per_month * (m$warm_median_ms / 1000) * m$memory_gb
  vcpu_s = per_month * (m$warm_median_ms / 1000) * m$vcpu
  cold_gb_s = cold_starts * (m$cold_median_ms / 1000) * m$memory_gb
  model_calls = per_month * m$model_calls_per_request

  # 3. THE HOST BILL ###################################

  host_cost = list(); fixed_host = list()
  for (name in names(p$hosts)) {
    h = p$hosts[[name]]
    if (identical(h$kind, "fixed")) fixed_host[name] = list(price(h, "fixed_month_usd"))
    if (identical(h$kind, "per_request")) {
      per_req = price(h, "price_per_million_requests_usd"); per_gb_s = price(h, "price_per_gb_s_usd")
      billed = gb_s + if (isTRUE(h$bills_cold_start)) cold_gb_s else 0
      # Some hosts bill vCPU-seconds as well as memory; the rest leave the key out.
      per_vcpu_s = if (is.null(h$price_per_vcpu_s_usd)) 0 else price(h, "price_per_vcpu_s_usd")
      free_vcpu = if (is.null(h$free_vcpu_s_month)) 0 else h$free_vcpu_s_month
      host_cost[name] = list(if (is.null(per_req) || is.null(per_gb_s) || is.null(per_vcpu_s)) NULL else round(
        max(0, per_month - h$free_requests_month) / 1e6 * per_req +
          max(0, billed - h$free_gb_s_month) * per_gb_s +
          max(0, vcpu_s - free_vcpu) * per_vcpu_s, 2))
    }
  }

  # 4. THE MODEL BILL, WHICH SCALE TO ZERO DOES NOT TOUCH ###################################

  per_call = price(p$model, "price_per_model_call_usd")
  model_cost = if (is.null(per_call)) NULL else round(model_calls * per_call, 2)

  list(requests_day = per_day, requests_month = per_month, mean_gap_s = round(mean_gap_s, 3),
       cold_fraction = round(cold_fraction, 4), cold_starts_month = round(cold_starts),
       gb_s_month = round(gb_s, 1), vcpu_s_month = round(vcpu_s, 1), cold_gb_s_month = round(cold_gb_s, 1),
       model_calls_month = round(model_calls), host_cost = host_cost, fixed_host = fixed_host,
       model_cost = model_cost)
}

# 5. WRITE cost.json ###################################

cost = list(
  made_by = "cost_estimate.R",
  inputs = list(measurements_sha256 = sha(MEASUREMENTS), prices_sha256 = sha(PRICES), example = isTRUE(m$example)),
  assumptions = list(days_per_month = DAYS,
                     arrivals = "random (Poisson): cold_fraction = exp(-idle_timeout_s / mean_gap_s)",
                     memory_gb = m$memory_gb, vcpu = m$vcpu, model_calls_per_request = m$model_calls_per_request,
                     left_out = "idle billing, network transfer, storage"),
  # Keeping one process warm all month holds this much memory whether or not anyone calls.
  keep_warm = list(processes = 1, memory_gb_hours_month = round(m$memory_gb * 24 * DAYS, 1)),
  levels = lapply(LEVELS, level_row)
)
write_json(cost, OUT, auto_unbox = TRUE, pretty = TRUE, null = "null", digits = NA)
for (row in cost$levels) cat(row$requests_day, "a day: cold fraction", row$cold_fraction,
                             ", model calls", row$model_calls_month, "\n")
cat("wrote", OUT, "\n")
