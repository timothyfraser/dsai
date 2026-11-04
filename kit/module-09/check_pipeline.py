# check_pipeline.py
# Check a team's pipeline folder and its served model
# Course kit, module 09
#
# Topic: A pipeline you can prove is working
#
# A pipeline runs while nobody watches, so you need a script that looks at what it
# left behind. This one prints one PASS or FAIL line for each check: did the ingest
# store today's rows, did it store any row twice, is there a saved model with a
# recorded metric in a sane range, does the served API pass a smoke test, does the
# smoke test fail on a wrong address, and does the agent's answer quote the model.
#
# No python packages to install: it uses only the standard library.
#
# Your folder needs this layout (change the names in 0.2 if yours differ):
#   data/traffic.db          the ingest table, called traffic
#   data/model.json          the saved model, with test_rmse inside it or in data/validation.json
#   data/agent_answer.txt    what your agent printed for day 1 at hour 8
#
# Run it from this folder:
#   PIPE_DIR=../../my-pipeline API_URL=https://your-server/your-api python3 check_pipeline.py
#   PIPE_STUB=1 python3 check_pipeline.py     # no server handy: an example folder and a stub stand in
#   PIPE_STUB=1 PIPE_FLAW=duplicates python3 check_pipeline.py   # a planted flaw, which must fail
# Exits 1 if any check fails.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import json  # for reading the JSON files and bodies
import os  # for the settings
import re  # for finding numbers in the agent's answer
import sqlite3  # for reading the ingest table
import sys  # for the exit code
import tempfile  # for the stub's example folder
import threading  # for running the stub beside the checks
import time  # for today's date in UTC
import urllib.request  # for calling the addresses
from http.server import BaseHTTPRequestHandler, HTTPServer  # for the stub server

import make_example  # builds the example folder the stub mode checks

## 0.2 Configuration #################################

STUB = os.getenv("PIPE_STUB", "")
FLAW = os.getenv("PIPE_FLAW", "")  # only with PIPE_STUB: plant one flaw to see its check fail
PIPE_DIR = os.getenv("PIPE_DIR", ".")
API_URL = os.getenv("API_URL", "")
METRO_ID = int(os.getenv("METRO_ID", "948"))  # the metro your ingest writes
METRIC_KEY = os.getenv("METRIC_KEY", "test_rmse")  # the metric your training records
METRIC_MIN = float(os.getenv("METRIC_MIN", "0"))  # the stated range for that metric:
METRIC_MAX = float(os.getenv("METRIC_MAX", "50"))  # vehicles per minute, for the course model
TODAY = os.getenv("PIPE_TODAY", time.strftime("%Y-%m-%d", time.gmtime()))  # UTC, like the ingest

# 1. THE STUB (ONLY IF ASKED) ###################################

# The stub answers the way a healthy deployment would. It is a fixture for this
# check, never output from your own server.
class Stub(BaseHTTPRequestHandler):
    def do_GET(self):
        if FLAW == "api_down":
            self.send_response(500)
            self.end_headers()
            return
        if self.path == "/health":
            body = {"status": "ok"}
        elif self.path.startswith("/predict"):
            body = {"predicted_vehicle_count": make_example.STUB_PREDICTION, "standard_error": 10.3}
        else:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def log_message(self, *args):  # keep the check output to PASS and FAIL lines
        pass

if STUB:
    PIPE_DIR = tempfile.mkdtemp(prefix="pipe_example_")
    make_example.build(PIPE_DIR, FLAW or None)
    server = HTTPServer(("127.0.0.1", 0), Stub)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    API_URL = f"http://127.0.0.1:{server.server_port}"
    print(f"PIPE_STUB is set: example folder {PIPE_DIR}, local stub at {API_URL}"
          + (f", planted flaw: {FLAW}" if FLAW else "") + "\n")
if not API_URL:
    sys.exit("API_URL is not set. Run: PIPE_DIR=your-folder API_URL=https://your-server/your-api python3 check_pipeline.py")
API_URL = API_URL.rstrip("/")

# 2. HELPERS ###################################

# Call one address. Return (status, body) or (None, reason) when it cannot be reached.
def fetch(url):
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return None, type(e).__name__

