# check.py
# The nine checks for the Module 12 lab: make an ugly app fabulous
# Course kit, module 12
#
# Topic: Interfaces, judged
#
# This script reads your team's ui-lab/ folder and prints one line per check.
# It does not judge whether your interface is good. A person does that.
# It checks that the evidence for "good" exists and is complete: a brief,
# a tokens file whose colours pass contrast, an audit, screenshots, the five
# states, a critique log with rounds, a rationale, and reduced motion.
#
# Run it from the top of the course repo:
#   python3 kit/module-12/check.py ui-lab
# Try it on the bundled fixture first, with no browser and no model:
#   UI_STUB=1 python3 kit/module-12/check.py      (a finished lab: passes)
#   UI_STUB=bad python3 kit/module-12/check.py    (a half-done lab: fails)
#
# If you haven't already, the browser checks need Playwright for Python:
# pip install playwright
# python3 -m playwright install chromium
# Without it, those checks say SKIP and why. Nothing else is needed.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import os, re, sys, json
from pathlib import Path

## 0.2 Configuration #################################

STUB = os.environ.get("UI_STUB", "")
KIT = Path(__file__).resolve().parent
if STUB == "1":
    LAB = KIT / "fixture" / "good" / "ui-lab"
elif STUB == "bad":
    LAB = KIT / "fixture" / "bad" / "ui-lab"
else:
    LAB = Path(sys.argv[1] if len(sys.argv) > 1 else "ui-lab")

# These values come from the module's tables. A brief or a rationale must use them.
BRIEF_HEADINGS = ["Who", "Task", "Decision supported", "Device first",
                  "Accessibility bar", "Latency budget", "States", "Scale rung", "Contract"]
FIVE_STATES = ["empty", "loading", "success", "error", "stale"]
RUNGS = ["demo", "team", "public"]
FRAMEWORKS = ["shiny", "streamlit", "gradio", "observable framework", "vite + react",
              "next.js", "react router", "tanstack start", "astro"]
STRATEGIES = ["copy-in", "headless", "full kit", "utility css", "framework-native"]
MIN_CONTRAST = 4.5     # WCAG AA floor for body text
MAX_WORDS = 600        # the rationale is one page, not an essay
MIN_ROUNDS = 3         # three trips round the loop, at least

results = []

def report(n, status, label, detail=""):
    results.append(status)
    print(f"{status:<5} check {n}: {label}" + (f"  ({detail})" if detail else ""))

def read(name):
    p = LAB / name
    return p.read_text(encoding="utf-8") if p.exists() else None

def sections(md):
    # Split a Markdown file into {heading: body} on '## ' headings.
    # Template lines that start with "Guide:" are notes, not answers, so they are dropped.
    out, head = {}, None
    for line in md.splitlines():
        if line.startswith("Guide:"):
            continue
        if line.startswith("## "):
            head = line[3:].strip()
            out[head] = ""
        elif head is not None:
            out[head] += line + "\n"
    return out

# 1. THE BRIEF ###################################

# Words before pixels: every heading must be there and say something.
def check_brief():
    md = read("BRIEF.md")
    if md is None:
        return report(1, "FAIL", "brief exists and is complete", "no BRIEF.md")
    sec = sections(md)
    missing = [h for h in BRIEF_HEADINGS if not sec.get(h, "").strip()]
    if missing:
        return report(1, "FAIL", "brief exists and is complete", "empty or missing: " + ", ".join(missing))
    states = sec["States"].lower()
    lost = [s for s in FIVE_STATES if s not in states]
    if lost:
        return report(1, "FAIL", "brief exists and is complete", "States does not name: " + ", ".join(lost))
    rung = sec["Scale rung"].strip().lower()
    if not any(rung.startswith(r) for r in RUNGS):
        return report(1, "FAIL", "brief exists and is complete", "Scale rung must be demo, team or public")
    report(1, "PASS", "brief exists and is complete", f"{len(BRIEF_HEADINGS)} headings, rung {rung.split()[0].strip(':,.')}")

# 2. TOKENS ###################################

