# check_api.py
# Check a deployed API and its web page from the outside
# Course kit, module 4
#
# Topic: Deploying an API, and a smoke test that says plainly when it is down
#
# The lab asks for two live addresses: the API, a process that answers
# requests, and the page, a folder of built files a browser downloads. Each
# can fail on its own. This script calls both and prints one PASS or FAIL line
# per check: does /health answer 200 with JSON, does one data route return
# the documented shape, does a smoke test fail cleanly on a wrong address,
# does the page load, does the page name the API it calls, and does the API
# let that page read its answers (CORS). Checks C1 and C2 look inside your
# repo, so you run those by hand.
#
# No python packages to install: it uses only the standard library.
#
# Run it from this folder:
#   API_URL=https://your-server/your-api PAGE_URL=https://your-server/your-page python3 check_api.py
#   API_STUB=1 python3 check_api.py     # no server handy: a local stub stands in
# APP_URL is still read when PAGE_URL is not set, so older notes keep working.
# Settings you may change: DATA_ROUTE (default /greetings/en), DATA_KEYS (default lang,text).
# Exits 1 if any check fails.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import json  # for reading the JSON bodies
import re  # for finding the scripts a page loads
import os  # for the settings
import sys  # for the exit code
import threading  # for running the stub beside the checks
import urllib.parse  # for joining and splitting addresses
import urllib.request  # for calling the addresses
from http.server import BaseHTTPRequestHandler, HTTPServer  # for the stub server

## 0.2 Configuration #################################

STUB = os.getenv("API_STUB", "")
API_URL = os.getenv("API_URL", "")
PAGE_URL = os.getenv("PAGE_URL", "") or os.getenv("APP_URL", "")  # the static page
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
        elif self.path in ("/page", "/page/"):
            body, kind = '<html><body><div id="root"></div><script src="assets/index.js"></script></body></html>', "text/html"
        elif self.path == "/page/assets/index.js":
            # A built page carries its API address inside its JavaScript, in plain text.
            body, kind = f'const API_URL="{API_URL}";fetch(API_URL+"/health");', "text/javascript"
        else:
            self.send_response(404)
            self.end_headers()
            return
        raw = (body if isinstance(body, str) else json.dumps(body)).encode()
        self.send_response(200)
        self.send_header("Content-Type", kind)
        # A healthy API names the one page origin it allows, not "*".
        if self.headers.get("Origin"):
            self.send_header("Access-Control-Allow-Origin", self.headers.get("Origin"))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args):  # keep the check output to PASS and FAIL lines
        pass

if STUB:
    server = HTTPServer(("127.0.0.1", 0), Stub)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    API_URL = f"http://127.0.0.1:{server.server_port}"
    PAGE_URL = API_URL + "/page/"
    print(f"API_STUB is set: using a local stub at {API_URL}\n")
if not API_URL:
    sys.exit("API_URL is not set. Run: API_URL=https://your-server/your-api python3 check_api.py")
API_URL = API_URL.rstrip("/")

# 2. THE SMOKE TEST ###################################

# Call one address. Return (status, body) or (None, reason) when it cannot be reached.
def fetch(url, origin=None):
    status, body, _ = fetch_full(url, origin)
    return status, body

# The same call, keeping the answer's headers (the CORS check reads one).
def fetch_full(url, origin=None):
    req = urllib.request.Request(url, headers={"Origin": origin} if origin else {})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.read().decode("utf-8", "replace"), r.headers
    except urllib.error.HTTPError as e:
        return e.code, "", e.headers
    except Exception as e:
        return None, type(e).__name__, {}

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

# 4. THE PAGE ###################################

# The page is files, not a process: the server hands them over and the browser
# runs them. So "the page works" means two things a script can see: the files
# answer, and the JavaScript inside them names the live API, not localhost.
if PAGE_URL:
    page = PAGE_URL if PAGE_URL.endswith("/") or PAGE_URL.endswith(".html") else PAGE_URL + "/"
    status, html = fetch(page)
    report("PASS" if status == 200 else "FAIL", "C7 the page answers 200", f"got {status}")

    # Read the page and every script it loads, and look for the API's address.
    texts = [html]
    for src in re.findall(r'<script[^>]+src="([^"]+)"', html):
        _, js = fetch(urllib.parse.urljoin(page, src))
        texts.append(js)
    names_api = any(API_URL in t for t in texts)
    names_local = any(h in t for t in texts for h in ("127.0.0.1:8000", "localhost:8000"))
    report("PASS" if names_api else "FAIL", "C8 the page names its API",
           "found the API address" if names_api else
           ("it still calls localhost: rebuild with the live API address" if names_local else "API address not found"))

    # CORS: the browser only lets the page read the API's answer if the API says so.
    parts = urllib.parse.urlsplit(page)
    origin = f"{parts.scheme}://{parts.netloc}"
    _, _, headers = fetch_full(API_URL + "/health", origin=origin)
    allow = headers.get("Access-Control-Allow-Origin", "") if headers else ""
    if allow == origin:
        report("PASS", "C9 the API allows the page's origin", allow)
    elif allow == "*":
        report("PASS", "C9 the API allows the page's origin", "allows every origin: narrow it to the page")
    else:
        report("FAIL", "C9 the API allows the page's origin", f"Access-Control-Allow-Origin is '{allow}'")
else:
    for name in ("C7 the page answers 200", "C8 the page names its API", "C9 the API allows the page's origin"):
        report("SKIP", name, "PAGE_URL is not set")

print(f"\n{results.count('PASS')} passed, {results.count('FAIL')} failed, {results.count('SKIP')} skipped")
sys.exit(1 if "FAIL" in results else 0)
