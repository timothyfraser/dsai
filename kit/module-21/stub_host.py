# stub_host.py
# A pretend host that puts an API to sleep, so the measurements and checks run without a server
# Course kit, module 21
#
# Topic: APIs that sleep
#
# This is a tiny API that behaves like a scale-to-zero host. After IDLE_TIMEOUT_S seconds
# with no request, it "stops the process": the next request pays COLD_MS of start-up,
# the way a real host pays for booting Python and loading a model. It has the routes the
# lab asks for: /health, /predict, /predict_cached and /jobs.
#
# It is a fixture for practice and for check.py. Numbers measured against it describe the
# stub, not any real host.
#   python3 stub_host.py --port 8765
#   STUB_BROKEN=1 python3 stub_host.py --port 8765   # health with no version, jobs not idempotent
#
# Uses only the Python standard library.

# 0. SETUP ###################################

import argparse  # for the --port option
import json  # for JSON answers
import os  # for settings
import threading  # for the lock around shared state
import time  # for the idle clock and the pretend start-up
import uuid  # for job ids
from datetime import datetime, timezone  # for made_at stamps
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer  # for the server

IDLE_TIMEOUT_S = float(os.environ.get("STUB_IDLE_TIMEOUT_S", "1"))
COLD_MS = float(os.environ.get("STUB_COLD_MS", "400"))
WARM_MS = float(os.environ.get("STUB_WARM_MS", "20"))
CACHE_TTL_S = 3600
BROKEN = os.environ.get("STUB_BROKEN", "") not in ("", "0")
VERSION = "stub-1"

# 1. THE PROCESS THAT GOES TO SLEEP ###################################

# Everything in this dictionary lives in memory, so a "stop" wipes it,
# exactly like the stop switch in a real API that a host puts to sleep.
state = {"last_request": None, "jobs": {}, "keys": {}}
lock = threading.Lock()


def wake_if_asleep():
    """Pay the cold start if the pretend process was stopped."""
    with lock:
        now = time.monotonic()
        asleep = state["last_request"] is None or now - state["last_request"] > IDLE_TIMEOUT_S
        if asleep:
            # The host stopped the process: memory is gone.
            state["jobs"], state["keys"] = {}, {}
        state["last_request"] = now
    time.sleep((COLD_MS if asleep else WARM_MS) / 1000)
    with lock:
        state["last_request"] = time.monotonic()
    return asleep


def stamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# 2. THE ROUTES ###################################

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # quiet: the measurement scripts print what matters

    def answer(self, code, body, headers=None):
        data = json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        cold = wake_if_asleep()
        path = self.path.split("?")[0]
        if path == "/health":
            # The health route touches nothing slow: no model, no database.
            body = {"ok": True, "cold": cold}
            if not BROKEN:
                body["version"] = VERSION
            return self.answer(200, body)
        if path == "/predict":
            return self.answer(200, {"predicted_vehicle_count": 42.0, "cold": cold})
        if path == "/predict_cached":
            return self.answer(200, {"predicted_vehicle_count": 42.0, "made_at": stamp(),
                                     "ttl_s": CACHE_TTL_S, "source": "cache"})
        if path.startswith("/jobs/"):
            job = state["jobs"].get(path.split("/")[-1])
            if job is None:
                return self.answer(404, {"error": "no such job (the process may have slept)"})
            return self.answer(200, job)
        return self.answer(404, {"error": "not found"})

    def do_POST(self):
        wake_if_asleep()
        if self.path.split("?")[0] != "/jobs":
            return self.answer(404, {"error": "not found"})
        key = self.headers.get("Idempotency-Key", "")
        with lock:
            # A repeat with the same key finds the first job instead of starting a second.
            if key and key in state["keys"] and not BROKEN:
                job_id = state["keys"][key]
            else:
                job_id = uuid.uuid4().hex[:12]
                state["jobs"][job_id] = {"id": job_id, "status": "queued"}
                if key:
                    state["keys"][key] = job_id
        return self.answer(202, {"id": job_id, "status_url": f"/jobs/{job_id}"})


# 3. RUN ###################################

def serve(port):
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    print(f"stub host on http://127.0.0.1:{args.port} (idle timeout {IDLE_TIMEOUT_S} s)", flush=True)
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
