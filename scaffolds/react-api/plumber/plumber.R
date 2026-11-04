# Routes only: parse the input, call R/logic.R, return JSON.
library(plumber)

source("R/logic.R")

#* @apiTitle Example API
#* @apiDescription A small API for a React page.

# CORS: which web address may a browser page call this API from?
# CORS_ORIGIN is an environment variable. Unset, it falls back to "*" (anyone),
# which is fine on your own machine. When you deploy, set CORS_ORIGIN on the
# Connect content to the address of your deployed page.
# Locally you can skip CORS altogether with the Vite dev proxy
# (see ../reactfront/vite.config.js).
# This filter must be the first one in the file.
#* @filter cors
function(req, res) {
  res$setHeader("Access-Control-Allow-Origin", Sys.getenv("CORS_ORIGIN", "*"))
  if (req$REQUEST_METHOD == "OPTIONS") {
    res$setHeader("Access-Control-Allow-Methods", "*")
    res$setHeader("Access-Control-Allow-Headers", "*")
    res$status = 200
    return(list())
  }
  plumber::forward()
}

#* Is the API up?
#* @get /health
function() {
  list(status = "ok", version = "1.0.0")
}

#* Count, mean, min and max of a list of numbers
#* @post /summary
function(req, res) {
  out = tryCatch(
    summarize(req$body$values),
    error = function(e) {
      res$status = 422
      list(detail = conditionMessage(e))
    }
  )
  out
}

#* @plumber
function(pr) {
  # Return unboxed JSON: {"status": "ok"}, not {"status": ["ok"]}
  plumber::pr_set_serializer(pr, plumber::serializer_unboxed_json())
}
