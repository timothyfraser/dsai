# make_example.py
# Build a small example pipeline folder, good or planted-bad, for check_pipeline.py
# Course kit, module 09
#
# Topic: A fixture you can break on purpose
#
# A check you have never seen fail is a check you cannot trust. This script writes a
# tiny pipeline folder (the same layout your team's folder has) so that check_pipeline.py
# has something to check without your own server or your own data. With no flaw, every
# check should pass. With a flaw, exactly one idea is broken, and the matching check
# should say FAIL. The folder is a fixture: it is never output from your own pipeline.
#
# No python packages to install: it uses only the standard library.
#
# Run it from this folder:
#   python3 make_example.py example_good
#   python3 make_example.py example_bad --flaw duplicates
# Flaws: duplicates, stale_rows, metric_range, uncited_answer, no_model, api_down

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import argparse  # for reading the command line
import json  # for writing the model file
import os  # for making folders
import sqlite3  # for writing the ingest table
import time  # for today's date in UTC

## 0.2 Configuration #################################

FLAWS = ["duplicates", "stale_rows", "metric_range", "uncited_answer", "no_model", "api_down"]
STUB_PREDICTION = 11.4  # the number the stub server returns; check_pipeline.py uses the same one
METRO_ID = 948  # the metro the course pipeline ingests

# 1. BUILD THE FOLDER ###################################

def build(folder, flaw=None):
    data = os.path.join(folder, "data")
    os.makedirs(data, exist_ok=True)
    today = time.strftime("%Y-%m-%d", time.gmtime())
    day = today if flaw != "stale_rows" else time.strftime("%Y-%m-%d", time.gmtime(time.time() - 3 * 86400))

    # The ingest table has the same columns as the course's traffic table.
    # A primary key is what keeps repeated cron runs from storing a row twice.
    db_path = os.path.join(data, "traffic.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = sqlite3.connect(db_path)
    key = "" if flaw == "duplicates" else ", PRIMARY KEY (metro_id, monitor_id, observed_at)"
    conn.execute("CREATE TABLE traffic (metro_id INTEGER, monitor_id TEXT, observed_at TEXT, "
                 f"vehicles INTEGER, speed REAL, occupancy REAL{key})")
    rows = [(METRO_ID, m, f"{day} 00:{minute:02d}:00", 5 + minute, 40.0, 2.0)
            for m in ("STE_TD3", "CIN_TD2", "MET_TD1") for minute in range(10)]
    if flaw == "duplicates":
        rows += rows[:5]  # a cron job that ran twice and stored the same minutes again
    conn.executemany("INSERT INTO traffic VALUES (?, ?, ?, ?, ?, ?)", rows)
    conn.commit()
    conn.close()

    # The model file records a metric, so a retrain that got worse is visible later.
    if flaw != "no_model":
        rmse = 480.0 if flaw == "metric_range" else 10.3
        with open(os.path.join(data, "model.json"), "w", encoding="utf-8") as f:
            json.dump({"model": "stand-in for a saved model", "metro_id": METRO_ID,
                       "test_rmse": rmse}, f, indent=2)

    # The agent's answer has to quote the number the model's own endpoint returned.
    said = (f"The model predicts {STUB_PREDICTION} vehicles in one minute for day 1 at hour 8."
            if flaw != "uncited_answer" else "Traffic is usually heavy early in the week.")
    with open(os.path.join(data, "agent_answer.txt"), "w", encoding="utf-8") as f:
        f.write(said + "\n")

# 2. COMMAND LINE ###################################

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--flaw", choices=FLAWS)
    args = ap.parse_args()
    build(args.folder, args.flaw)
    print(f"wrote {args.folder}" + (f" with flaw: {args.flaw}" if args.flaw else ""))
