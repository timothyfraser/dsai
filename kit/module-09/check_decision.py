# check_decision.py
# Check that DECISION.md is complete, and that its parts agree with each other
# Course kit, module 9
#
# Topic: Pipelines and cron
#
# The lab asks your team to decide how its pipeline runs while nobody watches:
# how often the ingest fires, what makes the model retrain, what runs the
# schedule, and who is paged when a run fails. This script reads that decision,
# DECISION.md, and checks that it is complete and that it agrees with itself:
# the schedule is fresh enough for the need you wrote, a drift threshold sits
# above the error your run recorded, and a person is named. It cannot tell you
# whether the decision is wise. A reviewer reads the reason.
#
# Run it:
#   python3 check_decision.py path/to/DECISION.md          # check your decision
#   python3 check_decision.py DECISION.md data/model.json  # also compare test_rmse with your model file
#   DECISION_STUB=1 python3 check_decision.py              # the saved example, which passes
#   DECISION_STUB=bad python3 check_decision.py            # broken on purpose, to show FAIL
# Exits 1 if any check fails.
#
# Uses only the Python standard library.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import json  # for reading your model file
import os  # for the stub switch
import re  # for pulling lines and numbers out of the text
import sys  # for arguments and the exit code
from pathlib import Path  # for paths beside this script

## 0.2 Configuration #################################

HERE = Path(__file__).resolve().parent
STUB = os.environ.get("DECISION_STUB", "")  # "", "1" or "bad"
SECTIONS = ["schedule", "retrain trigger", "alternatives", "reason", "evidence", "paged", "finale"]
RUNNERS = ["cron", "github actions", "posit connect", "event", "orchestrator"]
TRIGGERS = ["clock", "drift", "never"]
COLUMNS = ["cost", "freshness", "noticed", "failure", "owner", "staleness"]
ARTEFACTS = ["data/model.json", "data/validation.json", "data/agent_answer.txt", "check output"]

## 0.3 Find the File #################################

if STUB == "1":
    PATH = HERE / "example" / "DECISION.md"
elif STUB == "bad":
    PATH = HERE / "example_bad" / "DECISION.md"
else:
    PATH = Path(sys.argv[1] if len(sys.argv) > 1 else "DECISION.md")
MODEL_PATH = None if STUB else (sys.argv[2] if len(sys.argv) > 2 else None)

if not PATH.exists():
    print(f"FAIL  no file at {PATH}: copy example/DECISION.md and fill it in")
    sys.exit(1)
text = PATH.read_text(encoding="utf-8")


# 1. SPLIT THE TEXT INTO SECTIONS #################################

def sections_of(md):
    """Return {lowercased heading: body} for every '## ' heading."""
    found, name = {}, None
    for line in md.splitlines():
        if line.startswith("## "):
            name = line[3:].strip().lower()
            found[name] = ""
        elif name:
            found[name] += line + "\n"
    return found


def line_value(body, label):
    """The text after 'Label:' at the start of a line, or ''."""
    m = re.search(rf"^{label}:[ \t]*(.+)$", body, re.MULTILINE | re.IGNORECASE)
    return m.group(1).strip() if m else ""


def number_in(value):
    m = re.search(r"-?\d+(?:\.\d+)?", value or "")
    return float(m.group(0)) if m else None


def runs_per_field(field, span):
    """How many values a cron field takes in its span: '*' is all, '*/n' is span/n, '1,5' is 2."""
    if field == "*":
        return span
    if field.startswith("*/") and field[2:].isdigit() and int(field[2:]) > 0:
        return span / int(field[2:])
    count = 0
    for part in field.split(","):
        if re.fullmatch(r"\d+-\d+", part):
            a, b = (int(x) for x in part.split("-"))
            count += max(0, b - a + 1)
        elif part.isdigit():
            count += 1
        else:
            return None
    return count


def hours_between_runs(cron):
    """Average hours between runs of a five-field cron line, or None if it cannot be read."""
    fields = cron.split()
    if len(fields) != 5:
        return None
    minute, hour, dom, month, dow = fields
    per_hour = runs_per_field(minute, 60)
    per_day = runs_per_field(hour, 24)
    days_per_week = 7 if dow == "*" else runs_per_field(dow, 7)
    if dom != "*":
        days_per_month = runs_per_field(dom, 30)  # days of the month: about that many per 30 days
        days_per_week = days_per_month * 7 / 30 if days_per_month else None
    if not per_hour or not per_day or not days_per_week:
        return None
    runs_per_week = per_hour * per_day * days_per_week
    return 168 / runs_per_week


parts = sections_of(text)
print(f"Read {PATH}: sections {sorted(parts)}\n")
schedule = parts.get("schedule", "")
trigger = parts.get("retrain trigger", "")
evidence = parts.get("evidence", "")


# 2. THE CHECKS #################################

results = []

# P1: all seven sections are there and none is empty.
missing = [s for s in SECTIONS if not parts.get(s, "").strip()]
results.append(("P1", "all seven sections are present and filled in", not missing,
                f"missing or empty: {missing}"))