def blocks(css, selector_pattern):
    # Return the bodies of every rule whose selector matches the pattern.
    return [m.group(1) for m in re.finditer(selector_pattern + r"\s*\{([^{}]*)\}", css)]

def props(body):
    return dict(re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", body))

def theme_values(css):
    # Light values live in :root. Dark values live in a dark-scheme media query or [data-theme="dark"].
    light = {}
    for b in blocks(css, r":root"):
        light.update(props(b))
    dark = dict(light)
    m = re.search(r"@media\s*\(prefers-color-scheme:\s*dark\)\s*\{(.*?)\}\s*\}", css, re.S)
    if m:
        for b in blocks(m.group(1) + "}", r":root[^{]*"):
            dark.update(props(b))
    for b in blocks(css, r":root\[data-theme=\"dark\"\]"):
        dark.update(props(b))
    return light, dark

def check_tokens():
    css = read("tokens.css")
    if css is None:
        return report(2, "FAIL", "tokens: light and dark, type scale, spacing", "no tokens.css")
    light, dark = theme_values(css)
    colours = [k for k, v in light.items() if v.strip().startswith("#")]
    dark_changed = [k for k in colours if dark.get(k) != light.get(k)]
    sizes = [k for k in light if k.startswith("--text-")]
    spaces = [k for k in light if k.startswith("--space-")]
    problems = []
    if not colours:
        problems.append("no colour tokens in :root")
    if not dark_changed:
        problems.append("no dark values")
    if len(sizes) < 4:
        problems.append(f"{len(sizes)} --text- sizes, need 4")
    if len(spaces) < 3:
        problems.append(f"{len(spaces)} --space- steps, need 3")
    # A colour typed straight into the app's CSS bypasses the tokens: one value, stored once.
    app = LAB / "app"
    for f in sorted(app.rglob("*.css")) if app.exists() else []:
        text = re.sub(r":root[^{]*\{[^{}]*\}", "", f.read_text(encoding="utf-8"))
        for hexval in re.findall(r"#[0-9a-fA-F]{3,8}\b", text):
            problems.append(f"raw {hexval} in {f.name}")
            break
    if problems:
        return report(2, "FAIL", "tokens: light and dark, type scale, spacing", "; ".join(problems))
    report(2, "PASS", "tokens: light and dark, type scale, spacing",
           f"{len(colours)} colours, {len(sizes)} sizes, {len(spaces)} spacing steps")

# 3. CONTRAST ###################################

# The formula is WCAG's: relative luminance of each colour, then (L1 + 0.05) / (L2 + 0.05).
def luminance(hexval):
    h = hexval.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    rgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]

