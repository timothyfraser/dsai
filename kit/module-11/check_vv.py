# check_vv.py
# Run a team's V&V plan: read checks.yaml, run every machine check it lists
# Course kit, module 11
#
# Topic: Verification and validation (V&V) for AI systems
#
# A requirement you cannot check is a wish. This script reads your checks.yaml,
# runs your system once, and then runs each listed check against what the system
# wrote, one PASS or FAIL line per check. Then it runs the lab's own checks
# (C1 to C6) on the plan itself: is every check traced to a requirement, is the
# human sample big enough, and can your checks fail at all?
#
# If you haven't already, install these packages...
# pip install pyyaml
#
# Run it from the folder that holds your checks.yaml:
#   VV_STUB=1 python3 check_vv.py checks.yaml     # no model: check the outputs already on disk
#   python3 check_vv.py checks.yaml               # run your system first, then check
#   VV_STUB=bad python3 check_vv.py checks.yaml   # check the outputs you broke on purpose
# Exits 1 if any check fails.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import csv  # for reading the requirements, risks and ratings tables
import json  # for reading one output record per line
import os  # for the VV_STUB switch
import re  # for the forbidden-pattern check
import subprocess  # for running your system once
import sys  # for the exit code
from pathlib import Path  # for paths relative to checks.yaml

try:
    import yaml  # for reading checks.yaml
except ImportError:
    sys.exit("PyYAML is not installed. Run: pip install pyyaml")

## 0.2 Configuration #################################

STUB = os.getenv("VV_STUB", "")  # "", "1" or "bad"
MIN_CHECKS = 5        # the lab asks for at least five machine checks
MIN_HUMAN_SAMPLE = 10  # the lab asks for at least ten human-rated items
MIN_RISKS = 3          # the lab asks for at least three residual risks
KNOWN_TYPES = ["schema", "golden", "forbid_pattern", "refusal", "agreement", "max_words"]

## 0.3 Find the Plan #################################

plan_path = Path(sys.argv[1] if len(sys.argv) > 1 else "checks.yaml")
if not plan_path.exists():
    sys.exit(f"Cannot find {plan_path}. Run this from the folder that holds your checks.yaml.")
HERE = plan_path.resolve().parent
plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))

def read_csv(name):
    with open(HERE / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def read_jsonl(name):
    lines = (HERE / name).read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]

results = []
def report(status, name, detail=""):
    results.append(status)
    print(f"{status}  {name}" + (f"  ({detail})" if detail else ""))

# 1. RUN THE SYSTEM ONCE ###################################

# In stub mode we never call your system, so this runs anywhere, with no model.
system = plan["system"]
if STUB == "":
    print(f"Running your system: {system['run']}")
    proc = subprocess.run(system["run"], shell=True, cwd=HERE)
    if proc.returncode != 0:
        sys.exit(f"FAIL  your system exited with code {proc.returncode}; nothing to check")
outputs_file = system["bad_outputs"] if STUB == "bad" else system["outputs"]
print(f"Checking {outputs_file}\n")

# 2. THE MACHINE CHECKS ###################################

# Each function takes the output records and one check from checks.yaml,
# and returns (passed, detail). One requirement, one function, one line of output.

## 2.1 Schema: every record has the fields, with the types and ranges ####

TYPES = {"str": str, "int": int, "bool": bool, "float": (int, float)}

def check_schema(rows, c):
    bad = []
    for row in rows:
        for field, kind in c["fields"].items():
            value = row.get(field)
            # bool is a kind of int in Python, so test it on its own.
            wrong_type = value is None or (kind == "int" and isinstance(value, bool)) \
                or not isinstance(value, TYPES[kind])
            if wrong_type:
                bad.append(f"{row.get('id', '?')}:{field}")
        for field, (low, high) in c.get("ranges", {}).items():
            value = row.get(field)
            if isinstance(value, (int, float)) and not (low <= value <= high):
                bad.append(f"{row.get('id', '?')}:{field}={value}")
    return not bad, f"{len(bad)} problems: {bad[:5]}" if bad else f"{len(rows)} records"

## 2.2 Golden set: known inputs, known facts the answer must state #######

def check_golden(rows, c):
    by_id = {row.get("id"): row for row in rows}
    golden = read_csv(c["file"])
    hits = [g["id"] for g in golden
            if g["id"] in by_id and g["must_contain"] in str(by_id[g["id"]].get(c["field"], ""))]
    rate = len(hits) / max(len(golden), 1)
    missed = [g["id"] for g in golden if g["id"] not in hits]
    return rate >= c["min_rate"], f"{len(hits)} of {len(golden)} golden items" + (f", missed {missed}" if missed else "")

## 2.3 Forbidden pattern: words the requirement rules out #################

def check_forbid_pattern(rows, c):
    hits = [row.get("id") for row in rows if re.search(c["pattern"], str(row.get(c["field"], "")), re.IGNORECASE)]
    return not hits, f"found in {hits}" if hits else f"none in {len(rows)} records"

## 2.4 Refusal: the system says no when it should #########################

