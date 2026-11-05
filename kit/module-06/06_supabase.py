# 06_supabase.py
# Put the cleaned inventory in Postgres on Supabase, behind a row-level security policy
# Pairs with 06_supabase.R
# Course kit, module 6
#
# Topic: Postgres on Supabase
#
# This script takes the cleaned table that repair_table.py stored in SQLite and puts it in a
# hosted Postgres database on Supabase. It writes the SQL that creates the table and its one
# access rule, inserts the 30 rows with the secret key, then reads the table twice: once with
# the secret key and once with the publishable key a web page would use.
#
# If you haven't already, install the package...
# pip install supabase
#
# Run it from the folder that holds this file, after the repair:
#   LLM_STUB=1 python3 repair_table.py
#   python3 06_supabase.py
#
# It reads three settings from the environment, never from this file:
#   SUPABASE_URL   your project's address, from the project's Connect dialog
#   SUPABASE_KEY   the project's SECRET key (sb_secret_...). Server-side only.
#   SUPABASE_PUBLISHABLE_KEY  optional: the publishable key (sb_publishable_...), for section 4
# No project yet? Leave SUPABASE_URL and SUPABASE_KEY unset and the script runs in STUB mode:
# it prints the SQL and every request it would make, sends nothing, and exits 0.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import os  # for reading settings from the environment
import sqlite3  # for reading the cleaned table repair_table.py wrote
import sys  # for exiting with a plain message
from pathlib import Path  # for file paths that work on every computer

## 0.2 Configuration #################################

HERE = Path(__file__).resolve().parent
DB_PATH = HERE / "output" / "inventory.db"
SQL_PATH = HERE / "output" / "06_inventory.sql"
TABLE = "inventory"

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
SUPABASE_PUBLISHABLE_KEY = os.environ.get("SUPABASE_PUBLISHABLE_KEY", "")

# No address or no key means STUB mode: say so loudly, and send nothing.
STUB = not (SUPABASE_URL and SUPABASE_KEY)
if STUB:
    print("=" * 60)
    print("STUB MODE: SUPABASE_URL and SUPABASE_KEY are not set.")
    print("Nothing is sent to Supabase. This prints what the script would do.")
    print("=" * 60)

# The secret key skips every access rule, so it must never sit in a page.
# Anything named VITE_ is printed into the page's public JavaScript; a secret key never may be.
if SUPABASE_KEY.startswith("sb_publishable_"):
    sys.exit("SUPABASE_KEY holds a publishable key. Section 3 writes rows, so it needs the secret key.")

# 1. WRITE THE TABLE AND ITS POLICY AS SQL ###################################

# The same rules as the SQLite table in repair_table.py, now enforced by Postgres.
# The web API cannot create tables, so you run this once in the project's SQL editor.
SQL = """create table if not exists public.inventory (
  row_id integer primary key,
  sku text not null,
  qty_on_hand integer check (qty_on_hand is null or qty_on_hand > 0),
  last_restock date,
  category text check (category is null or category in ('Electronics', 'Food'))
);

-- New tables may get no grants by default (Supabase is making access opt-in), so grant it here.
-- Grants decide which roles reach the table at all; the policy below decides which rows.
grant select, insert, update on public.inventory to service_role;
grant select on public.inventory to anon;

-- Row-level security: with it on, a key that does not skip the rules sees no rows
-- and may write none, until a policy allows something.
alter table public.inventory enable row level security;

-- One policy: the public page may read rows whose count is known. No policy allows writes.
create policy "page reads counted rows"
  on public.inventory for select
  to anon
  using (qty_on_hand is not null);
"""

SQL_PATH.parent.mkdir(exist_ok=True)
SQL_PATH.write_text(SQL, encoding="utf-8")
print(f"Wrote {SQL_PATH.name}. Paste it into the SQL editor of your Supabase project once.")

# 2. LOAD THE CLEANED ROWS ###################################

if not DB_PATH.exists():
    sys.exit("No output/inventory.db yet. Run  LLM_STUB=1 python3 repair_table.py  first.")

con = sqlite3.connect(DB_PATH)
con.row_factory = sqlite3.Row
rows = [dict(r) for r in con.execute("SELECT * FROM inventory ORDER BY row_id")]
con.close()
print(f"Loaded {len(rows)} cleaned rows from {DB_PATH.name}.")
counted = sum(1 for r in rows if r["qty_on_hand"] is not None)

# 3. INSERT WITH THE SECRET KEY ###################################

# Upsert, not insert: run the script twice and you still have 30 rows, not 60.
if STUB:
    print(f"STUB: would POST {len(rows)} rows to /rest/v1/{TABLE} with the secret key,")
    print("      Prefer: resolution=merge-duplicates, so a second run changes nothing.")
    print(f"STUB: first row would be row_id {rows[0]['row_id']}, sku {rows[0]['sku']}, "
          f"qty_on_hand {rows[0]['qty_on_hand']}, category {rows[0]['category']}")
else:
    from supabase import create_client  # for the Supabase client (only needed for a real run)

    server = create_client(SUPABASE_URL, SUPABASE_KEY)
    server.table(TABLE).upsert(rows).execute()
    print(f"Upserted {len(rows)} rows into {TABLE} with the secret key.")

# 4. READ WITH EACH KEY ###################################

# The secret key skips row-level security, so it sees every row.
# The publishable key is the one a page may hold, so it sees only what the policy allows.
if STUB:
    print(f"STUB: a read with the secret key would return {len(rows)} rows (it skips the policy).")
    print(f"STUB: a read with the publishable key would return {counted} rows (rows with a count).")
    print("STUB: a write with the publishable key would be refused: no policy allows it.")
else:
    seen = server.table(TABLE).select("row_id").execute().data
    print(f"Secret key reads {len(seen)} rows.")
    if not SUPABASE_PUBLISHABLE_KEY:
        print("SKIP: set SUPABASE_PUBLISHABLE_KEY to compare the read a page would make.")
    else:
        page = create_client(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY)
        seen = page.table(TABLE).select("row_id").execute().data
        print(f"Publishable key reads {len(seen)} rows. The policy expects {counted}.")
        try:
            page.table(TABLE).insert({"row_id": 999, "sku": "TEST"}).execute()
            print("WARNING: the publishable key could write a row. Check the policies.")
        except Exception as err:  # the database refuses, and the client raises
            print(f"Publishable key write refused, as it should be: {str(err)[:80]}")
