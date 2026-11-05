# check_decision.py
# The Finale lab's checks: read a team's finished repo and test what a script can test.
# Course kit, module 23
#
# Topic: Finale: defend it, hand it off
#
# A script cannot tell you whether your architecture is good. It can tell you whether
# every box carries a decision, whether the decision log is complete, whether a stranger
# has the instructions they need, and whether a key or "the AI did it" slipped in.
# The defence itself is judged by a person listening. This script calls no model.

# Run from this folder:
#   python3 check_decision.py example                # the saved example (stub mode)
#   python3 check_decision.py /path/to/your/repo     # your team's own repo
# Exits 1 if any check fails.

# 0. SETUP ###################################

import re          # for reading headings and fields
import sys         # for the folder argument and the exit code
from pathlib import Path  # for walking the repo

HERE = Path(__file__).resolve().parent
ARG = sys.argv[1] if len(sys.argv) > 1 else "example"
REPO = Path(ARG) if Path(ARG).is_absolute() else (HERE / ARG if (HERE / ARG).exists() else Path(ARG))
REPO = REPO.resolve()

MIN_DECISIONS = 5        # a finished system has made at least five choices worth writing down
MAX_STANDUP_WORDS = 450  # about three minutes spoken
# Phrases that hand your work to a tool. Say what you chose, not who typed it.
HOLLOW = ("the ai", "the agent did", "chatgpt did", "claude did", "cursor did")
# A heading names the decision, never when it was made: the date goes in git, not the title.
DATE_WORDS = re.compile(r"\b(19|20)\d\d\b|\b(jan(uary)?|feb(ruary)?|mar(ch)?|apr(il)?|june?|july?|aug(ust)?"
                        r"|sep(t|tember)?|oct(ober)?|nov(ember)?|dec(ember)?)\b|\bmay \d"
                        r"|\b(mon|tues|wednes|thurs|fri|satur|sun)day\b|\d{1,2}/\d{1,2}", re.I)
# Shapes that look like a real key. A placeholder such as "your-key-here" is fine.
KEY_SHAPES = re.compile(r"sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}|AIza[0-9A-Za-z_-]{30,}")

results = []
def check(name, ok, detail=""):
    ok = bool(ok)
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))

def read(name):
    p = REPO / name
    return p.read_text(encoding="utf-8") if p.exists() else None

def said_something(line):
    """True for a line with words in it; False for a blank or a '<placeholder>' line."""
    t = line.strip()
    return bool(t) and not (t.startswith("<") and t.endswith(">"))

def sections(text, prefix):
    """Split a Markdown file into {heading: body} for '## <prefix>...' headings."""
    out, head = {}, None
    for line in text.splitlines():
        if line.startswith("## "):
            head = line[3:].strip() if line[3:].strip().lower().startswith(prefix) else None
            if head:
                out[head] = []
        elif head:
            out[head].append(line)
    return {h: "\n".join(b) for h, b in out.items()}

def field(body, label):
    m = re.search(rf"^[ \t]*[-*]?[ \t]*\**{label}\**[ \t]*:[ \t]*(\S.*)$", body, re.I | re.M)
    return m.group(1).strip() if m else ""

def resolves(ref):
    """Evidence must point somewhere a reviewer can open: a link, or a file in the repo."""
    ref = ref.strip("`<> ")
    if re.match(r"https?://", ref):
        return True
    target = ref.split("#")[0].split(" ")[0]
    return bool(target) and (REPO / target).exists()

if not REPO.is_dir():
    print(f"FAIL  no folder at {REPO}. Run from kit/module-23, or pass your repo's path.")
    sys.exit(1)
print(f"Checking {REPO.name}/")

# 1. THE ARCHITECTURE ###################################

# C1: every box in the diagram carries the choice made and the alternative rejected.
arch = read("ARCHITECTURE.md")
if arch is None:
    check("C1 ARCHITECTURE.md exists and every box has a decision", False, "no ARCHITECTURE.md")
else:
    fence = re.search(r"```mermaid\n(.*?)```", arch, re.S)
    nodes = set(re.findall(r"\b\w+\[\"?([^\]\"]+)\"?\]", fence.group(1))) if fence else set()
    boxes = {h.split(":", 1)[1].strip(): b for h, b in sections(arch, "box").items() if ":" in h}
    undecided = sorted(n for n in nodes if n not in boxes
                       or not said_something(field(boxes[n], "Choice"))
                       or not said_something(field(boxes[n], "Instead of")))
    check("C1 ARCHITECTURE.md exists and every box has a decision",
          len(nodes) >= 3 and not undecided,
          f"boxes found {len(nodes)}; boxes with no Choice or Instead of, or one still blank or a <placeholder>: {undecided}")