def check_refusal(rows, c):
    cases = [row for row in rows if all(row.get(k) == v for k, v in c["when"].items())]
    # A refusal test with no cases proves nothing, so it fails.
    if not cases:
        return False, "no records match 'when', so nothing was tested"
    missed = [row.get("id") for row in cases if row.get("refused") is not True]
    return not missed, f"{len(cases) - len(missed)} of {len(cases)} refused" + (f", not refused {missed}" if missed else "")

## 2.5 Agreement: does the AI judge rate the way a person does? ###########

def check_agreement(rows, c):
    human = {h["id"]: float(h[c["field"]]) for h in read_csv(c["human"])}
    judge = {j["id"]: float(j[c["field"]]) for j in read_csv(c["judge"])}
    shared = [i for i in human if i in judge]
    if len(shared) < c["min_n"]:
        return False, f"only {len(shared)} items rated by both; need {c['min_n']}"
    close = [i for i in shared if abs(human[i] - judge[i]) <= c["tolerance"]]
    exact = [i for i in shared if human[i] == judge[i]]
    rate = len(close) / len(shared)
    apart = [i for i in shared if i not in close]
    detail = f"within {c['tolerance']} on {len(close)} of {len(shared)} ({rate:.0%}), exact on {len(exact)}"
    return rate >= c["min_rate"], detail + (f", apart on {apart}" if apart else "")

## 2.6 Length: a plain limit a reader can feel ###########################

def check_max_words(rows, c):
    long = [row.get("id") for row in rows if len(str(row.get(c["field"], "")).split()) > c["limit"]]
    return not long, f"over {c['limit']} words: {long}" if long else f"all {len(rows)} within {c['limit']} words"

CHECKS = {"schema": check_schema, "golden": check_golden, "forbid_pattern": check_forbid_pattern,
          "refusal": check_refusal, "agreement": check_agreement, "max_words": check_max_words}

def run_checks(rows, quiet=False):
    outcome = {}
    for c in plan["checks"]:
        if c.get("type") not in CHECKS:
            outcome[c["id"]] = False
            if not quiet:
                report("FAIL", f"{c['id']} unknown check type '{c.get('type')}'")
            continue
        ok, detail = CHECKS[c["type"]](rows, c)
        outcome[c["id"]] = ok
        if not quiet:
            report("PASS" if ok else "FAIL", f"{c['id']} {c['type']} ({c['requirement']})", detail)
    return outcome

print("Machine checks, from checks.yaml:")
outcome = run_checks(read_jsonl(outputs_file))

# 3. THE LAB CHECKS: IS THE PLAN ITSELF SOUND? ###################################

print("\nLab checks, on the plan itself:")
reqs = read_csv(plan["requirements"])
req_ids = {r["id"] for r in reqs}

# C1: a requirements table, each row with a kind and an acceptance criterion.
bad = [r.get("id") for r in reqs if r.get("kind") not in ("verification", "validation")
       or not str(r.get("acceptance", "")).strip()]
report("PASS" if len(reqs) >= MIN_CHECKS and not bad else "FAIL",
       "C1 requirements table: each row has a kind and an acceptance criterion",
       f"{len(reqs)} rows" + (f", incomplete {bad}" if bad else ""))

# C2: at least five machine checks, each traced to a requirement that exists.
untraced = [c["id"] for c in plan["checks"] if c.get("requirement") not in req_ids]
report("PASS" if len(plan["checks"]) >= MIN_CHECKS and not untraced else "FAIL",
       f"C2 at least {MIN_CHECKS} machine checks, each traced to a requirement",
       f"{len(plan['checks'])} checks" + (f", untraced {untraced}" if untraced else ""))

# C3: every machine check passes on the system's real outputs.
failed = [k for k, ok in outcome.items() if not ok]
report("PASS" if not failed else "FAIL", "C3 every machine check passes",
       f"failing {failed}" if failed else f"{len(outcome)} of {len(outcome)}")

# C4: a human-rated sample, big enough, compared with the AI judge.
agree = [c for c in plan["checks"] if c.get("type") == "agreement"]
n = len(read_csv(agree[0]["human"])) if agree else 0
report("PASS" if agree and n >= MIN_HUMAN_SAMPLE else "FAIL",
       f"C4 at least {MIN_HUMAN_SAMPLE} human-rated items compared with the judge",
       f"{n} items" if agree else "no agreement check in checks.yaml")

# C5: a residual-risk list: what the checks cannot see, and who watches it.
risks = read_csv(plan["risks"])
thin = [i + 1 for i, r in enumerate(risks)
        if not all(str(r.get(k, "")).strip() for k in ("risk", "why_the_checks_miss_it", "mitigation", "owner"))]
report("PASS" if len(risks) >= MIN_RISKS and not thin else "FAIL",
       f"C5 at least {MIN_RISKS} residual risks, each with a mitigation and an owner",
       f"{len(risks)} risks" + (f", incomplete rows {thin}" if thin else ""))

# C6: the checks can fail. A check that passes on broken outputs is not a check.
caught = [k for k, ok in run_checks(read_jsonl(system["bad_outputs"]), quiet=True).items() if not ok]
report("PASS" if caught else "FAIL", "C6 the broken outputs fail at least one machine check",
       f"caught by {caught}" if caught else "every check passed on outputs you broke on purpose")

# 4. RESULT ###################################

print(f"\n{results.count('PASS')} passed, {results.count('FAIL')} failed")
sys.exit(1 if "FAIL" in results else 0)
