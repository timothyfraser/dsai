# cache_route.py
# A cached route: serve a stored answer while it is fresh, compute it again when it is stale
# Pairs with cache_route.R
# Course kit, module 21
#
# Topic: APIs that sleep
#
# A slow answer that changes slowly does not need computing on every request. A scheduled
# job (Module 9) or the first caller writes it to cache/predict.json with a made_at stamp.
# This route serves that copy while it is younger than TTL_S, and only falls back to the
# slow live route when the copy is missing or stale.
#
# Add it to your FastAPI app, and replace live_predict() with your own slow route.
#   pip install fastapi uvicorn
#   python -m uvicorn cache_route:app --port 8000

# 0. SETUP ###################################

import json  # for the stored answer
from datetime import datetime, timezone  # for made_at and the age check
from pathlib import Path  # for the cache file

from fastapi import FastAPI  # for the app

app = FastAPI()
CACHE = Path("cache/predict.json")
TTL_S = 3600  # time to live: how old a stored answer may be before it is refreshed

# 1. THE SLOW LIVE ANSWER ###################################


def live_predict():
    # Replace this with your real route's work (a model call, a big query).
    return {"predicted_vehicle_count": 42.0}

# 2. READ, CHECK THE AGE, OR REFRESH ###################################


def now():
    return datetime.now(timezone.utc)


@app.get("/predict_cached")
def predict_cached():
    if CACHE.exists():
        stored = json.loads(CACHE.read_text(encoding="utf-8"))
        age_s = (now() - datetime.fromisoformat(stored["made_at"])).total_seconds()
        # A fresh copy costs the server almost nothing, even right after a cold start.
        if age_s < TTL_S:
            return {**stored, "ttl_s": TTL_S, "source": "cache"}
    # Missing or stale: do the slow work once, store it, and serve it.
    answer = {**live_predict(), "made_at": now().isoformat(timespec="seconds")}
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(answer), encoding="utf-8")
    return {**answer, "ttl_s": TTL_S, "source": "live"}