# P2: the schedule is a five-field cron line and names what runs it.
cron = line_value(schedule, "Cron")
gap = hours_between_runs(cron)
runner = line_value(schedule, "Runner").lower()
results.append(("P2", "the schedule gives a five-field cron line and a runner",
                gap is not None and any(r in runner for r in RUNNERS),
                f"write 'Cron: 0 6 * * *' and 'Runner: one of {RUNNERS}' in Schedule"))

# P3: the schedule is at least as fresh as the need it states.
need = number_in(line_value(schedule, "Freshness needed"))
results.append(("P3", "the cron line runs at least as often as 'Freshness needed' asks",
                gap is not None and need is not None and gap <= need,
                f"the cron line runs about every {gap and round(gap, 1)} hours; "
                f"'Freshness needed: {need} hours' asks for at most that"))

# P4: the retrain trigger is a clock, drift or never, with the number that makes it concrete.
kind = line_value(trigger, "Trigger").lower().split(" ")[0] if line_value(trigger, "Trigger") else ""
threshold = number_in(line_value(trigger, "Threshold"))
every = line_value(trigger, "Every")
concrete = (kind == "clock" and hours_between_runs(every) is not None) or \
           (kind == "drift" and threshold is not None) or kind == "never"
results.append(("P4", "the retrain trigger is clock, drift or never, with its cron line or threshold",
                kind in TRIGGERS and concrete,
                "write 'Trigger: drift' and 'Threshold: 14', or 'Trigger: clock' and 'Every: 0 7 * * 1'"))

# P5: at least two alternatives, each a bullet that names what it is and why it lost.
bullets = [l for l in parts.get("alternatives", "").splitlines() if l.strip().startswith("- ")]
results.append(("P5", "at least two alternatives are named, one bullet each", len(bullets) >= 2,
                f"found {len(bullets)} bullet(s) in Alternatives"))

# P6: the reason argues from the Step 3 table: it names two of its columns.
used = [c for c in COLUMNS if c in parts.get("reason", "").lower()]
results.append(("P6", "the reason names at least two columns of the Step 3 table", len(used) >= 2,
                f"named {used}; the table's columns are {COLUMNS}"))

# P7: the evidence comes from a run: the checks passed and the recorded test_rmse.
rmse = number_in(line_value(evidence, "test_rmse"))
checks = re.search(r"^Checks:\s*(\d+)\s+of\s+(\d+)", evidence, re.MULTILINE | re.IGNORECASE)
ok_checks = checks is not None and checks.group(1) == checks.group(2) == "8"
detail = "write 'Checks: 8 of 8' and 'test_rmse: 10.22' from your run of check.sh"
if ok_checks and rmse is not None and MODEL_PATH:
    try:
        model = json.loads(Path(MODEL_PATH).read_text(encoding="utf-8"))
        ok_checks = abs(float(model.get("test_rmse", "nan")) - rmse) < 0.01
        detail = f"the model file says test_rmse {model.get('test_rmse')}; the evidence says {rmse}"
    except (OSError, ValueError) as err:
        ok_checks, detail = False, f"could not read {MODEL_PATH}: {err}"
results.append(("P7", "the evidence gives 8 of 8 checks and the recorded test_rmse",
                ok_checks and rmse is not None, detail))

# P8: a drift threshold sits above the error the run recorded, or it would retrain every time.
if kind == "drift":
    sane = threshold is not None and rmse is not None and threshold > rmse
    note = f"the threshold {threshold} must be above the recorded test_rmse {rmse}"
else:
    sane, note = True, ""
results.append(("P8", "a drift threshold is above the recorded test_rmse", sane, note))

# P9: a person is paged, by a named route, and it is not 'nobody'.
who = line_value(parts.get("paged", ""), "Who").lower()
how = line_value(parts.get("paged", ""), "How")
results.append(("P9", "a person is named under Paged, with how they hear of a failed run",
                bool(who) and who not in ("nobody", "none", "no one", "tbd") and bool(how),
                "write 'Who: the team member on duty this week' and 'How: GitHub Actions failure email'"))

# P10: the finale line names one artefact this pipeline produces.
finale = line_value(parts.get("finale", ""), "Finale evidence").lower()
results.append(("P10", "the finale line names an artefact this pipeline produces",
                any(a in finale for a in ARTEFACTS),
                f"write 'Finale evidence: ' and one of {ARTEFACTS}, then why it is evidence"))


# 3. PRINT ONE LINE PER CHECK #################################

failed = 0
for cid, label, ok, why in results:
    print(f"{'PASS' if ok else 'FAIL'}  {cid} {label}")
    if not ok:
        failed += 1
        print("      " + why)

passed = len(results) - failed
print(f"\n{passed} of {len(results)} checks pass." +
      (" A reviewer still reads the reason." if failed == 0 else ""))
sys.exit(1 if failed else 0)