# The smoke test the lab asks you to write: True only if /health and one prediction work.
def smoke(base):
    status, _ = fetch(base + "/health")
    if status != 200:
        return False
    status, body = fetch(base + "/predict?day_of_week=1&hour_of_day=8")
    return status == 200 and body.strip() not in ("", "{}", "[]")

results = []
def report(status, name, detail=""):
    results.append(status)
    print(f"{status}  {name}" + (f"  ({detail})" if detail else ""))

def read_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None

# 3. THE INGEST CHECKS ###################################

db_path = os.path.join(PIPE_DIR, "data", "traffic.db")
today_rows, dupes, db_note = 0, None, ""
try:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    today_rows = conn.execute("SELECT COUNT(*) FROM traffic WHERE metro_id = ? AND substr(observed_at, 1, 10) = ?",
                              (METRO_ID, TODAY)).fetchone()[0]
    # A row is a duplicate when the same monitor reports the same minute more than once.
    dupes = conn.execute("SELECT COUNT(*) FROM (SELECT 1 FROM traffic WHERE metro_id = ? "
                         "GROUP BY monitor_id, observed_at HAVING COUNT(*) > 1)", (METRO_ID,)).fetchone()[0]
    conn.close()
except sqlite3.Error as e:
    db_note = f"cannot read {db_path}: {e}"

report("PASS" if today_rows > 0 else "FAIL", "C1 the ingest stored rows for today", db_note or f"{today_rows} rows for today, UTC")
report("PASS" if dupes == 0 else "FAIL", "C2 no monitor-minute is stored twice", db_note or f"{dupes} duplicated")

# 4. THE TRAINING CHECKS ###################################

model_path = os.path.join(PIPE_DIR, "data", "model.json")
model = read_json(model_path)
report("PASS" if isinstance(model, dict) else "FAIL", "C3 model.json exists and is JSON", model_path)

# The metric may sit in the model file itself or in a validation file beside it.
metric = None
for doc in (model, read_json(os.path.join(PIPE_DIR, "data", "validation.json"))):
    if isinstance(doc, dict) and isinstance(doc.get(METRIC_KEY), (int, float)):
        metric = float(doc[METRIC_KEY])
        break
in_range = metric is not None and METRIC_MIN <= metric <= METRIC_MAX
report("PASS" if in_range else "FAIL", f"C4 {METRIC_KEY} is recorded and within {METRIC_MIN:g} to {METRIC_MAX:g}",
       "no such field" if metric is None else f"got {metric:g}")

# 5. THE API CHECKS ###################################

status, body = fetch(API_URL + "/health")
healthy = False
try:
    healthy = status == 200 and "ok" in str(json.loads(body))
except ValueError:
    pass
report("PASS" if healthy else "FAIL", "C5 /health answers 200 with JSON that says ok", f"got {status}")

status, body = fetch(API_URL + "/predict?day_of_week=1&hour_of_day=8")
predicted = None
try:
    predicted = json.loads(body).get("predicted_vehicle_count")
except (ValueError, AttributeError):
    pass
report("PASS" if status == 200 and isinstance(predicted, (int, float)) else "FAIL",
       "C6 /predict returns a number for day 1 at hour 8", f"status {status}, value {predicted}")

# A smoke test that passes on a wrong address is worse than none.
report("PASS" if not smoke("http://127.0.0.1:9") else "FAIL", "C7 the smoke test fails on a wrong address")

# 6. THE AGENT CHECK ###################################

# The agent must quote the number the endpoint gave. Compare as numbers, not as loose text.
try:
    with open(os.path.join(PIPE_DIR, "data", "agent_answer.txt"), encoding="utf-8") as f:
        answer = f.read()
except OSError:
    answer = ""
said = [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", answer)]
cited = isinstance(predicted, (int, float)) and any(abs(n - predicted) < 0.05 for n in said)
report("PASS" if cited else "FAIL", "C8 the agent's answer quotes the model's number", f"endpoint said {predicted}")

print(f"\n{results.count('PASS')} passed, {results.count('FAIL')} failed")
sys.exit(1 if "FAIL" in results else 0)
