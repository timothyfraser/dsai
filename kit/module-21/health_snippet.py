# health_snippet.py
# A health route that tells "asleep and waking" from "broken"
# Pairs with health_snippet.R
# Course kit, module 21
#
# Topic: APIs that sleep
#
# Paste this route into your FastAPI app, next to your other routes.
# It answers "I am up, and this is my version", and does nothing slow.
# Time the first call after a quiet spell and you see the cold start with no model in it.

from fastapi import FastAPI  # for the app

app = FastAPI()
VERSION = "1.0.0"  # bump it on every deploy, so the smoke test proves the new code is live


@app.get("/health")
def health():
    # No model call, no database call: if this is slow, the host is waking, not your code.
    return {"ok": True, "version": VERSION}
