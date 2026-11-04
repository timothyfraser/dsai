# check.py
# The lab's checks for photo_to_record, run without a model
# Course kit, module 17
#
# Topic: Visual Language Models
#
# This script runs photo_to_record (R, Python, or both) in stub mode,
# so no model and no key are needed, and prints one line per check.
# When every line says PASS, the tool does what the lab asks.
#
# Run it from the top of the course repo, so the image path resolves:
#   python check.py            # both languages
#   python check.py --lang py  # Python only
#   python check.py --lang r   # R only
#
# Uses only the Python standard library.

# 0. SETUP ###################################

import argparse  # for the --lang option
import csv  # for reading the CSV the tool writes
import json  # for reading the schema
import os  # for paths
import shutil  # for finding Rscript
import subprocess  # for running the tool
import sys  # for the exit code
import tempfile  # for a scratch folder, so the check never touches your own CSV

HERE = os.path.dirname(os.path.abspath(__file__))
IMAGE = os.environ.get("CHECK_IMAGE", "06_agents/05_coffeeshop_small.jpg")
SCHEMA_PATH = os.environ.get("RECORD_SCHEMA", os.path.join(HERE, "record_schema.json"))

with open(SCHEMA_PATH, encoding="utf-8") as f:
    schema = json.load(f)
fields = schema["fields"]
columns = ["photo", "model"] + [f["name"] for f in fields]


# 1. RUN THE TOOL ONCE #################################

def run_tool(lang, stub, csv_path):
    """Run photo_to_record in one language with one stub reply. Returns the exit code."""
    env = dict(os.environ, VLM_STUB=stub)
    if lang == "py":
        cmd = [sys.executable, os.path.join(HERE, "photo_to_record.py"), IMAGE, csv_path]
    else:
        cmd = ["Rscript", os.path.join(HERE, "photo_to_record.R"), IMAGE, csv_path]
    done = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=120)
    return done.returncode, done.stdout + done.stderr


def read_rows(csv_path):
    if not os.path.exists(csv_path):
        return None, []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)


# 2. CHECK ONE VALUE AGAINST ITS FIELD #######################

def value_ok(field, value):
    if field.get("allow_unknown") and value == "unknown":
        return True
    if field["type"] == "integer":
        return value.isdigit()
    if field["type"] == "choice":
        return value in field["choices"]
    return value != ""


# 3. THE CHECKS #################################

def check_lang(lang):
    results = []
    folder = tempfile.mkdtemp(prefix="m17_check_")
    csv_path = os.path.join(folder, "records.csv")

    code, out = run_tool(lang, "1", csv_path)
    results.append(("C1", "a clean reply runs and exits 0", code == 0, out))

    header, rows = read_rows(csv_path)
    results.append(("C2", "the CSV has exactly the required columns, in order", header == columns,
                    f"got {header}"))

    typed = len(rows) == 1 and all(value_ok(f, rows[0].get(f["name"], "")) for f in fields)
    results.append(("C3", "one row, and every value has its schema type", typed, f"rows: {rows}"))

    # The clean stub reply holds at least one "unknown"; it must reach the CSV unchanged.
    kept = len(rows) == 1 and "unknown" in rows[0].values()
    results.append(("C4", "\"unknown\" is kept as unknown, never filled in", kept, f"rows: {rows}"))

    code_g, out_g = run_tool(lang, "guess", csv_path)
    _, rows_g = read_rows(csv_path)
    results.append(("C5", "a guess (\"about 9\") is refused and adds no row",
                    code_g != 0 and len(rows_g) == 1, out_g))

    code_m, out_m = run_tool(lang, "mismatch", csv_path)
    _, rows_m = read_rows(csv_path)
    results.append(("C6", "counts that do not add up are refused and add no row",
                    code_m != 0 and len(rows_m) == 1, out_m))

    shutil.rmtree(folder, ignore_errors=True)
    return results


# 4. PRINT ONE LINE PER CHECK #################################

parser = argparse.ArgumentParser()
parser.add_argument("--lang", choices=["py", "r", "both"], default="both")
langs = ["py", "r"] if parser.parse_args().lang == "both" else [parser.parse_args().lang]

if not os.path.exists(IMAGE):
    print(f"FAIL  the photo {IMAGE} is not here. Run this from the top of the course repo.")
    sys.exit(1)

failed = 0
for lang in langs:
    if lang == "r" and shutil.which("Rscript") is None:
        print("SKIP  R: Rscript is not on this computer")
        continue
    for cid, text, ok, detail in check_lang(lang):
        print(f"{'PASS' if ok else 'FAIL'}  {lang:<2} {cid} {text}")
        if not ok:
            failed += 1
            print("      " + detail.strip().replace("\n", "\n      ")[:1500])

print(f"\n{'All checks pass.' if failed == 0 else str(failed) + ' check(s) failed.'}")
sys.exit(1 if failed else 0)
