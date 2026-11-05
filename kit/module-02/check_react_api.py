# check_react_api.py
# The lab's live checks: does the API answer, and does the page keep its secrets?
# Course kit, module 02
#
# Topic: Checking a React page over an API
#
# This script checks the two halves of the lab app from the outside. For the API: the
# health route answers 200 with JSON, the data route returns rows, and the data route
# carries a CORS header, so a page on another origin is allowed to read it. For the page:
# one file in web/src reads the API address from VITE_API_URL, and the built page in
# web/dist holds no key-shaped string. Whether the page shows the rows, and what it does
# when the API is down, are for a person to see in a browser; this script says so at the end.
#
# Run it from this folder:
#   API_URL=http://127.0.0.1:8000 WEB_DIR=path/to/your/web python3 check_react_api.py
#   APP_STUB=1 python3 check_react_api.py     # no app handy: a local stub API and example/web
#   APP_STUB=bad python3 check_react_api.py   # a stub broken on purpose, to show FAIL
# Prints one PASS or FAIL line per check and exits 1 if any check fails.
# Standard library only: nothing to install.

# 0. SETUP ###################################

import json  # for reading the API's answers
import os  # for the settings in the environment
import re  # for finding key patterns and the variable name
import sys  # for the exit code
import threading  # for running the stub beside the checks
import urllib.error  # for reading an error answer
import urllib.request  # for asking the API
from http.server import BaseHTTPRequestHandler, HTTPServer  # for the stub server
from pathlib import Path  # for paths that work on every system

## 0.1 Settings #################################

STUB = os.getenv("APP_STUB", "")
DATA_ROUTE = os.getenv("DATA_ROUTE", "/rows")  # the route that returns rows
ORIGIN = "http://localhost:5173"  # where a Vite page runs on a laptop; the browser sends this
KEY_PATTERNS = [  # shapes that real keys take; the same list as check_contract.py
    r"sk-[A-Za-z0-9_-]{16,}",
    r"AIza[0-9A-Za-z_-]{20,}",
    r"(?i)(api[_-]?key|token|secret)\s*[=:]\s*['\"]?[A-Za-z0-9_-]{16,}",
]

results = []
def check(name, ok, detail=""):
    # One PASS or FAIL line per check; the detail only shows when it fails.
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))

# 1. THE STUB (ONLY IF ASKED) ###################################

# The stub answers the way a healthy API would. It is a fixture for this script,
# not an API to copy: the real one is yours, in Plumber or FastAPI.
class Stub(BaseHTTPRequestHandler):
    def do_GET(self):
        bad = STUB == "bad"
        if self.path == "/health":
            body, kind = ("ok", "text/plain") if bad else (json.dumps({"status": "ok"}), "application/json")
        elif self.path == DATA_ROUTE:
            body, kind = json.dumps([{"name": "Luke Skywalker", "height": 172}]), "application/json"
        else:
            self.send_response(404); self.end_headers(); return
        self.send_response(200)
        self.send_header("Content-Type", kind)
        if not bad:
            self.send_header("Access-Control-Allow-Origin", "*")  # the header CORS asks for
        self.end_headers()
        self.wfile.write(body.encode())
    def log_message(self, *args):
        pass  # keep the check's output to one line per check

if STUB:
    server = HTTPServer(("127.0.0.1", 0), Stub)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    API_URL = f"http://127.0.0.1:{server.server_port}"
    WEB_DIR = Path(__file__).parent / ("example_bad/web" if STUB == "bad" else "example/web")
    print(f"APP_STUB={STUB}: a stub API at {API_URL}, and the page in {WEB_DIR.parent.name}/web of the kit")
else:
    API_URL = os.getenv("API_URL", "").rstrip("/")
    WEB_DIR = Path(os.getenv("WEB_DIR", "web"))
    if not API_URL:
        print("FAIL  A0 API_URL is not set: start your API, then set API_URL to its address")
        sys.exit(1)

def ask(path):
    # Ask the API one question, sending an Origin the way a browser would.
    req = urllib.request.Request(API_URL + path, headers={"Origin": ORIGIN})
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            return res.status, dict(res.headers), res.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), ""
    except OSError as e:
        return 0, {}, str(e)

def as_json(text):
    try:
        return json.loads(text)
    except ValueError:
        return None

# 2. THE API ###################################

status, headers, body = ask("/health")
check("A1 /health answers 200 with JSON", status == 200 and as_json(body) is not None,
      f"status {status}, body starts {body[:40]!r}")
status, headers, body = ask(DATA_ROUTE)
rows = as_json(body)
check(f"A2 {DATA_ROUTE} answers 200 with at least one row", status == 200 and
      isinstance(rows, list) and len(rows) > 0, f"status {status}")
cors = {k.lower(): v for k, v in headers.items()}.get("access-control-allow-origin", "")
check(f"A3 {DATA_ROUTE} carries an Access-Control-Allow-Origin header (CORS)",
      cors in ("*", ORIGIN), "no header: a page on another origin cannot read this answer")

# 3. THE PAGE ###################################

# The address lives in one file, read from VITE_API_URL, so it can change without
# editing the page. After a build the name is gone: Vite pastes the value in its place.
src = [p for p in (WEB_DIR / "src").rglob("*") if p.is_file()] if (WEB_DIR / "src").is_dir() else []
readers = [p.name for p in src if "VITE_API_URL" in p.read_text(encoding="utf-8", errors="replace")]
check("W1 exactly one file in web/src reads VITE_API_URL", len(readers) == 1,
      f"found in {len(readers)} files: {', '.join(readers) or 'none'}")

# Anything named VITE_ is printed into the public JavaScript. A key there is a leaked key.
dist = WEB_DIR / "dist"
index = dist / "index.html"
built = [p for p in dist.rglob("*") if p.is_file()] if dist.is_dir() else []
leaks = [p.name for p in built
         if any(re.search(k, p.read_text(encoding="utf-8", errors="replace")) for k in KEY_PATTERNS)]
check("W2 the built page (web/dist) exists and holds no key-shaped string",
      index.is_file() and not leaks, "no dist/index.html: run npm run build" if not index.is_file()
      else "in: " + ", ".join(leaks))

# 4. SUMMARY ###################################

print(f"{sum(results)} of {len(results)} live checks pass.")
print("A person checks the rest in a browser: the page shows the rows (lab check 2), and with "
      "the API stopped it shows a message instead of going blank (3).")
sys.exit(0 if all(results) else 1)
