# 04_check.py
# The lab's checks: does a spoken field report become a valid, filed record?
# Course kit, module 18
#
# Topic: Checking an audio pipeline with a script
#
# Runs 03_voice_note_to_work_order in stub mode (no Whisper, no Ollama needed),
# reads the CSV it wrote, and prints one PASS / FAIL / SKIP line per check.
# Run it from the top of the course repo:
#   python3 kit/module-18/04_check.py
# Point KIT_DIR somewhere else if your copy of the kit lives elsewhere.
# Exit code 0 means every check that ran passed.

# 0. SETUP ###################################

import csv  # for reading the work-order CSV
import json  # for the broken test answer
import os  # for paths + environment
import shutil  # for finding Rscript and piper
import subprocess  # for running each script
import sys  # for this Python + the exit code
import tempfile  # for a scratch folder

KIT_DIR = os.getenv("KIT_DIR", os.path.dirname(os.path.abspath(__file__)))
AUDIO_PATH = os.getenv("AUDIO_PATH", "06_agents/06_jfk_short.wav")
REQUIRED = ["asset", "location", "problem", "priority", "safety_hazard", "action_requested"]
COLUMNS = ["recorded_at", "audio_file", "transcript"] + REQUIRED + ["status"]
PRIORITIES = ["low", "medium", "high"]

results = []  # one (status, name, detail) per check

def report(status, name, detail=""):
    results.append(status)
    print(f"{status:4}  {name}" + (f"  ({detail})" if detail else ""))


# 1. RUN THE PIPELINE IN STUB MODE #####################################

def run_pipeline(command, csv_path, extra_env=None):
    """Run one version of script 03 with both stubs on. Return the finished process."""
    env = dict(os.environ, AUDIO_STUB="1", LLM_STUB="1", AUDIO_PATH=AUDIO_PATH, WORK_ORDERS_CSV=csv_path)
    env.update(extra_env or {})
    return subprocess.run(command, capture_output=True, text=True, env=env)

def read_rows(csv_path):
    if not os.path.exists(csv_path):
        return None, []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)

scratch = tempfile.mkdtemp(prefix="m18-check-")
if not os.path.exists(AUDIO_PATH):
    print(f"FAIL  audio file not found: {AUDIO_PATH} (run from the top of the course repo)")
    sys.exit(1)


# 2. CHECKS ON THE PYTHON PIPELINE #####################################

py_csv = os.path.join(scratch, "work_orders_py.csv")
proc = run_pipeline([sys.executable, os.path.join(KIT_DIR, "03_voice_note_to_work_order.py")], py_csv)
report("PASS" if proc.returncode == 0 else "FAIL", "C1 the pipeline runs and exits cleanly",
       "" if proc.returncode == 0 else proc.stderr.strip().splitlines()[-1])

header, rows = read_rows(py_csv)
ok = header == COLUMNS and len(rows) == 1
report("PASS" if ok else "FAIL", "C2 the CSV has the agreed columns and exactly one row",
       "" if ok else f"columns={header} rows={len(rows)}")

row = rows[0] if rows else {}
bad = [f for f in REQUIRED if row.get(f, "").strip() == ""]
if row.get("priority") not in PRIORITIES:
    bad.append("priority")
if row.get("safety_hazard") not in ("True", "False"):
    bad.append("safety_hazard")
report("PASS" if row and not bad else "FAIL", "C3 every required field is filled and fits the schema",
       "" if not bad else "bad: " + ", ".join(bad))

ok = row.get("status") == "draft" and row.get("audio_file") == os.path.basename(AUDIO_PATH)
report("PASS" if ok else "FAIL", "C4 the record is a draft and names its source recording",
       "" if ok else f"status={row.get('status')} audio_file={row.get('audio_file')}")

broken = json.dumps({"asset": "Pump 3", "location": "North lift station", "problem": "Leak",
                     "priority": "urgent", "safety_hazard": "yes"})  # bad enum, bad type, a missing field
bad_csv = os.path.join(scratch, "work_orders_bad.csv")
proc = run_pipeline([sys.executable, os.path.join(KIT_DIR, "03_voice_note_to_work_order.py")], bad_csv,
                    {"LLM_STUB_JSON": broken})
ok = proc.returncode != 0 and "Work order rejected" in proc.stderr and not os.path.exists(bad_csv)
report("PASS" if ok else "FAIL", "C5 a model answer that breaks the schema is rejected and nothing is filed")


# 3. THE R PIPELINE GIVES THE SAME RECORD #####################################

if shutil.which("Rscript"):
    r_csv = os.path.join(scratch, "work_orders_r.csv")
    proc = run_pipeline(["Rscript", os.path.join(KIT_DIR, "03_voice_note_to_work_order.R")], r_csv)
    _, r_rows = read_rows(r_csv)
    same = proc.returncode == 0 and len(r_rows) == 1 and all(r_rows[0].get(c) == row.get(c) for c in REQUIRED + ["status", "audio_file"])
    report("PASS" if same else "FAIL", "C6 the R pipeline files the same record",
           "" if same else (proc.stderr.strip().splitlines() or ["no output"])[-1])
else:
    report("SKIP", "C6 the R pipeline files the same record", "Rscript is not installed")


# 4. ROUND TRIP: SPEAK, THEN TRANSCRIBE #####################################

# If Piper and faster-whisper are both installed, speak a sentence and transcribe it back.
# The key words must survive the trip. This is a test of the two models, not of your code.
def have_module(name):
    return subprocess.run([sys.executable, "-c", f"import {name}"], capture_output=True).returncode == 0

voice = os.getenv("PIPER_VOICE", "en_US-lessac-medium")
if not have_module("piper"):
    report("SKIP", "C7 round trip: spoken words come back as text", "piper-tts is not installed")
elif not have_module("faster_whisper"):
    report("SKIP", "C7 round trip: spoken words come back as text", "faster-whisper is not installed")
else:
    wav = os.path.join(scratch, "round_trip.wav")
    sentence = "Pump three at the north lift station is leaking oil."
    spoke = subprocess.run([sys.executable, "-m", "piper", "-m", voice, "-f", wav, "--", sentence],
                           capture_output=True, text=True)
    if spoke.returncode != 0 or not os.path.exists(wav):
        report("SKIP", "C7 round trip: spoken words come back as text", f"piper could not speak with voice {voice}")
    else:
        from faster_whisper import WhisperModel
        segments, _ = WhisperModel("base.en", device="cpu", compute_type="int8").transcribe(wav)
        heard = " ".join(s.text for s in segments).lower()
        missing = [w for w in ["pump", "north", "leaking", "oil"] if w not in heard]
        report("PASS" if not missing else "FAIL", "C7 round trip: spoken words come back as text",
               f"heard: {heard.strip()}" if missing else "")


# 5. SUMMARY #####################################

shutil.rmtree(scratch, ignore_errors=True)
print(f"\n{results.count('PASS')} passed, {results.count('FAIL')} failed, {results.count('SKIP')} skipped")
sys.exit(1 if "FAIL" in results else 0)
