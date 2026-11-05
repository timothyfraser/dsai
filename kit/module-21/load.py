# load.py
# Send a small, capped burst of requests and record what came back
# Pairs with load.R
# Course kit, module 21
#
# Topic: APIs that sleep
#
# A burst of callers is how you learn whether your API says "slow down" (429, 503 with a
# Retry-After) or quietly falls over (500, timeouts). This script sends COUNT requests at
# RATE per second, one at a time, and adds a "load" block to measurements.json.
#
# The caps are hard: a class of teams load-testing one shared server is its own outage.
#   API_URL=https://connect.example.com/content/abc python3 load.py
#   M21_STUB=1 python3 load.py
#
# Uses only the Python standard library.

# 0. SETUP ###################################

import json  # for measurements.json
import os  # for settings
import sys  # for the exit code
import time  # for pacing
import urllib.error  # for failed requests
import urllib.request  # for HTTP requests

## 0.1 Configuration #################################

API_URL = os.environ.get("API_URL", "").rstrip("/")
ROUTE = os.environ.get("ROUTE", "/health")
MAX_COUNT, MAX_RATE = 50, 2.0  # the hard caps: never more than 50 requests, 2 a second
COUNT = min(int(os.environ.get("COUNT", "20")), MAX_COUNT)
RATE = min(float(os.environ.get("RATE", "1")), MAX_RATE)
CLIENT_TIMEOUT_S = float(os.environ.get("CLIENT_TIMEOUT_S", "30"))
OUT = os.environ.get("OUT", "measurements.json")

if os.environ.get("M21_STUB", "") not in ("", "0"):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import stub_host  # the pretend host
    stub_host.serve(8773)
    API_URL, RATE = "http://127.0.0.1:8773", MAX_RATE

if not API_URL:
    sys.exit("API_URL not set. Set it to your deployed base URL, or set M21_STUB=1.")

# 1. SEND THE BURST ###################################

results = []
for i in range(COUNT):
    start = time.perf_counter()
    retry_after = None
    try:
        with urllib.request.urlopen(API_URL + ROUTE, timeout=CLIENT_TIMEOUT_S) as resp:
            resp.read()
            status = resp.status
    except urllib.error.HTTPError as e:
        status, retry_after = e.code, e.headers.get("Retry-After")
    except Exception:
        status = 0  # a timeout or a refused connection
    ms = round((time.perf_counter() - start) * 1000, 1)
    results.append({"status": status, "ms": ms, "retry_after": retry_after})
    time.sleep(max(0.0, 1.0 / RATE - ms / 1000))

# 2. SAVE ###################################

counts = {}
for r in results:
    counts[str(r["status"])] = counts.get(str(r["status"]), 0) + 1

record = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
# A 5xx other than 503, or a 429 or 503 with no Retry-After, needs a line in "explained".
record["load"] = {"route": ROUTE, "count": COUNT, "rate_per_s": RATE,
                  "status_counts": counts, "requests": results,
                  "explained": record.get("load", {}).get("explained", {})}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(record, f, indent=2)
    f.write("\n")
print(f"sent {COUNT} at {RATE}/s: {counts}")
