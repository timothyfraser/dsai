# check_no_keys.py
# Check C5: no secret key in the files the browser gets, or in the repo.
# Course kit, module 22
#
# Run it over your built page and your repo:  python3 check_no_keys.py dist .
# With no arguments it scans the current folder. Prints one PASS or FAIL line. Stdlib only.

# 0. SETUP ###################################

import re   # for the key patterns
import sys  # for the arguments and the exit code
from pathlib import Path  # for walking folders

ROOTS = [Path(p) for p in (sys.argv[1:] or ["."])]
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv"}

# A publishable key may sit in a browser; a secret key may not. These shapes are secrets.
# Each pattern is built from two halves so this file does not match itself.
PATTERNS = {
    "Supabase secret key": re.compile("sb_" + "secret_[A-Za-z0-9_-]{8,}"),
    "a JWT (a legacy Supabase key is one)": re.compile("eyJ" + r"[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}"),
    "an API key assigned a value": re.compile(r"(OLLAMA|OPENAI|ANTHROPIC)_API_KEY\s*[=:]\s*['\"]?[A-Za-z0-9_-]{16,}"),
    "a private key block": re.compile("-----BEGIN " + "[A-Z ]*PRIVATE KEY-----"),
}

# 1. SCAN ###################################

hits = []
scanned = 0
for root in ROOTS:
    files = [root] if root.is_file() else [p for p in root.rglob("*") if p.is_file()]
    for path in files:
        if SKIP_DIRS & set(path.parts) or path.stat().st_size > 5_000_000:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        scanned += 1
        for name, pattern in PATTERNS.items():
            for m in pattern.finditer(text):
                line = text.count("\n", 0, m.start()) + 1
                hits.append(f"{path}:{line} {name}")  # we print where, never the value

print(f"{'PASS' if not hits else 'FAIL'}  C5 no secret key in the page or the repo  ("
      + ("; ".join(hits) if hits else f"{scanned} files scanned") + ")")
sys.exit(1 if hits else 0)
