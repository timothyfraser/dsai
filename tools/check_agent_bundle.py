# check_agent_bundle.py
# Check the agent bundle: skills, agents, OpenCode config, CLAUDE.md and AGENTS.md.
# Course repo tooling, no packages to install (standard library only).
#
# Run it from anywhere:
#   python3 tools/check_agent_bundle.py
# It prints one PASS or FAIL line per check, and exits 1 if any check fails.
#
# The checks:
#   1. every .claude/skills/*/SKILL.md has a name and a description under 1,024 characters
#   2. opencode.json parses as JSON
#   3. no key-shaped string anywhere under the repo, except kit/module-03/example_bad
#   4. the command tables in CLAUDE.md and AGENTS.md are identical
#   5. none of the strings that belong to other courses or to the instructor's private
#      repo appear anywhere in the bundle

# 0. SETUP ###################################

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
results = []


def check(label, ok, detail=""):
    results.append(ok)
    print(("PASS  " if ok else "FAIL  ") + label + (f"  ({detail})" if detail else ""))


def files_under(base, skip_dirs=(".git", "node_modules", "__pycache__", "dist")):
    for p in sorted(Path(base).rglob("*")):
        if p.is_file() and not any(part in skip_dirs for part in p.relative_to(ROOT).parts):
            yield p


def read(p):
    try:
        return p.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


# 1. SKILLS ###################################

problems = []
skills = sorted((ROOT / ".claude" / "skills").glob("*/SKILL.md"))
for md in skills:
    text = read(md) or ""
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        problems.append(f"{md.parent.name}: no front matter")
        continue
    front = m.group(1)
    name = re.search(r"(?m)^name:\s*(\S.*)$", front)
    desc = re.search(r"(?m)^description:\s*(\S.*)$", front)
    if not name:
        problems.append(f"{md.parent.name}: no name")
    elif name.group(1).strip() != md.parent.name:
        problems.append(f"{md.parent.name}: name is {name.group(1).strip()}")
    if not desc:
        problems.append(f"{md.parent.name}: no description")
    elif len(desc.group(1).strip()) >= 1024:
        problems.append(f"{md.parent.name}: description is {len(desc.group(1).strip())} characters")
check(f"{len(skills)} skills each have a name and a description under 1,024 characters", not problems and len(skills) > 0, "; ".join(problems))

# 2. OPENCODE.JSON ###################################

try:
    json.loads((ROOT / "opencode.json").read_text(encoding="utf-8"))
    check("opencode.json parses", True)
except (OSError, ValueError) as err:
    check("opencode.json parses", False, str(err).splitlines()[0])

# 3. NO KEY-SHAPED STRING ###################################

# Prefixed keys (sk-, AKIA, ghp_) are looked for in every text file in the repo.
# A run of 32 or more hex characters is looked for in the bundle's own files only: course data
# and checksum files elsewhere in the repo (a .sha256 file, a plan's document id) are not keys.
# Inside the bundle, manifest.json files hold file checksums, and a workflow's `uses: name@<40 hex>`
# pins a commit; neither is a key.
PREFIXED = re.compile(r"\bsk-[A-Za-z0-9_-]{20,}|\bAKIA[0-9A-Z]{16}\b|\bghp_[A-Za-z0-9]{20,}")
HEXRUN = re.compile(r"(?<![@0-9a-fA-F])[0-9a-fA-F]{32,}(?![0-9a-fA-F])")
EXEMPT = ROOT / "kit" / "module-03" / "example_bad"
BINARY = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".gz", ".ico", ".woff", ".woff2"}
BUNDLE = [".claude", ".opencode", "opencode.json", "CLAUDE.md", "AGENTS.md", "scaffolds/react-api", "tools",
          "docs/agents.md", "docs/model-ladder.md", "docs/opencode.md", "docs/prompts-starter.md", "docs/start.md"]
bundle_files = set()
for rel in BUNDLE:
    base = ROOT / rel
    bundle_files.update([base] if base.is_file() else files_under(base) if base.exists() else [])
hits = []
for p in files_under(ROOT):
    if EXEMPT in p.parents or p.suffix in BINARY:
        continue
    text = read(p)
    if not text:
        continue
    bad = PREFIXED.search(text) or (p in bundle_files and p.name != "manifest.json" and HEXRUN.search(text))
    if bad:
        hits.append(str(p.relative_to(ROOT)))
check("no key-shaped string under the repo (kit/module-03/example_bad excepted)", not hits, ", ".join(hits[:8]))

# 4. COMMAND TABLES ###################################


def command_table(path):
    lines, on = [], False
    for line in (read(path) or "").splitlines():
        if line.startswith("| Command |"):
            on = True
        if on:
            if not line.startswith("|"):
                break
            lines.append(line)
    return lines


a, b = command_table(ROOT / "CLAUDE.md"), command_table(ROOT / "AGENTS.md")
check("CLAUDE.md and AGENTS.md command tables are identical", bool(a) and a == b, f"{len(a)} and {len(b)} lines")

# 5. NOTHING FROM OTHER COURSES OR THE PRIVATE REPO ###################################

# Built from pieces so this file does not trip its own check.
FORBIDDEN = ["sysen" + "_instructors", "courses" + "/dsai", "connect." + "systems-apps.com", "tmf" + "77",
             "Six " + "Sigma", "sigma" + "-hat", "control " + "chart", "Dev" + "post"]
found = []
for rel in BUNDLE:
    base = ROOT / rel
    if not base.exists():
        found.append(f"missing {rel}")
        continue
    for p in ([base] if base.is_file() else files_under(base)):
        if p == Path(__file__).resolve() or p.name in {"package-lock.json", "manifest.json"}:
            continue
        text = read(p)
        if not text:
            continue
        for word in FORBIDDEN:
            if word.lower() in text.lower():
                found.append(f"{p.relative_to(ROOT)}: {word}")
check("no private-repo, other-course or event strings anywhere in the bundle", not found, "; ".join(found[:8]))

# 6. SUMMARY ###################################

n_ok = sum(results)
print(f"\n{n_ok} passed, {len(results) - n_ok} failed")
sys.exit(0 if all(results) else 1)
