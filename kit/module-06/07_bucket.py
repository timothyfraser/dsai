# 07_bucket.py
# Keep the raw file and the audit log in a private Supabase Storage bucket, and share one by a signed URL
# Pairs with 07_bucket.R
# Course kit, module 6
#
# Topic: Buckets
#
# The table now lives in Postgres. Two files do not belong in a table: the raw CSV exactly as
# it arrived, and the audit log that explains every change. This script puts both in a private
# bucket, a folder of files on Supabase Storage that nobody can read without a key, then mints
# a signed URL: a web address for one file that stops working after ten minutes.
#
# If you haven't already, install the package...
# pip install supabase
#
# Run it from the folder that holds this file, after the repair:
#   LLM_STUB=1 python3 repair_table.py
#   python3 07_bucket.py
#
# It reads two settings from the environment, never from this file:
#   SUPABASE_URL   your project's address
#   SUPABASE_KEY   the project's SECRET key (sb_secret_...). Server-side only.
# No project yet? Leave them unset and the script runs in STUB mode: it prints every request
# it would make, sends nothing, and exits 0.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import os  # for reading settings from the environment
import sys  # for exiting with a plain message
from pathlib import Path  # for file paths that work on every computer

## 0.2 Configuration #################################

HERE = Path(__file__).resolve().parent
BUCKET = "inventory-files"
EXPIRES_IN = 600  # seconds a signed URL keeps working: ten minutes

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# No address or no key means STUB mode: say so loudly, and send nothing.
STUB = not (SUPABASE_URL and SUPABASE_KEY)
if STUB:
    print("=" * 60)
    print("STUB MODE: SUPABASE_URL and SUPABASE_KEY are not set.")
    print("Nothing is sent to Supabase. This prints what the script would do.")
    print("=" * 60)

# 1. PICK WHAT GOES IN THE BUCKET ###################################

# Files go in the bucket whole. Rows you query go in the table.
# The raw CSV is evidence: kept exactly as it arrived, never edited, so the audit can replay.
FILES = {
    "raw/inventory_raw.csv": (HERE / "data" / "inventory_raw.csv", "text/csv"),
    "audit/audit.jsonl": (HERE / "output" / "audit.jsonl", "application/x-ndjson"),
}
for name, (path, _) in FILES.items():
    if not path.exists():
        sys.exit(f"No {path.name} yet. Run  LLM_STUB=1 python3 repair_table.py  first.")
    print(f"{name}: {path.stat().st_size} bytes")

# 2. MAKE SURE THE BUCKET IS PRIVATE ###################################

# A public bucket serves every file to anyone who guesses the name. Ours is private.
if STUB:
    print(f"STUB: would create bucket {BUCKET} with public = False, if it does not exist yet.")
else:
    from supabase import create_client  # for the Supabase client (only needed for a real run)

    server = create_client(SUPABASE_URL, SUPABASE_KEY)
    if BUCKET not in [b.name for b in server.storage.list_buckets()]:
        server.storage.create_bucket(BUCKET, options={"public": False})
        print(f"Created private bucket {BUCKET}.")
    else:
        print(f"Bucket {BUCKET} already exists.")

# 3. UPLOAD THE TWO FILES ###################################

# upsert = "true" replaces a file of the same name, so a second run does not fail.
for name, (path, content_type) in FILES.items():
    if STUB:
        print(f"STUB: would POST {path.name} to /storage/v1/object/{BUCKET}/{name}")
    else:
        server.storage.from_(BUCKET).upload(
            name, path, {"content-type": content_type, "upsert": "true"}
        )
        print(f"Uploaded {name}.")

# 4. MINT A SIGNED URL ###################################

# A signed URL lets one person fetch one file without a key, until it expires.
# Send the link, never the key.
if STUB:
    print(f"STUB: would POST to /storage/v1/object/sign/{BUCKET}/raw/inventory_raw.csv")
    print(f"      with expiresIn = {EXPIRES_IN}, and print the link it returns.")
else:
    signed = server.storage.from_(BUCKET).create_signed_url("raw/inventory_raw.csv", EXPIRES_IN)
    print(f"Signed URL, good for {EXPIRES_IN // 60} minutes:")
    print(signed["signedURL"])