def ratio(a, b):
    la, lb = sorted([luminance(a), luminance(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)

def check_contrast():
    css = read("tokens.css") or ""
    themes = theme_values(css) if css else None
    # Declare each text-on-background pair you use, as a comment: /* pair: --ink on --paper */
    pairs = re.findall(r"pair:\s*(--[\w-]+)\s+on\s+(--[\w-]+)", css)
    if not themes or not pairs:
        return report(3, "FAIL", "contrast 4.5 to 1 on declared pairs", "no tokens or no '/* pair: --a on --b */' lines")
    worst, fails = None, []
    for name, theme in zip(["light", "dark"], themes):
        for fg, bg in pairs:
            if fg not in theme or bg not in theme:
                fails.append(f"{fg} on {bg}: not defined")
                continue
            r = ratio(theme[fg], theme[bg])
            worst = r if worst is None else min(worst, r)
            if r < MIN_CONTRAST:
                fails.append(f"{fg} on {bg} ({name}) {r:.2f}")
    if fails:
        return report(3, "FAIL", "contrast 4.5 to 1 on declared pairs", "; ".join(fails))
    report(3, "PASS", "contrast 4.5 to 1 on declared pairs", f"{len(pairs)} pairs x 2 themes, lowest {worst:.2f}")

# 4. AUTOMATED AUDIT ###################################

# The agent runs the tools and saves what they print. The script reads the saved files.
def check_audit():
    audit = LAB / "audit"
    axe = [audit / "axe-390.json", audit / "axe-1280.json"]
    detect = audit / "detect.txt"
    if not all(p.exists() for p in axe + [detect]):
        if STUB:
            return report(4, "SKIP", "audit clean: detector and axe", "stub mode: the fixture has no audit/ folder, and no browser runs here")
        return report(4, "FAIL", "audit clean: detector and axe", "save audit/detect.txt, audit/axe-390.json, audit/axe-1280.json")
    bad = []
    for p in axe:
        v = json.loads(p.read_text(encoding="utf-8")).get("violations", [])
        serious = [x["id"] for x in v if x.get("impact") in ("serious", "critical")]
        if serious:
            bad.append(f"{p.name}: {', '.join(serious)}")
    if re.search(r"\bP0\b", detect.read_text(encoding="utf-8")):
        bad.append("detect.txt lists a P0")
    if bad:
        return report(4, "FAIL", "audit clean: detector and axe", "; ".join(bad))
    report(4, "PASS", "audit clean: detector and axe", "0 serious or critical, 0 P0")

# 5. SCREENSHOTS ###################################

SHOTS = ["before-390.png", "before-1280.png", "after-390.png", "after-1280.png"]

def check_shots():
    missing = [s for s in SHOTS if not (LAB / "shots" / s).exists()
               or (LAB / "shots" / s).read_bytes()[:8] != b"\x89PNG\r\n\x1a\n"]
    if missing:
        return report(5, "FAIL", "before and after screenshots", "missing or not PNG: " + ", ".join(missing))
    report(5, "PASS", "before and after screenshots", "4 PNGs; sideways scroll is measured in check 6")

# 6. THE FIVE STATES, LIVE ###################################

# A picture can be cropped. The browser cannot lie about scrollWidth or about what is on screen.
# The app marks each state with data-state="empty|loading|success|error|stale"; the brief's
# Contract heading says which address the page calls, and UI_API_GLOB repeats it here.
def check_states():
    url, glob = os.environ.get("UI_URL"), os.environ.get("UI_API_GLOB")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return report(6, "SKIP", "five states reachable, no sideways scroll at 390", "Playwright for Python is not installed")
    if STUB:
        return report(6, "SKIP", "five states reachable, no sideways scroll at 390", "stub mode: the fixture has no app to drive")
    if not url or not glob:
        return report(6, "SKIP", "five states reachable, no sideways scroll at 390", "set UI_URL to your page and UI_API_GLOB to your API path")
    replies = {"success": (200, {"answer": "Stub answer", "source": "stub.csv, row 1"}),
               "stale": (200, {"answer": "Stub answer", "source": None}),
               "error": (500, {"detail": "stub failure"})}
    seen, wide = [], False
    with sync_playwright() as p:
        page = p.chromium.launch().new_page(viewport={"width": 390, "height": 844})
        page.goto(url)
        wide = page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
        if page.locator('[data-state="empty"]').inner_text().strip():
            seen.append("empty")
        for state, (code, body) in replies.items():
            page.route(glob, lambda r, c=code, b=body: r.fulfill(status=c, json=b))
            page.reload()
            page.get_by_role("button").first.click()
            el = page.locator(f'[data-state="{state}"]')
            el.wait_for(timeout=5000)
            if el.inner_text().strip():
                seen.append(state)
            page.unroute(glob)
        # Loading: hold the reply and look while it waits.
        page.route(glob, lambda r: None)
        page.reload()
        page.get_by_role("button").first.click()
        if page.locator('[data-state="loading"]').inner_text().strip():
            seen.append("loading")
    lost = [s for s in FIVE_STATES if s not in seen]
    if lost or wide:
        return report(6, "FAIL", "five states reachable, no sideways scroll at 390",
                      ("not shown: " + ", ".join(lost) + "; " if lost else "") + ("scrolls sideways" if wide else ""))
    report(6, "PASS", "five states reachable, no sideways scroll at 390", "5 of 5 states, scrollWidth fits")

# 7. CRITIQUE LOG ###################################

# Each round: findings as '- P1 [hierarchy] what is wrong', and a 'Changed:' line.
def check_critique():
    md = read("CRITIQUE.md")
    if md is None:
        return report(7, "FAIL", "critique log has rounds", "no CRITIQUE.md")
    rounds = {h: b for h, b in sections(md).items() if re.match(r"Round \d+", h)}
    problems = []
    if len(rounds) < MIN_ROUNDS:
        problems.append(f"{len(rounds)} rounds, need {MIN_ROUNDS}")
    for h, b in rounds.items():
        if not re.search(r"^- P[0-3] \[[\w -]+\] \S", b, re.M):
            problems.append(f"'{h}' has no '- P# [word] finding' line")
        if not re.search(r"^Changed:\s*\S", b, re.M):
            problems.append(f"'{h}' has no 'Changed:' line")
    if not any("phone" in h.lower() for h in rounds):
        problems.append("no round marked phone")
    if problems:
        return report(7, "FAIL", "critique log has rounds", "; ".join(problems))
    report(7, "PASS", "critique log has rounds", f"{len(rounds)} rounds, one on a phone")

# 8. RATIONALE ###################################

# The defended decision. The script checks it is complete; a person reads whether it is honest.
def check_rationale():
    md = read("RATIONALE.md")
    if md is None:
        return report(8, "FAIL", "rationale: one page, the four choices, two rejected", "no RATIONALE.md")
    sec = {k.lower(): v.strip().lower() for k, v in sections(md).items()}
    words = len(" ".join(l for l in md.splitlines() if not l.startswith("Guide:")).split())
    problems = []
    if words >= MAX_WORDS:
        problems.append(f"{words} words, must be under {MAX_WORDS}")
    for head, allowed in [("framework", FRAMEWORKS), ("component strategy", STRATEGIES), ("scale rung", RUNGS)]:
        if not any(a in sec.get(head, "") for a in allowed):
            problems.append(f"'{head}' names no value from the module's tables")
    if not sec.get("ai tool"):
        problems.append("'AI tool' is empty")
    rejected = re.findall(r"^- \S", sec.get("alternatives rejected", ""), re.M)
    if len(rejected) < 2:
        problems.append(f"alternatives rejected: {len(rejected)} of 2")
    evidence = sec.get("evidence", "")
    if not re.search(r"(critique\.md|shots/|audit/)", evidence):
        problems.append("'evidence' points at no file in ui-lab")
    if problems:
        return report(8, "FAIL", "rationale: one page, the four choices, two rejected", "; ".join(problems))
    report(8, "PASS", "rationale: one page, the four choices, two rejected", f"{words} words")

# 9. REDUCED MOTION ###################################

# If anything moves, the page must say what happens when the reader asked for stillness.
def check_motion():
    app = LAB / "app"
    files = [f for f in app.rglob("*") if f.suffix in (".css", ".js", ".jsx", ".tsx", ".html")] if app.exists() else []
    text = "\n".join(f.read_text(encoding="utf-8") for f in files)
    moves = re.search(r"\b(animation|transition)\s*:|from ['\"]motion|animate\(", text)
    if not moves:
        return report(9, "PASS", "reduced motion obeyed", "nothing animates")
    obeys = re.search(r"prefers-reduced-motion:\s*reduce|useReducedMotion|reducedMotion", text)
    if not obeys:
        return report(9, "FAIL", "reduced motion obeyed", "the app animates and never reads prefers-reduced-motion")
    report(9, "PASS", "reduced motion obeyed", "animates, and has a reduced-motion rule")

# 10. RUN THEM ALL ###################################

print(f"mode: {'stub (' + STUB + ')' if STUB else 'real'}; folder {LAB.relative_to(KIT.parent.parent) if STUB else LAB}")
check_brief()
check_tokens()
check_contrast()
check_audit()
check_shots()
check_states()
check_critique()
check_rationale()
check_motion()
failed = results.count("FAIL")
skipped = results.count("SKIP")
print(f"RESULT: {results.count('PASS')} passed, {failed} failed, {skipped} skipped"
      + (" (a person runs the skipped ones)" if skipped else ""))
sys.exit(1 if failed else 0)
