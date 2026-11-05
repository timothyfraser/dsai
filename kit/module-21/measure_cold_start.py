# measure_cold_start.py
# Measure a cold start and warm requests on your deployed API
# Pairs with measure_cold_start.R
# Course kit, module 21
#
# Topic: APIs that sleep
#
# A host that scales to zero stops your API after an idle timeout. This script waits
# longer than that, sends one request and times it (a cold trial), then sends a run of
# requests back to back and times those (warm). It repeats the cold trial, then writes
# everything to measurements.json for cost_estimate.py and the lab's checks.
#
# Run it from your lab folder:
#   API_URL=https://connect.example.com/content/abc python3 measure_cold_start.py
# No server handy? Set M21_STUB=1 and it measures stub_host.py, a pretend host, instead.
#   M21_STUB=1 python3 measure_cold_start.py
#
# Uses only the Python standard library. It never prints or stores a key.

# 0. SETUP ###################################

import json  # for writing measurements.json
import os  # for settings
import statistics  # for the median
import sys  # for the exit code
import time  # for timing and waiting
import urllib.error  # for failed requests
import urllib.request  # for HTTP requests
from datetime import datetime, timezone  # for measured_at

## 0.1 Configuration #################################

API_URL = os.environ.get("API_URL", "").rstrip("/")
ROUTE = os.environ.get("ROUTE", "/health")
HOST = os.environ.get("HOST_NAME", "posit-connect")
IDLE_TIMEOUT_S = float(os.environ.get("IDLE_TIMEOUT_S", "5"))  # Connect's default; the module page cites the source
COLD_TRIALS = int(os.environ.get("COLD_TRIALS", "3"))
WARM_COUNT = int(os.environ.get("WARM_COUNT", "20"))
CLIENT_TIMEOUT_S = float(os.environ.get("CLIENT_TIMEOUT_S", "30"))
OUT = os.environ.get("OUT", "measurements.json")
KEY = os.environ.get("CONNECT_VIEWER_KEY", "")
STUB = os.environ.get("M21_STUB", "") not in ("", "0")

if STUB:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import stub_host  # the pretend host, started inside this script
    stub_host.serve(8771)
    API_URL, HOST, IDLE_TIMEOUT_S = "http://127.0.0.1:8771", "stub (pretend host)", stub_host.IDLE_TIMEOUT_S

if not API_URL:
    sys.exit("API_URL not set. Set it to your deployed base URL, or set M21_STUB=1.")

# Wait longer than the idle timeout, or the "cold" trial may land on a warm process.
IDLE_WAIT_S = IDLE_TIMEOUT_S * 2 + 1

# 1. TIME ONE REQUEST ###################################


def timed_get(path):
    """Return (milliseconds, status) for one GET. A timeout counts as status 0."""
    req = urllib.request.Request(API_URL + path)
    if KEY:
        req.add_header("Authorization", "Key " + KEY)
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=CLIENT_TIMEOUT_S) as resp:
            resp.read()
            status = resp.status
    except urllib.error.HTTPError as e:
        status = e.code
    except Exception:
        status = 0
    return round((time.perf_counter() - start) * 1000, 1), status


# 2. COLD TRIALS AND WARM RUNS ###################################

cold_ms, warm_ms, statuses = [], [], []
per_trial = max(1, WARM_COUNT // COLD_TRIALS + 1)
for trial in range(COLD_TRIALS):
    print(f"cold trial {trial + 1} of {COLD_TRIALS}: waiting {IDLE_WAIT_S:.0f} s so the host can stop the process")
    time.sleep(IDLE_WAIT_S)
    ms, status = timed_get(ROUTE)
    cold_ms.append(ms)
    statuses.append(status)
    # Right after the cold request the process is warm: time a few in a row.
    for _ in range(per_trial):
        if len(warm_ms) >= WARM_COUNT:
            break
        ms, status = timed_get(ROUTE)
        warm_ms.append(ms)
        statuses.append(status)

# 3. SUMMARISE AND SAVE ###################################

# p95: the time that 95 of every 100 requests beat; the slow end users remember.
ordered = sorted(warm_ms)
p95 = ordered[min(len(ordered) - 1, int(round(0.95 * (len(ordered) - 1))))]

record = {
    "example": STUB,
    "host": HOST,
    "url": API_URL,
    "route": ROUTE,
    "measured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "idle_timeout_s": IDLE_TIMEOUT_S,
    "idle_wait_s": IDLE_WAIT_S,
    "client_timeout_s": CLIENT_TIMEOUT_S,
    "cold_ms": cold_ms,
    "warm_ms": warm_ms,
    "cold_median_ms": statistics.median(cold_ms),
    "warm_median_ms": statistics.median(warm_ms),
    "warm_p95_ms": p95,
    "statuses": sorted(set(statuses)),
}

# Keep anything else already in the file (the load results, the memory you wrote in).
if os.path.exists(OUT):
    with open(OUT, encoding="utf-8") as f:
        old = json.load(f)
    old.update(record)
    record = old

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(record, f, indent=2)
    f.write("\n")

print(f"cold median {record['cold_median_ms']} ms, warm median {record['warm_median_ms']} ms, warm p95 {p95} ms")
print(f"wrote {OUT}")
