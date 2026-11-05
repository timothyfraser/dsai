# health_snippet.R
# A health route that tells "asleep and waking" from "broken"
# Pairs with health_snippet.py
# Course kit, module 21
#
# Topic: APIs that sleep
#
# Paste this route into your plumber.R, next to your other routes.
# It answers "I am up, and this is my version", and does nothing slow.
# Time the first call after a quiet spell and you see the cold start with no model in it.

VERSION = "1.0.0" # bump it on every deploy, so the smoke test proves the new code is live

#* Health check
#* @get /health
function() {
  # No model call, no database call: if this is slow, the host is waking, not your code.
  list(ok = TRUE, version = VERSION)
}
