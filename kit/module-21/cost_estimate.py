# cost_estimate.py
# Turn your measurements and a host's published prices into a monthly bill at three traffic levels
# Pairs with cost_estimate.R
# Course kit, module 21
#
# Topic: APIs that sleep
#
# It reads measurements.json (what you measured) and prices.json (what the vendor pages
# say, each with its URL and the day you read it) and writes cost.json. It types no
# number of its own: run it twice on the same two files and cost.json is byte for byte
# the same, which is how the lab's check C7 knows nobody edited a figure by hand.
#
# Run it from your lab folder:
#   python3 cost_estimate.py
#
# Uses only the Python standard library.

# 0. SETUP ###################################

import hashlib  # for fingerprints of the two input files
import json  # for reading and writing
import math  # for the cold-start estimate
import os  # for paths
import sys  # for the exit code

MEASUREMENTS = os.environ.get("MEASUREMENTS", "measurements.json")
PRICES = os.environ.get("PRICES", "prices.json")
OUT = os.environ.get("OUT", "cost.json")
LEVELS = [100, 10000, 100000]  # requests a day: a class once a day, steady, busy
DAYS = 30

# 1. READ, AND REFUSE INCOMPLETE INPUTS ###################################


def load(path):
    with open(path, "rb") as f:
        raw = f.read()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()[:16]


m, m_sha = load(MEASUREMENTS)
p, p_sha = load(PRICES)

needed = ["cold_median_ms", "warm_median_ms", "idle_timeout_s", "memory_gb", "vcpu", "model_calls_per_request"]
missing = [k for k in needed if k not in m]
if missing:
    sys.exit(f"measurements.json is missing {missing}. Measure first, then write memory_gb, vcpu and model_calls_per_request in.")

priced = list(p["hosts"].items()) + [("model", p["model"])]
for name, entry in priced:
    if not str(entry.get("source_url", "")).startswith("https://") or not entry.get("accessed"):
        sys.exit(f"prices.json: '{name}' needs a source_url (https://) and an accessed date.")


def price(entry, key):
    """A number, or None when the price is 'see vendor page'."""
    v = entry.get(key)
    return v if isinstance(v, (int, float)) else None


# 2. HOW MANY REQUESTS ARE COLD ###################################

# If requests arrive at random, the chance that the gap before one is longer than the
# idle timeout is exp(-idle_timeout / mean_gap). Those requests meet a cold start.
# This is an assumption about your traffic, and cost.json says so.


def level_row(per_day):
    per_month = per_day * DAYS
    mean_gap_s = 86400 / per_day
    cold_fraction = math.exp(-m["idle_timeout_s"] / mean_gap_s)
    cold_starts = per_month * cold_fraction
    gb_s = per_month * (m["warm_median_ms"] / 1000) * m["memory_gb"]
    vcpu_s = per_month * (m["warm_median_ms"] / 1000) * m["vcpu"]
    cold_gb_s = cold_starts * (m["cold_median_ms"] / 1000) * m["memory_gb"]
    model_calls = per_month * m["model_calls_per_request"]

    # 3. THE HOST BILL ###################################

    host_cost, fixed_host = {}, {}
    for name, h in p["hosts"].items():
        if h.get("kind") == "fixed":
            fixed_host[name] = price(h, "fixed_month_usd")
        elif h.get("kind") == "per_request":
            per_req, per_gb_s = price(h, "price_per_million_requests_usd"), price(h, "price_per_gb_s_usd")
            billed_gb_s = gb_s + (cold_gb_s if h.get("bills_cold_start") else 0)
            # Some hosts bill vCPU-seconds as well as memory; the rest leave the key out.
            per_vcpu_s = price(h, "price_per_vcpu_s_usd") if "price_per_vcpu_s_usd" in h else 0
            if per_req is None or per_gb_s is None or per_vcpu_s is None:
                host_cost[name] = None  # a price we could not read: see the vendor page
            else:
                host_cost[name] = round(
                    max(0, per_month - h["free_requests_month"]) / 1e6 * per_req
                    + max(0, billed_gb_s - h["free_gb_s_month"]) * per_gb_s
                    + max(0, vcpu_s - h.get("free_vcpu_s_month", 0)) * per_vcpu_s, 2)

    # 4. THE MODEL BILL, WHICH SCALE TO ZERO DOES NOT TOUCH ###################################

    per_call = price(p["model"], "price_per_model_call_usd")
    model_cost = None if per_call is None else round(model_calls * per_call, 2)

    return {
        "requests_day": per_day,
        "requests_month": per_month,
        "mean_gap_s": round(mean_gap_s, 3),
        "cold_fraction": round(cold_fraction, 4),
        "cold_starts_month": round(cold_starts),
        "gb_s_month": round(gb_s, 1),
        "vcpu_s_month": round(vcpu_s, 1),
        "cold_gb_s_month": round(cold_gb_s, 1),
        "model_calls_month": round(model_calls),
        "host_cost": host_cost,
        "fixed_host": fixed_host,
        "model_cost": model_cost,
    }


# 5. WRITE cost.json ###################################

cost = {
    "made_by": "cost_estimate.py",
    "inputs": {"measurements_sha256": m_sha, "prices_sha256": p_sha, "example": bool(m.get("example"))},
    "assumptions": {
        "days_per_month": DAYS,
        "arrivals": "random (Poisson): cold_fraction = exp(-idle_timeout_s / mean_gap_s)",
        "memory_gb": m["memory_gb"],
        "vcpu": m["vcpu"],
        "model_calls_per_request": m["model_calls_per_request"],
        "left_out": "idle billing, network transfer, storage",
    },
    # Keeping one process warm all month holds this much memory whether or not anyone calls.
    "keep_warm": {"processes": 1, "memory_gb_hours_month": round(m["memory_gb"] * 24 * DAYS, 1)},
    "levels": [level_row(n) for n in LEVELS],
}
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    json.dump(cost, f, indent=2, sort_keys=True)
    f.write("\n")

for row in cost["levels"]:
    print(f"{row['requests_day']:>7} a day: cold fraction {row['cold_fraction']}, host {row['host_cost']}, "
          f"fixed {row['fixed_host']}, model calls {row['model_calls_month']}, model cost {row['model_cost']}")
print(f"wrote {OUT}")
