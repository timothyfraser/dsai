# cache_route.R
# A cached route: serve a stored answer while it is fresh, compute it again when it is stale
# Pairs with cache_route.py
# Course kit, module 21
#
# Topic: APIs that sleep
#
# A slow answer that changes slowly does not need computing on every request. A scheduled
# job (Module 9) or the first caller writes it to cache/predict.json with a made_at stamp.
# This route serves that copy while it is younger than TTL_S, and only falls back to the
# slow live route when the copy is missing or stale.
#
# Add it to your plumber.R, and replace live_predict() with your own slow route.
# install.packages(c("plumber", "jsonlite"))

# 0. SETUP ###################################

library(plumber) # for the API
library(jsonlite) # for the stored answer

CACHE = "cache/predict.json"
TTL_S = 3600 # time to live: how old a stored answer may be before it is refreshed

# 1. THE SLOW LIVE ANSWER ###################################

live_predict = function() {
  # Replace this with your real route's work (a model call, a big query).
  list(predicted_vehicle_count = 42.0)
}

# 2. READ, CHECK THE AGE, OR REFRESH ###################################

stamp = function() format(Sys.time(), "%Y-%m-%dT%H:%M:%S+00:00", tz = "UTC")

#* Cached prediction
#* @get /predict_cached
function() {
  if (file.exists(CACHE)) {
    stored = fromJSON(CACHE)
    made = as.POSIXct(substr(stored$made_at, 1, 19), format = "%Y-%m-%dT%H:%M:%S", tz = "UTC")
    age_s = as.numeric(difftime(Sys.time(), made, units = "secs"))
    # A fresh copy costs the server almost nothing, even right after a cold start.
    if (age_s < TTL_S) return(c(stored, list(ttl_s = TTL_S, source = "cache")))
  }
  # Missing or stale: do the slow work once, store it, and serve it.
  answer = c(live_predict(), list(made_at = stamp()))
  dir.create(dirname(CACHE), showWarnings = FALSE, recursive = TRUE)
  write_json(answer, CACHE, auto_unbox = TRUE)
  c(answer, list(ttl_s = TTL_S, source = "live"))
}
