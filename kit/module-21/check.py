# check.py
# The lab's nine checks: does your API behave when it sleeps, and is the decision backed?
# Course kit, module 21
#
# Topic: APIs that sleep
#
# Run it from your lab folder (the one with measurements.json, prices.json, cost.json and
# DECISION.md), with API_URL set to your deployed API. No model and no key are needed.
#   API_URL=https://connect.example.com/content/abc python3 check.py
# CHECK_STUB=1 runs every check on the kit's example files against stub_host.py.
# CHECK_STUB=broken does the same with a broken host and a hand-edited cost.json, so you
# can see the checks fail.
#
# Uses only the Python standard library. It works on a scratch copy of your files.

# 0. SETUP ###################################

import json
import re  # for the files and the answers
import os  # for paths and settings
import shutil  # for the scratch copy
import statistics  # for the median
import subprocess  # for rerunning cost_estimate
import sys  # for the exit code
import tempfile  # for a scratch folder
import urllib.error  # for failed requests
import urllib.request  # for HTTP requests
import uuid  # for an idempotency key
from datetime import datetime  # for the ISO date check

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_decision  # the decision file check, C9

MODE = os.environ.get("CHECK_STUB", "")
LAB = os.path.join(HERE, "example") if MODE else os.getcwd()
API_URL = os.environ.get("API_URL", "").rstrip("/")
results = []


def report(status, label, why=""):
    results.append(status)
    print(f"{status}  {label}" + (f"  ({why})" if why else ""))


if MODE:
    os.environ["STUB_BROKEN"] = "1" if MODE == "broken" else ""
    import stub_host  # the pretend host
    stub_host.BROKEN = MODE == "broken"
    stub_host.serve(8779)
    API_URL = "http://127.0.0.1:8779"

for name in ["measurements.json", "prices.json", "cost.json", "DECISION.md"]:
    if not os.path.exists(os.path.join(LAB, name)):
        sys.exit(f"{name} not found in {LAB}. Run this from your lab folder.")

work = tempfile.mkdtemp(prefix="m21-check-")
for name in ["measurements.json", "prices.json", "cost.json", "DECISION.md"]:
    shutil.copy(os.path.join(LAB, name), work)
if MODE == "broken":
    # A hand-typed figure: the kind of edit C7 exists to catch.
    c = json.load(open(os.path.join(work, "cost.json")))
    c["levels"][0]["fixed_host"] = {"digitalocean_fixed": 0}
    json.dump(c, open(os.path.join(work, "cost.json"), "w"), indent=2, sort_keys=True)
    # A decision with no latency requirement and a host cold start that was never measured: what C9 exists to catch.
    d = open(os.path.join(work, "DECISION.md"), encoding="utf-8").read()
    d = re.sub(r"(?m)^Latency requirement:.*\n", "", d).replace("Fly.io 1180 ms", "Fly.io 999 ms")
    open(os.path.join(work, "DECISION.md"), "w", encoding="utf-8").write(d)
m = json.load(open(os.path.join(work, "measurements.json")))
p = json.load(open(os.path.join(work, "prices.json")))
timeout = float(m.get("client_timeout_s") or 30)


def call(method, path, headers=None):
    req = urllib.request.Request(API_URL + path, method=method, headers=headers or {}, data=b"" if method == "POST" else None)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, {}
    except Exception as e:
        return 0, {"error": str(e)}

# 1. THE MEASUREMENTS ###################################


cold, warm = m.get("cold_ms", []), m.get("warm_ms", [])
try:
    datetime.fromisoformat(str(m.get("measured_at", "")).replace("Z", "+00:00"))
    iso = True
except ValueError:
    iso = False
ok = len(cold) >= 3 and len(warm) >= 20 and all(x > 0 for x in cold + warm) and iso
report("PASS" if ok else "FAIL", "C1 measurements.json has 3 cold trials, 20 warm requests and a measured_at",
       "" if ok else f"{len(cold)} cold, {len(warm)} warm, measured_at ISO: {iso}")

