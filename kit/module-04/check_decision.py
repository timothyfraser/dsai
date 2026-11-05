# check_decision.py
# Read a team's DECISION.md and check that the deployment decision is complete.
# Course kit, module 4
#
# Topic: Deployment, decided on purpose
#
# A deploy that works is half the lab. The other half is the decision behind
# it: which host, against which alternatives, for what reason, on what
# evidence; who holds the key that can change what everyone sees; and how
# the team goes back when a deploy breaks. This script checks that every part
# is written down. It cannot check that the reasoning is good: a reviewer
# reads the file for that. It calls no server and no model, so it runs anywhere.
#
# No python packages to install: it uses only the standard library.
#
# Run it from this folder:
#   python3 check_decision.py example/DECISION.md       # the saved example, which passes
#   python3 check_decision.py example_bad/DECISION.md   # broken on purpose, to show FAIL
#   python3 check_decision.py path/to/your/DECISION.md  # your team's own file
# Exits 1 if any check fails.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import re  # for finding the sections and the patterns inside them
import sys  # for the file argument and the exit code
from pathlib import Path  # for reading the file

## 0.2 Configuration #################################

PATH = Path(sys.argv[1] if len(sys.argv) > 1 else "DECISION.md")

# The six sections the lab asks for, by their headings. A seventh, CORS, has its own check (D8).
SECTIONS = ["Host", "Alternatives", "Reason", "Evidence", "Credentials", "Rollback"]
# The trade-offs the host table in the module compares. A reason names at least one.
TRADE_OFFS = ("cost", "control", "reach", "access", "who can", "3 am", "break", "support", "sleep", "secret")
# Answers that mean "nobody in particular" when written as a key holder.
NOBODY = ("everyone", "all of us", "the whole team", "the team", "anyone", "the agent", "the ai")

results = []
def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))

# 1. READ THE SECTIONS ###################################

if not PATH.exists():
    print(f"FAIL  no file at {PATH}: copy example/DECISION.md and fill it in")
    sys.exit(1)
text = PATH.read_text(encoding="utf-8")

# Split on "## Heading" lines. Each section's body is the text up to the next heading.
parts = re.split(r"^##\s+(.+?)\s*$", text, flags=re.M)
body = {parts[i].strip().split()[0].lower(): parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}
def sec(name):
    return body.get(name.lower(), "")
def bullets(s):
    return [l.strip()[1:].strip() for l in s.splitlines() if l.strip().startswith(("-", "*"))]
print(f"Read {PATH}: sections {sorted(body)}\n")

# 2. THE CHECKS ###################################

# D1: every section is there and has words in it.
empty = [s for s in SECTIONS if len(sec(s).split()) < (1 if s == "Host" else 3)]
check("D1 all six sections are present and filled in", not empty, f"missing or empty: {empty}")

# D2: one host chosen, and at least two alternatives that are not the same host.
host = sec("Host").splitlines()[0].strip().lower() if sec("Host") else ""
alts = bullets(sec("Alternatives"))
same = [a for a in alts if host and a.lower().split(",")[0].strip() == host.split(",")[0].strip()]
check("D2 one host, and at least two alternatives considered", bool(host) and len(alts) >= 2 and not same,
      f"host '{host}', {len(alts)} alternatives, repeats the host: {same}")

# D3: the reason names a trade-off, not only a preference.
reason = sec("Reason").lower()
named = [t for t in TRADE_OFFS if t in reason]
check("D3 the reason names a trade-off", bool(named), "name cost, control, who can reach it, or what breaks at 3 am")

# D4: the evidence is something a reviewer can open or rerun: a live address and a check's output.
ev = sec("Evidence")
check("D4 the evidence has a live address and pasted check output",
      bool(re.search(r"https?://", ev)) and bool(re.search(r"\bPASS\b|\b\d+ passed\b", ev)),
      "paste the live address and the lines check.sh printed")

# D5: a named holder for the Publisher key, and a place for the Viewer key.
cred = sec("Credentials")
pub = next((l for l in cred.splitlines() if "publisher" in l.lower()), "")
holder = pub.split(":", 1)[1].strip().lower() if ":" in pub else ""
check("D5 a named person holds the Publisher key, and the Viewer key has a place",
      bool(holder) and not any(holder.startswith(n) for n in NOBODY) and "viewer" in cred.lower(),
      f"Publisher line is '{pub.strip()}'")

# D6: the rollback names what you go back to and how you know it worked.
rb = sec("Rollback").lower()
route = any(w in rb for w in ("reactivat", "redeploy", "app platform rollback", "roll back to"))
back_to = any(w in rb for w in ("previous", "bundle", "commit", "revert", "tag", "version"))
proof = any(w in rb for w in ("health", "check.sh", "smoke"))
check("D6 the rollback names the route the team can take, the version to return to and the check that proves it",
      route and back_to and proof,
      f"names a route (reactivate a bundle, redeploy a commit, the host's rollback) {route}, a version {back_to}, a check {proof}")

# D7: no secret in the file. A long run of letters and digits looks like a key.
leaked = re.findall(r"\b[A-Za-z0-9_\-]{32,}\b", text)
check("D7 no key value is written in the file", not leaked, f"{len(leaked)} key-shaped strings")

# D8: the CORS section names the page's origin (scheme and host), and is not the wildcard.
cors = sec("CORS")
origin = re.search(r"https?://[A-Za-z0-9.\-]+(:\d+)?", cors)
wild = bool(re.search(r"(?<![\w.])\*(?![\w.])", cors))
check("D8 the CORS line names the page's origin, not *", bool(origin) and not wild,
      "write the page's origin, such as https://host.example.edu, and no *")

# 3. SUMMARY ###################################

print(f"\n{sum(results)} of {len(results)} checks pass. A reviewer still reads the reason.")
sys.exit(0 if all(results) else 1)