# 2. THE DECISION LOG ###################################

# C2: at least MIN_DECISIONS entries, date-free headings, all four fields, evidence that resolves.
log = read("DECISIONS.md")
if log is None:
    check(f"C2 DECISIONS.md has {MIN_DECISIONS} complete entries", False, "no DECISIONS.md")
else:
    entries = sections(log, "d")
    bad = []
    for head, body in entries.items():
        missing = [f for f in ("Choice", "Alternatives", "Reason", "Evidence") if not said_something(field(body, f))]
        if DATE_WORDS.search(head):
            missing.append("a date in the heading")
        if field(body, "Evidence") and not resolves(field(body, "Evidence")):
            missing.append("evidence that opens")
        if missing:
            bad.append(f"{head.split(':')[0]}: {', '.join(missing)}")
    check(f"C2 DECISIONS.md has {MIN_DECISIONS} complete entries",
          len(entries) >= MIN_DECISIONS and not bad, f"{len(entries)} entries; {bad}")

# 3. THE HAND-OFF ###################################

# C3: a stranger can install it, run it and check it from the README alone.
readme = read("README.md") or ""
heads = [l[3:].lower() for l in readme.splitlines() if l.startswith("## ")]
lacking = [w for w in ("install", "run", "check") if not any(w in h for h in heads)]
check("C3 README.md has install, run and check sections", readme and not lacking,
      f"missing: {lacking}")

# C4: the next team's agent gets a skill file with a name and a description.
skill = read("SKILL.md") or ""
check("C4 SKILL.md for the next team has a name and a description",
      skill.startswith("---") and re.search(r"^name:\s*\S", skill, re.M)
      and re.search(r"^description:\s*\S", skill, re.M), "needs front matter with name: and description:")

# C5: the run records are in the repo, so a claim of "it passed" can be opened.
runs = [p for p in (REPO / "runs").glob("*") if p.is_file() and p.stat().st_size > 0] \
    if (REPO / "runs").is_dir() else []
check("C5 run records exist in runs/", len(runs) >= 1, "runs/ is missing or empty")

# C6: no key anywhere in the repo, and no .env file except .env.example.
leaks = []
for p in REPO.rglob("*"):
    if not p.is_file() or ".git" in p.parts:
        continue
    if p.name == ".env" or (p.name.startswith(".env") and p.name != ".env.example"):
        leaks.append(str(p.relative_to(REPO)))
        continue
    try:
        if KEY_SHAPES.search(p.read_text(encoding="utf-8", errors="ignore")):
            leaks.append(str(p.relative_to(REPO)))
    except OSError:
        pass
check("C6 no key in the repo", not leaks, f"look at: {sorted(set(leaks))}")

# 4. THE STAND-UP AND THE SELF-ASSESSMENT ###################################

# C7: the stand-up answers the four questions, fits in three minutes, and owns its work.
standup = read("STANDUP.md") or ""
words = len(re.findall(r"[A-Za-z0-9']+", standup))
low = standup.lower()
answers = {h.lower(): b for h, b in sections(standup, "").items()}
# A part counts only if its section says something: a blank or a <placeholder> line is no answer.
parts = [q for q in ("what it is", "why this architecture", "what it costs", "where it fails")
         if not any(said_something(l) for l in answers.get(q, "").splitlines())]
# Whole words only: "the air" and "the aim" are not "the ai".
said = [h for h in HOLLOW if re.search(rf"\b{re.escape(h)}\b", low)]
check(f"C7 STANDUP.md answers four questions in under {MAX_STANDUP_WORDS} words, owning the work",
      standup and words < MAX_STANDUP_WORDS and not parts and not said,
      f"{words} words; parts unanswered {parts}; hollow phrases {said}")

# C8: the four columns, each with evidence a reviewer can open.
selfa = read("SELF-ASSESSMENT.md") or ""
rows = {r[0].strip().lower(): r for r in
        (l.strip().strip("|").split("|") for l in selfa.splitlines() if l.strip().startswith("|"))
        if len(r) >= 3}
gaps = []
for col in ("build", "verify", "productionise", "explain"):
    row = rows.get(col)
    links = (re.findall(r"\(([^)]+)\)", row[-1]) + re.findall(r"`([^`]+)`", row[-1])) if row else []
    # The "Our answer" cell must hold an answer, not a blank or a <placeholder>.
    if not row or not said_something(row[2]) or not links or not all(resolves(l) for l in links):
        gaps.append(col)
check("C8 SELF-ASSESSMENT.md fills all four columns with evidence that opens", not gaps,
      f"columns without working evidence: {gaps}")

print(f"{sum(results)} of {len(results)} checks pass.")
sys.exit(0 if all(results) else 1)
