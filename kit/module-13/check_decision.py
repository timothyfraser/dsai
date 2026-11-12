# check_decision.py
# The lab's checks: read a decision record and its audit log, and test the rules.
# Course kit, module 13
#
# Topic: Decision support
#
# A decision-support tool may inform, rank or recommend. A named person decides.
# This script reads two files your tool writes, options.json and audit_log.jsonl,
# and prints one PASS or FAIL line per check. It calls no model, so it runs anywhere.

# Run from this folder:
#   python3 check_decision.py example     # the saved example (stub mode)
#   python3 check_decision.py decision    # your team's own folder
# Exits 1 if any check fails.

# 0. SETUP ###################################

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FOLDER = HERE / (sys.argv[1] if len(sys.argv) > 1 else "decision")
RECORD = FOLDER / "options.json"
LOG = FOLDER / "audit_log.jsonl"

# The levels a model is allowed to work at. "decide" is not on the list, on purpose.
MODEL_ROLES = ("inform", "rank", "recommend")
# Words that mean "the model" when someone types them into an owner field.
NOT_A_PERSON = ("model", "ai", "llm", "assistant", "the tool", "system")

results = []
def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))

# 1. LOAD ###################################

if not RECORD.exists() or not LOG.exists():
    print(f"FAIL  {FOLDER.name}/ needs options.json and audit_log.jsonl")
    sys.exit(1)
record = json.loads(RECORD.read_text(encoding="utf-8"))
log = [json.loads(l) for l in LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
options = record.get("options", [])
ids = [o.get("id") for o in options]
owner = str(record.get("decision_owner", "")).strip()
decision = record.get("decision") or {}
print(f"Loaded {len(options)} options and {len(log)} audit lines from {FOLDER.name}/.")

# 2. THE CHECKS ###################################

# C1: real options. At least two, and each one has a reason and a source for that reason.
thin = [o.get("id") for o in options
        if not o.get("reasons") or not o.get("sources")
        or any(not str(s.get("where", "")).strip() for s in o.get("sources", []))]
check("C1 at least two options, each with reasons and sources",
      len(options) >= 2 and not thin, f"options without a reason or a source: {thin}")

# C2: a person owns the decision. An owner field that names the model does not count.
check("C2 a named person owns the decision",
      bool(owner) and owner.lower() not in NOT_A_PERSON, f"decision_owner is '{owner}'")

# C3: the model does not decide. Its role is one of the allowed levels,
# and no audit line shows the model taking the "decide" action.
model_decides = [l["seq"] for l in log if l.get("actor") == "model" and l.get("action") == "decide"]
check("C3 the model does not decide",
      record.get("model_role") in MODEL_ROLES and not model_decides,
      f"model_role '{record.get('model_role')}', model decide lines {model_decides}")

# C4: the audit log is complete. Lines are in order, each says who did what,
# and a person reviewed before a person decided.
seqs = [l.get("seq") for l in log]
in_order = seqs == sorted(seqs) and len(set(seqs)) == len(seqs)
complete = all(l.get("actor") in ("human", "model") and l.get("action") and str(l.get("note", "")).strip()
               for l in log)
decide_at = [l["seq"] for l in log if l.get("actor") == "human" and l.get("action") == "decide"]
review_at = [l["seq"] for l in log if l.get("actor") == "human" and l.get("action") == "review"]
reviewed_first = bool(decide_at) and any(r < decide_at[-1] for r in review_at)
check("C4 the audit log is in order and a person reviewed before deciding",
      in_order and complete and reviewed_first,
      f"in order {in_order}, every line complete {complete}, review before decide {reviewed_first}")

# C5: the record and the log agree. The chosen option exists, the person who decided
# is the owner, and the last decide line in the log names the same option.
last_decide = next((l for l in reversed(log) if l.get("action") == "decide"), {})
agree = (decision.get("chosen_option") in ids
         and str(decision.get("decided_by", "")).strip() == owner
         and last_decide.get("option") == decision.get("chosen_option"))
check("C5 the decision record and the audit log agree", agree,
      f"chosen '{decision.get('chosen_option')}', decided_by '{decision.get('decided_by')}', log says '{last_decide.get('option')}'")

# C6: the owner wrote down why. A rationale in the owner's words, not left empty.
check("C6 the decision has a rationale", bool(str(decision.get("rationale", "")).strip()))

# C7-C10 read DESIGN.md, the team's written design choice, from the same folder.
# Four sections: Rung, Rejected, Reason, Evidence.
DESIGN = FOLDER / "DESIGN.md"
design_text = DESIGN.read_text(encoding="utf-8") if DESIGN.exists() else ""
sections = {}
current = None
for line in design_text.splitlines():
    if line.startswith("## "):
        current = line[3:].strip().lower()
        sections[current] = []
    elif current is not None:
        sections[current].append(line)
body = {k: "\n".join(v).strip() for k, v in sections.items()}
NEEDED = ("rung", "rejected", "reason", "evidence")

# C7: DESIGN.md exists and has the four sections, each with some text.
missing = [n for n in NEEDED if not body.get(n)]
check("C7 DESIGN.md has Rung, Rejected, Reason and Evidence sections",
      DESIGN.exists() and not missing,
      "DESIGN.md is missing" if not DESIGN.exists() else f"missing or empty sections: {missing}")

# C8: the Rung line is one of the allowed levels and matches model_role in options.json.
m = re.search(r"^Rung:\s*(\S+)", body.get("rung", ""), re.M | re.I)
rung = m.group(1).strip().lower().rstrip(".,") if m else ""
check("C8 the Rung is inform, rank or recommend and matches options.json",
      rung in MODEL_ROLES and rung == record.get("model_role"),
      f"Rung '{rung}', model_role '{record.get('model_role')}'")

# C9: Rejected has a bullet that names another rung, a solver or rule-based code, and says why it lost.
others = [r for r in MODEL_ROLES if r != rung] + ["decide", "solver", "rule-based", "rule based"]
rejected_ok = False
for b in body.get("rejected", "").splitlines():
    t = b.strip().lower()
    if t.startswith(("-", "*")) and any(w in t for w in others) and "because" in t:
        rejected_ok = True
check("C9 Rejected names another rung, a solver or rule-based code, and why it lost",
      rejected_ok, "need a bullet that names one of them and has the word 'because'")

# C10: Evidence names audit_log.jsonl and a line count that matches the file.
m = re.search(r"audit_log\.jsonl\D{0,40}?(\d+)\s+lines", body.get("evidence", ""))
claimed = int(m.group(1)) if m else None
check("C10 Evidence names audit_log.jsonl and its true line count",
      claimed == len(log), f"Evidence says {claimed}, the file has {len(log)} lines")

# 3. SUMMARY ###################################

print(f"{sum(results)} of {len(results)} checks pass.")
sys.exit(0 if all(results) else 1)
