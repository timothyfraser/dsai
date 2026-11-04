# check_api.py
# Check a deployed API and app from the outside
# Course kit, module 4
#
# Topic: Deploying an API, and a smoke test that says plainly when it is down
#
# The lab asks for a live address, and a live address can fail in five ways.
# This script calls yours and prints one PASS or FAIL line for each: does
# /health answer 200 with JSON, does one data route return the documented
# shape, does a smoke test fail cleanly on a wrong address, and does the app
# load. Checks C1 and C2 look inside your repo, so you run those by hand.
#
# No python packages to install: it uses only the standard library.
#
# Run it from this folder:
#   API_URL=https://your-server/your-api APP_URL=https://your-server/your-app python3 check_api.py
#   API_STUB=1 python3 check_api.py     # no server handy: a local stub stands in
# Settings you may change: DATA_ROUTE (default /greetings/en), DATA_KEYS (default lang,text).
# Exits 1 if any check fails.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import json  # for reading the JSON bodies
import os  # for the settings
import sys  # for the exit code
import threading  # for running the stub beside the checks
import urllib.request  # for calling the addresses
from http.server import BaseHTTPRequestHandler, HTTPServer  # for the stub server

## 0.2 Configuration #################################

STUB = os.getenv("API_STUB", "")
API_URL = os.getenv("API_URL", "")
APP_URL = os.getenv("APP_URL", "")
DATA_ROUTE = os.getenv("DATA_ROUTE", "/greetings/en")  # the data route the lab asks for
DATA_KEYS = os.getenv("DATA_KEYS", "lang,text").split(",")  # the documented shape of its answer

# 1. THE STUB (ONLY IF ASKED) ###################################

# The stub answers the way a healthy deployment would. It is a fixture for this
# check, never output from your own server.
class Stub(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            body, kind = {"status": "ok"}, "application/json"
        elif self.path == DATA_ROUTE:
            body, kind = {"lang": "en", "text": "Hello"}, "application/json"
        elif self.path == "/app":
            body, kind = "<html><body>stub app</body></html>", "text/html"
        else:
            self.send_response(404)
            self.end_headers()
            return
        raw = (body if isinstance(body, str) else json.dumps(body)).encode()
        self.send_response(200)
        self.send_header("Content-Type", kind)
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args):  # keep the check output to PASS and FAIL lines
        pass

if STUB:
    server = HTTPServer(("127.0.0.1", 0), Stub)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    API_URL = f"http://127.0.0.1:{server.server_port}"
    APP_URL = API_URL + "/app"
    print(f"API_STUB is set: using a local stub at {API_URL}\n")
if not API_URL:
    sys.exit("API_URL is not set. Run: API_URL=https://your-server/your-api python3 check_api.py")
API_URL = API_URL.rstrip("/")

# 2. THE SMOKE TEST ###################################

# Call one address. Return (status, body) or (None, reason) when it cannot be reached.
def fetch(url):
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return None, type(e).__name__

# The smoke test the lab asks you to write: True only if every call works.
def smoke(base):
    status, body = fetch(base + "/health")
    if status != 200:
        return False
    status, body = fetch(base + DATA_ROUTE)
    return status == 200 and body.strip() not in ("", "{}", "[]")

# 3. THE CHECKS ###################################

results = []
def report(status, name, detail=""):
    results.append(status)
    print(f"{status}  {name}" + (f"  ({detail})" if detail else ""))

status, body = fetch(API_URL + "/health")
report("PASS" if status == 200 else "FAIL", "C3 /health answers 200", f"got {status}")

try:
    health = json.loads(body)
    report("PASS" if "ok" in str(health) else "FAIL", "C4 /health is JSON and says ok", str(health)[:60])
except ValueError:
    report("FAIL", "C4 /health is JSON and says ok", "the body is not JSON")

status, body = fetch(API_URL + DATA_ROUTE)
try:
    data = json.loads(body)
    row = data[0] if isinstance(data, list) and data else data
    missing = [k for k in DATA_KEYS if not isinstance(row, dict) or k not in row]
    report("PASS" if status == 200 and not missing else "FAIL",
           f"C5 {DATA_ROUTE} returns the documented shape", f"missing {missing}" if missing else f"keys {DATA_KEYS}")
except ValueError:
    report("FAIL", f"C5 {DATA_ROUTE} returns the documented shape", f"status {status}, body is not JSON")

# A smoke test that passes on a wrong address is worse than none.
wrong_ok = smoke("http://127.0.0.1:9")
report("PASS" if not wrong_ok else "FAIL", "C6 the smoke test fails on a wrong address")

if APP_URL:
    status, _ = fetch(APP_URL)
    report("PASS" if status == 200 else "FAIL", "C7 the app answers 200", f"got {status}")
else:
    report("SKIP", "C7 the app answers 200", "APP_URL is not set")

print(f"\n{results.count('PASS')} passed, {results.count('FAIL')} failed, {results.count('SKIP')} skipped")
sys.exit(1 if "FAIL" in results else 0)