ok = bool(cold and warm) and statistics.median(cold) > statistics.median(warm)
report("PASS" if ok else "FAIL", "C2 the cold median is slower than the warm median",
       "" if ok else "a cold trial that is not slower means the wait was shorter than the idle timeout")

# 2. THE LIVE API ###################################

if not API_URL:
    for label in ["C3 /health answers", "C4 the chosen fix works"]:
        report("SKIP", label, "API_URL not set")
else:
    status, body = call("GET", "/health")
    ok = status == 200 and body.get("ok") is True and isinstance(body.get("version"), str)
    report("PASS" if ok else "FAIL", "C3 /health answers 200 with ok and a version, within the client timeout",
           "" if ok else f"status {status}, body {body}")

    status, body = call("GET", "/predict_cached")
    if status == 200 and "made_at" in body:
        ok, how = True, "cached route with made_at"
    else:
        key = uuid.uuid4().hex
        s1, b1 = call("POST", "/jobs", {"Idempotency-Key": key})
        s2, b2 = call("POST", "/jobs", {"Idempotency-Key": key})
        ok = s1 == 202 and s2 == 202 and b1.get("id") and b1.get("id") == b2.get("id")
        how = "job route" if ok else f"no cached route; job route gave {s1}/{s2}, ids {b1.get('id')} and {b2.get('id')}"
    report("PASS" if ok else "FAIL", "C4 the chosen fix works (a cached route with made_at, or a repeat job finds the first)", how)

ok = "client_timeout_s" in m and (m["client_timeout_s"] <= 30 or m.get("route", "").startswith("/jobs"))
report("PASS" if ok else "FAIL", "C5 a client timeout is set, and is 30 s or less unless it covers the job route")

# 3. PRICES AND THE BILL ###################################

entries = list(p.get("hosts", {}).items()) + [("model", p.get("model", {}))]
bad = [n for n, e in entries if not str(e.get("source_url", "")).startswith("https://") or not e.get("accessed")]
report("PASS" if not bad else "FAIL", "C6 every price in prices.json has a source_url and an accessed date", ", ".join(bad))

made_by = json.load(open(os.path.join(work, "cost.json"))).get("made_by", "cost_estimate.py")
before = open(os.path.join(work, "cost.json"), "rb").read()
cmd = (["Rscript", os.path.join(HERE, "cost_estimate.R")] if made_by.endswith(".R")
       else [sys.executable, os.path.join(HERE, "cost_estimate.py")])
run = subprocess.run(cmd, cwd=work, capture_output=True, text=True,
                     env={**os.environ, "OUT": "cost.rerun.json"})
after = open(os.path.join(work, "cost.rerun.json"), "rb").read() if run.returncode == 0 else b""
report("PASS" if before == after else "FAIL", "C7 rerunning cost_estimate on the committed inputs gives the same cost.json",
       "" if before == after else "cost.json differs from a fresh run: a number was typed or an input changed")

cost = json.loads(before)
levels = {row.get("requests_day"): row for row in cost.get("levels", [])}
ok = all(n in levels and all(k in levels[n] for k in ["host_cost", "model_cost", "fixed_host"]) for n in [100, 10000, 100000])
load = m.get("load", {})
odd = [r for r in load.get("requests", []) if (r["status"] >= 500 and r["status"] != 503)
       or (r["status"] in (429, 503) and not r.get("retry_after"))]
explained = load.get("explained", {})
ok = ok and bool(load) and all(str(r["status"]) in explained for r in odd)
report("PASS" if ok else "FAIL", "C8 cost.json has all three traffic levels, and every odd load result is explained",
       "" if ok else "missing a level or a field, no load block, or an unexplained 5xx")

problems = check_decision.check(os.path.join(work, "DECISION.md"), os.path.join(work, "cost.json"),
                                os.path.join(work, "measurements.json"))
report("PASS" if not problems else "FAIL", "C9 DECISION.md: a choice at each level, the alternatives, and the evidence named",
       "; ".join(problems))

shutil.rmtree(work, ignore_errors=True)
print(f"\n{results.count('PASS')} passed, {results.count('FAIL')} failed, {results.count('SKIP')} skipped")
sys.exit(1 if "FAIL" in results else 0)
