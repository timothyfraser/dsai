# FDA_trends.py
# FDA Adverse Event data: fetch, aggregate, and use Ollama to summarize trends
# Builds on FDA_good_query.python.py; Ollama usage inspired by 02_ollama.py and 03_ollama_cloud.py

import json
import os
import requests
from collections import defaultdict
from dotenv import load_dotenv

# --- Load env (FDA + optional Ollama Cloud) ---
if os.path.exists("FDA.env"):
    load_dotenv("FDA.env")
elif os.path.exists("../FDA.env"):
    load_dotenv("../FDA.env")
else:
    print("FDA.env not found. Set FDA_API_KEY in FDA.env or in your environment.")

# Also load .env for OLLAMA_API_KEY if using Ollama Cloud
load_dotenv()

FDA_API_KEY = os.getenv("FDA_API_KEY")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
BASE_URL = "https://api.fda.gov/drug/event.json"

# --- 1. Fetch FDA data ---

params = {
    "limit": 500,
    "search": "receivedate:[20230101 TO 20241231]",
    "sort": "receivedate:desc",
}

if FDA_API_KEY:
    params["api_key"] = FDA_API_KEY

try:
    response = requests.get(BASE_URL, params=params, timeout=30)
except requests.RequestException as e:
    print("Request failed:", e)
    raise

if not response.ok and response.status_code == 500:
    error_text = response.text or ""
    if "parse_exception" in error_text or "TO" in error_text:
        print("Date-range search caused API parse error; retrying with limit only.")
        params_fallback = {"limit": 500}
        if FDA_API_KEY:
            params_fallback["api_key"] = FDA_API_KEY
        response = requests.get(BASE_URL, params=params_fallback, timeout=30)
        params = params_fallback

if not response.ok:
    print("HTTP status:", response.status_code)
    response.raise_for_status()

data = response.json()
results = data.get("results", [])

if not results:
    print("No records returned. Cannot compute trends.")
    exit(0)

# --- 2. Extract and aggregate (same as before) ---

def get_drug_names_list(record):
    drugs = record.get("drug") or (record.get("patient") or {}).get("drug") or []
    names = []
    for d in (drugs if isinstance(drugs, list) else []):
        n = d.get("medicinalproduct") or d.get("brand_name")
        if n:
            names.append(str(n).strip())
    return names if names else ["(unknown)"]

def get_reaction_names_list(record):
    reactions = record.get("reaction") or (record.get("patient") or {}).get("reaction") or []
    names = []
    for r in (reactions if isinstance(reactions, list) else []):
        if isinstance(r, dict):
            n = r.get("reactionmeddrapt")
            if n:
                names.append(str(n).strip())
    return names if names else ["(unknown)"]

drug_counts = defaultdict(int)
reaction_counts = defaultdict(int)
date_counts = defaultdict(int)
drug_reaction_pairs = defaultdict(int)

for r in results:
    rec_date = r.get("receivedate") or ""
    if rec_date and len(rec_date) >= 6:
        date_counts[rec_date[:6]] += 1
    drugs = get_drug_names_list(r)
    reactions = get_reaction_names_list(r)
    for d in drugs:
        drug_counts[d] += 1
    for re in reactions:
        reaction_counts[re] += 1
    for d in drugs:
        for re in reactions:
            drug_reaction_pairs[(d, re)] += 1

def fmt_month(ym):
    return f"{ym[:4]}-{ym[4:6]}" if len(ym) == 6 else ym

sorted_months = sorted(date_counts.keys())
top_drugs = sorted(drug_counts.items(), key=lambda x: -x[1])[:15]
top_reactions = sorted(reaction_counts.items(), key=lambda x: -x[1])[:15]
top_pairs = sorted(drug_reaction_pairs.items(), key=lambda x: -x[1])[:10]

# --- 3. Build a short summary for the LLM (fewer tokens = faster, less timeout) ---

summary_for_llm = {
    "total_reports": len(results),
    "date_range": f"{fmt_month(sorted_months[0])} to {fmt_month(sorted_months[-1])}" if sorted_months else "N/A",
    "reports_by_month": {fmt_month(ym): date_counts[ym] for ym in sorted_months},
    "top_drugs": [{"drug": name, "count": c} for name, c in top_drugs[:10]],
    "top_reactions": [{"reaction": name, "count": c} for name, c in top_reactions[:10]],
    "top_drug_reaction_pairs": [
        {"drug": d, "reaction": r, "count": c} for (d, r), c in top_pairs[:6]
    ],
    "unique_drugs": len(drug_counts),
    "unique_reactions": len(reaction_counts),
}

summary_text = json.dumps(summary_for_llm, indent=2)

# --- 4. Call Ollama (local or cloud) to get narrative summary ---

