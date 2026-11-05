# check_decision.py
# Check that DECISION.md has its three parts, each with what a judge will ask for
# Course kit, module 14
#
# Topic: Hackathon
#
# Before the clock starts, your team writes DECISION.md: the prompt you chose and
# the two you rejected, the scope cut, and the evidence that the system works.
# The judges ask review question 3 against this file. This script checks that the
# file is complete. It cannot tell you whether the reasons are good; a teammate
# and the judges read them. It can tell you that every part is there.
#
# Run it from the top of your team repo:
#   python check_decision.py DECISION.md           # check your decision
#   DECISION_STUB=1 python check_decision.py       # check the sample decision
#   DECISION_STUB=bad python check_decision.py     # check a sample broken on purpose; must fail
# Exits 1 if any check fails.
#
# Uses only the Python standard library.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import os  # for paths and the stub switch
import re  # for reading labelled lines
import sys  # for arguments and the exit code

## 0.2 Configuration #################################

HERE = os.path.dirname(os.path.abspath(__file__))
STUB = os.environ.get("DECISION_STUB", "")  # "", "1" or "bad"
SECTIONS = ["The prompt", "The cut", "The evidence"]
MIN_REASON_WORDS = 6  # a reason shorter than this is a label, not a reason
MIN_CASES = 2  # one passing case is one run; the judges ask for more

## 0.3 Find the Text #################################

if STUB:
    with open(os.path.join(HERE, "DECISION.example.md"), encoding="utf-8") as f:
        text = f.read()
    if STUB == "bad":
        # Break it on purpose: drop one rejected prompt and cut the evidence to one case.
        text = re.sub(r"^- A parking photo counter.*\n", "", text, flags=re.MULTILINE)
        text = text.replace("Cases: 3 of 3", "Cases: 1 of 1")
else:
    path = sys.argv[1] if len(sys.argv) > 1 else "DECISION.md"
    if not os.path.exists(path):
        sys.exit(f"FAIL  {path} is not here. Run this from the folder that holds your DECISION.md.")
    with open(path, encoding="utf-8") as f:
        text = f.read()


# 1. SPLIT THE TEXT INTO SECTIONS #################################

def sections_of(md):
    """Return {heading: body} for every '## ' heading."""
    found, name = {}, None
    for line in md.splitlines():
        if line.startswith("## "):
            name = line[3:].strip()
            found[name] = ""
        elif name:
            found[name] += line + "\n"
    return found


def line_value(body, label):
    """The text after 'Label:' on its own line, or None."""
    m = re.search(rf"^{label}:[ \t]*(.*)$", body, re.MULTILINE | re.IGNORECASE)
    return m.group(1).strip() if m else None


def words(s):
    return len(re.findall(r"[A-Za-z0-9']+", s or ""))


parts = sections_of(text)
prompt = parts.get("The prompt", "")
cut = parts.get("The cut", "")
evidence = parts.get("The evidence", "")


# 2. THE CHECKS #################################

results = []

# H1: all three sections are there and none is empty.
missing = [s for s in SECTIONS if not parts.get(s, "").strip()]
results.append(("H1", "all three sections are present and not empty", not missing,
                f"missing or empty: {missing}"))

# H2: the chosen prompt is named.
chosen = line_value(prompt, "Chosen")
results.append(("H2", "the chosen prompt is named", bool(chosen),
                "write a line 'Chosen: <the prompt>' in the section The prompt"))

# H3: two rejected prompts, each with a reason after a colon.
rejected = [l[2:] for l in prompt.splitlines() if l.strip().startswith("- ")]
with_reason = [r for r in rejected if ":" in r and words(r.split(":", 1)[1]) >= MIN_REASON_WORDS]
results.append(("H3", "two rejected prompts are named, each with a reason", len(with_reason) >= 2,
                f"found {len(with_reason)} rejected prompt(s) written as '- <prompt>: <reason>' "
                f"with at least {MIN_REASON_WORDS} words of reason"))

# H4: the cut names the user and what was dropped first, with a reason.
user = line_value(cut, "User")
dropped = line_value(cut, "Dropped first")
results.append(("H4", "the cut names the user and what was dropped first, with a reason",
                bool(user) and words(dropped) >= MIN_REASON_WORDS and "because" in (dropped or "").lower(),
                "write 'User: <who>' and 'Dropped first: <feature>, because <reason>' in The cut"))

# H5: the evidence names a check and its test data.
check = line_value(evidence, "Check")
data = line_value(evidence, "Data")
results.append(("H5", "the evidence names a check script and its test data", bool(check) and bool(data),
                "write 'Check: <script path>' and 'Data: <test data path>' in The evidence"))

# H6: the evidence is more than one run: at least two cases, all passing.
cases = re.search(r"^Cases:\s*(\d+)\s+of\s+(\d+)", evidence, re.MULTILINE | re.IGNORECASE)
k, n = (int(cases.group(1)), int(cases.group(2))) if cases else (None, None)
results.append(("H6", f"the evidence covers at least {MIN_CASES} cases, all passing",
                cases is not None and n >= MIN_CASES and k == n,
                f"write 'Cases: k of n' with n at least {MIN_CASES}; the file says {k} of {n}"))


# 3. PRINT ONE LINE PER CHECK #################################

failed = 0
for cid, label, ok, detail in results:
    print(f"{'PASS' if ok else 'FAIL'}  {cid} {label}")
    if not ok:
        failed += 1
        print("      " + detail)

print(f"\n{'Decision file complete.' if failed == 0 else str(failed) + ' decision check(s) failed.'}")
sys.exit(1 if failed else 0)
