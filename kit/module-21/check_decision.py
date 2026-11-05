# check_decision.py
# Check that DECISION.md is complete: a choice at each traffic level, the alternatives, the evidence
# Course kit, module 21
#
# Topic: APIs that sleep
#
# It checks completeness, not wisdom: a reviewer still reads whether each reason follows.
# A "Latency requirement:" line says, with a number, the wait your users can live with.
# Each traffic level needs its own heading, a "Choice:" line that names keep warm, scale to
# zero or something else (cache, queue, schedule, a fixed instance, a longer idle timeout),
# and an "Evidence:" line naming at least one field in cost.json or measurements.json, in
# backticks. A "## Host" section says which host (Connect or Fly.io), gives the measured cold
# start on each as "Connect <ms> ms, Fly.io <ms> ms" (both numbers must appear in
# measurements.json) and a "Why:" line. An "## Alternatives considered" section names at
# least two other options.
#   python3 check_decision.py DECISION.md cost.json measurements.json
#
# Uses only the Python standard library.

import json  # for the field names
import re  # for reading the headings
import sys  # for arguments and the exit code

LEVELS = ["100", "10,000", "100,000"]
OPTIONS = ["keep warm", "scale to zero", "cache", "queue", "schedule", "fixed instance", "another host",
           "idle timeout", "warm-up"]
CHOICE = "|".join(re.escape(o) for o in OPTIONS)


def numbers(obj, out):
    if isinstance(obj, dict):
        for v in obj.values():
            numbers(v, out)
    elif isinstance(obj, list):
        for v in obj:
            numbers(v, out)
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        out.add(float(obj))
    return out


def field_names(obj, out):
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.add(k)
            field_names(v, out)
    elif isinstance(obj, list):
        for v in obj:
            field_names(v, out)
    return out


def check(decision_path, cost_path, measurements_path):
    text = open(decision_path, encoding="utf-8").read()
    fields = field_names(json.load(open(cost_path)), set())
    measured = json.load(open(measurements_path))
    fields = field_names(measured, fields)
    values = numbers(measured, set())
    problems = []
    if not re.search(r"(?mi)^Latency requirement:.*\d", text):
        problems.append("no 'Latency requirement:' line with a number (the wait your users can live with)")
    sections = re.split(r"(?m)^## ", text)
    for level in LEVELS:
        body = next((s for s in sections if s.startswith(f"{level} requests a day")), None)
        if body is None:
            problems.append(f"no '## {level} requests a day' section")
            continue
        choice = re.search(r"(?mi)^Choice:\s*(" + CHOICE + r")\b", body)
        evidence = re.search(r"(?mi)^Evidence:(.*)$", body)
        cited = re.findall(r"`([A-Za-z_0-9]+)`", evidence.group(1)) if evidence else []
        if not choice:
            problems.append(f"{level}: no 'Choice:' line naming keep warm, scale to zero or another option")
        if not [c for c in cited if c in fields]:
            problems.append(f"{level}: Evidence names no field of cost.json or measurements.json")
    host = next((s for s in sections if s.startswith("Host")), None)
    if host is None:
        problems.append("no '## Host' section")
    else:
        if not re.search(r"(?mi)^Host:\s*(connect|fly\.io)", host):
            problems.append("Host: no 'Host: Connect' or 'Host: Fly.io' line")
        if not re.search(r"(?mi)^Why:\s*\S", host):
            problems.append("Host: no 'Why:' line")
        for name in ["Connect", "Fly.io"]:
            m = re.search(r"(?i)\b" + re.escape(name) + r"\s+(\d+(?:\.\d+)?)\s*ms", host)
            if not m:
                problems.append(f"Host: no measured cold start for {name} (write '{name} <number> ms')")
            elif not any(abs(float(m.group(1)) - v) < 1e-6 for v in values):
                problems.append(f"Host: {name} {m.group(1)} ms is not a number in measurements.json")
    alt = next((s for s in sections if s.lower().startswith("alternatives considered")), "")
    if sum(1 for o in OPTIONS if o in alt.lower()) < 2:
        problems.append("'## Alternatives considered' names fewer than two options")
    return problems


if __name__ == "__main__":
    found = check(*sys.argv[1:4])
    for p in found:
        print("  -", p)
    sys.exit(1 if found else 0)