SYSTEM_PROMPT = """You are a data analyst. Summarize the main trends in this FDA adverse event data using bullet points. Include:
- Top drugs and top reactions (with counts where helpful)
- Notable drug–reaction pairs
- Time trend or date-range note
- One follow-up question or recommendation
Be concise; use numbers. Format as bullet points for easy reading."""

USER_PROMPT = f"FDA adverse event summary ({len(results)} reports):\n\n{summary_text}\n\nWrite a brief trend report in bullet points."

print("\n🚀 Fetching FDA data and asking Ollama for trend summary...\n")

output = None
llm_response = None

if OLLAMA_API_KEY:
    # Ollama Cloud (chat API) — same pattern as 03_ollama_cloud.py
    print("Using Ollama Cloud (OLLAMA_API_KEY is set).")
    url = "https://ollama.com/api/chat"
    headers = {
        "Authorization": f"Bearer {OLLAMA_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": "gpt-oss:20b-cloud",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT},
        ],
        "stream": False,
    }
    try:
        llm_response = requests.post(url, headers=headers, json=body, timeout=120)
        llm_response.raise_for_status()
        output = llm_response.json()["message"]["content"]
    except requests.RequestException as e:
        print("Ollama Cloud request failed:", e)
        if llm_response is not None and getattr(llm_response, "text", None):
            print("Response body:", llm_response.text[:500])
        output = None
else:
    # Local Ollama (generate API) — same pattern as 02_ollama.py
    # Use same default model as 02_ollama.py
    LOCAL_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:latest")
    print(f"Using local Ollama (model: {LOCAL_MODEL}).")
    PORT = 11434
    url = f"http://localhost:{PORT}/api/generate"
    body = {
        "model": LOCAL_MODEL,
        "prompt": f"{SYSTEM_PROMPT}\n\n---\n\n{USER_PROMPT}",
        "stream": False,
    }
    # Longer timeout for slow/local models (e.g. 5 min)
    OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "300"))
    try:
        llm_response = requests.post(url, json=body, timeout=OLLAMA_TIMEOUT)
        llm_response.raise_for_status()
        output = llm_response.json().get("response", "")
    except requests.ConnectionError as e:
        print("Local Ollama connection failed. Is Ollama running?")
        print("  → Start it with: ollama serve")
        print("  → Then pull a model: ollama pull gemma3:latest")
        print("  Error:", e)
        output = None
    except requests.Timeout as e:
        print("Local Ollama timed out (model too slow or still loading).")
        print("  → Use a smaller/faster model: set OLLAMA_MODEL=llama3.2:1b in .env")
        print("  → Or increase wait: set OLLAMA_TIMEOUT=600 in .env")
        print("  Error:", e)
        output = None
    except requests.RequestException as e:
        print("Local Ollama request failed:", e)
        if llm_response is not None:
            try:
                err = llm_response.json()
                if "error" in err:
                    print("  Model error:", err["error"])
            except Exception:
                if getattr(llm_response, "text", None):
                    print("  Response:", llm_response.text[:300])
        if "404" in str(e):
            print("  → If Ollama is running, try: ollama pull gemma3:latest")
        print("  → Or set OLLAMA_MODEL=llama3.2:1b (smaller, faster) in .env")
        output = None

# --- 5. Print results ---

print("=" * 60)
print("FDA ADVERSE EVENT TRENDS & PATTERNS")
print("(Based on", len(results), "reports from openFDA Drug Event API)")
print("=" * 60)

if output:
    print("\n📝 OLLAMA SUMMARY (meaningful trends and patterns)\n")
    print(output)
    print("\n" + "=" * 60)
else:
    print("\n⚠️ Could not get Ollama summary. Showing aggregated stats only.\n")
    print("📅 REPORTS BY MONTH")
    print("-" * 40)
    for ym in sorted_months:
        bar = "█" * min(date_counts[ym], 40) + "░" * (40 - min(date_counts[ym], 40))
        print(f"  • {fmt_month(ym)}: {date_counts[ym]:4d} reports  {bar}")
    print("\n💊 TOP 10 DRUGS (by report count)")
    print("-" * 40)
    for name, count in top_drugs[:10]:
        print(f"  • {name}: {count}")
    print("\n⚠️ TOP 10 REACTIONS (by report count)")
    print("-" * 40)
    for name, count in top_reactions[:10]:
        print(f"  • {name}: {count}")
    print("\n🔗 TOP 5 DRUG–REACTION PAIRS")
    print("-" * 40)
    for (d, r), count in top_pairs[:5]:
        print(f"  • {d} → {r}: {count}")
    print("\n📋 SUMMARY")
    print("-" * 40)
    print(f"  • Total reports: {len(results)}")
    print(f"  • Unique drugs: {len(drug_counts)}")
    print(f"  • Unique reactions: {len(reaction_counts)}")
    if sorted_months:
        print(f"  • Date range: {fmt_month(sorted_months[0])} to {fmt_month(sorted_months[-1])}")
    print("=" * 60)

print("\n✅ Done.\n")
