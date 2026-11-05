# check_lineage.py
# Check C4: one number is the same in the store, in the API and on the page.
# Course kit, module 22
#
# Run it from your team folder:
#   LINEAGE_STUB=1 python3 check_lineage.py   # stub mode: replays the saved store, response and page
#   python3 check_lineage.py                  # live: your database, your API, your page
# It reads lineage.yaml (flat "key: value" lines). Live mode reads a SQLite file (store_db) or,
# when DATABASE_URL is set and psycopg is installed, Postgres. The page hop uses Playwright if it
# is installed; without it that hop is skipped with the reason printed. Stdlib only otherwise.

# 0. SETUP ###################################

import html.parser  # for reading a saved page
import json         # for the API response
import os           # for the stub switch and DATABASE_URL
import sqlite3      # for the store hop
import sys          # for the exit code
import urllib.request  # for the live API hop
from pathlib import Path  # for file paths

TEAM = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
STUB = os.environ.get("LINEAGE_STUB") == "1"

def read_flat_yaml(path):
    """Read 'key: value' lines; a line that starts with # is a comment."""
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#") and ": " in line:
            key, value = line.split(": ", 1)
            out[key.strip()] = value.strip()
    return out

spec = read_flat_yaml(TEAM / "lineage.yaml")
tolerance = float(spec.get("tolerance", "0"))

# 1. THE STORE HOP ###################################

# The store is where the number is defined, so the SQL here is the definition.
def store_value():
    if STUB:
        con = sqlite3.connect(":memory:")
        con.executescript((TEAM / spec["store_seed"]).read_text(encoding="utf-8"))
        return con.execute(spec["store_sql"]).fetchone()[0], "saved store"
    if os.environ.get("DATABASE_URL"):
        try:
            import psycopg  # for Postgres; pip install psycopg[binary]
        except ImportError:
            return None, "skipped: DATABASE_URL is set but psycopg is not installed"
        with psycopg.connect(os.environ["DATABASE_URL"]) as con:
            return con.execute(spec["store_sql"]).fetchone()[0], "Postgres"
    # Open read-only, so a wrong path is an error and not a new empty database.
    con = sqlite3.connect(f"file:{TEAM / spec['store_db']}?mode=ro", uri=True)
    return con.execute(spec["store_sql"]).fetchone()[0], spec["store_db"]

# 2. THE API HOP ###################################

def api_value():
    if STUB:
        body = (TEAM / spec["api_saved"]).read_text(encoding="utf-8")
        where = spec["api_saved"]
    else:
        with urllib.request.urlopen(spec["api_url"], timeout=20) as r:
            body = r.read().decode("utf-8")
        where = spec["api_url"]
    return json.loads(body)[spec["api_field"]], where

# 3. THE PAGE HOP ###################################

class ById(html.parser.HTMLParser):
    """Collect the text inside the element whose id the selector names."""
    def __init__(self, wanted):
        super().__init__()
        self.wanted, self.depth, self.text = wanted, 0, ""
    def handle_starttag(self, tag, attrs):
        if self.depth or dict(attrs).get("id") == self.wanted:
            self.depth += 1
    def handle_endtag(self, tag):
        self.depth = max(self.depth - 1, 0)
    def handle_data(self, data):
        if self.depth:
            self.text += data

def page_value():
    selector = spec["page_selector"]
    if STUB:
        if not selector.startswith("#"):
            return None, "skipped: stub mode reads an id selector such as #vehicles-total"
        p = ById(selector[1:])
        p.feed((TEAM / spec["page_saved"]).read_text(encoding="utf-8"))
        return p.text.strip(), spec["page_saved"]
    try:
        from playwright.sync_api import sync_playwright  # for a real browser
    except ImportError:
        return None, "skipped: playwright is not installed (pip install playwright; playwright install chromium)"
    # The page is read in a real browser, because the number a person sees is drawn by its code.
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.goto(spec["page_url"])
        text = page.locator(selector).first.inner_text(timeout=15000)
        browser.close()
    return text.strip(), spec["page_url"]

# 4. COMPARE ###################################

def as_number(v):
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None

hops = []
for name, fn in (("store", store_value), ("api", api_value), ("page", page_value)):
    try:
        value, where = fn()
    except Exception as err:  # a hop that cannot be read is a failed hop, named
        value, where = None, f"error: {err}"
    hops.append((name, value, where))
    shown = where if value is None else f"{value} from {where}"
    print(f"   {name:5} {shown}")

read = [(n, as_number(v)) for n, v, w in hops if v is not None]
skipped = [n for n, v, w in hops if v is None and w.startswith("skipped")]
errors = [f"{n}: {w}" for n, v, w in hops if v is None and not w.startswith("skipped")]
# The store and the API must both be read; a skipped page hop is allowed and is said out loud.
ok = (not errors and {"store", "api"} <= {n for n, _ in read}
      and all(x is not None for _, x in read)
      and max(x for _, x in read) - min(x for _, x in read) <= tolerance)
detail = "; ".join(errors) if errors else ", ".join(f"{n} {x:g}" for n, x in read if x is not None)
if skipped:
    detail += f"; skipped: {', '.join(skipped)}"
print(f"{'PASS' if ok else 'FAIL'}  C4 one number agrees at store, API and page  ({spec.get('number', '')}: {detail})")
sys.exit(0 if ok else 1)
