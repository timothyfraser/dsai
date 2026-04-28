# FDA_query.python.py
# FDA Open Data API: filtered adverse-event query 

# STAGE 1: DESIGN QUERY
# API name:     openFDA Drug Event API (FAERS – FDA Adverse Event Reporting System)
# Endpoint:     https://api.fda.gov/drug/event.json
# Query type:  Filtered data (date range) returning multiple records for analysis.

# Planned parameters:
#   - api_key:  Required for higher rate limits; loaded from FDA.env.
#   - limit:    20 (max 1000 per request).
#   - search:   receivedate:[20230101+TO+20241231] to restrict to 2023–2024.
#   - sort:     receivedate:desc to get most recent first.


import os  # for reading environment variables
import requests  # for HTTP GET request
from dotenv import load_dotenv  # for loading variables from .env


if os.path.exists("FDA.env"):
    load_dotenv("FDA.env")
elif os.path.exists("../FDA.env"):
    load_dotenv("../FDA.env")
else:
    print("FDA.env not found. Set FDA_API_KEY in FDA.env or in your environment.")

FDA_API_KEY = os.getenv("FDA_API_KEY")

# STAGE 2: IMPLEMENT QUERY


BASE_URL = "https://api.fda.gov/drug/event.json"

# Date range: use space around TO (API returns parse_exception with +TO+)
params = {
    "limit": 15,
    "search": "receivedate:[20230101 TO 20241231]",  # filter: 2023–2024
    "sort": "receivedate:desc",
}

if FDA_API_KEY:
    params["api_key"] = FDA_API_KEY

## 2. Make GET Request with Error Handling ###########################

try:
    response = requests.get(BASE_URL, params=params, timeout=30)
except requests.RequestException as e:
    print("Request failed:", e)
    raise

# If date-range search causes 500 parse_exception, retry with limit only (no search)
if not response.ok and response.status_code == 500:
    error_text = response.text or ""
    if "parse_exception" in error_text or "TO" in error_text:
        print("Date-range search caused API parse error; retrying with limit=15 only.")
        params_fallback = {"limit": 15}
        if FDA_API_KEY:
            params_fallback["api_key"] = FDA_API_KEY
        response = requests.get(BASE_URL, params=params_fallback, timeout=30)
        params = params_fallback  # for summary output

# Only parse JSON when the request succeeded
if not response.ok:
    print("HTTP status:", response.status_code)
    print("Response text (first 500 chars):", (response.text[:500] if response.text else "(empty)"))
    response.raise_for_status()

data = response.json()


# STAGE 3: DOCUMENT RESULTS
# Expected data structure (openFDA drug/event):
#   - meta:  { "disclaimer", "terms", "license", "last_updated", "results": { "skip", "limit", "total" } }
#   - results:  list of adverse-event reports (each is one record).
#
# Number of records:  meta.results.limit (requested) and len(results) (returned).
#   - total:  meta.results.total = total matching the search (may be large).
#   - returned:  len(data["results"]) = number of rows in this response (up to limit).
#
# Key fields per record (each item in results):
#   - receive_date:     when FDA received the report (YYYYMMDD).
#   - patient:         age, sex, weight, etc. (optional).
#   - drugs:           list of products (brand_name, medicinalproduct, etc.).
#   - reactions:       list of reactions (e.g. reactionmeddrapt).
#   - report_num:      safety report ID.

meta = data.get("meta", {})
results_info = meta.get("results", {})
total_matching = results_info.get("total", 0)
skip_count = results_info.get("skip", 0)
limit_requested = results_info.get("limit", 0)

results = data.get("results", [])
num_records = len(results)


def _drug_names(record, max_len=40):
    """First product name(s) from record, truncated. Drug list may be under patient."""
    drugs = record.get("drug") or (record.get("patient") or {}).get("drug") or []
    names = []
    for d in (drugs[:2] if isinstance(drugs, list) else []):
        n = d.get("medicinalproduct") or d.get("brand_name") or "?"
        names.append(str(n)[:25] if n else "?")
    s = ", ".join(names)[:max_len]
    return s + "..." if len(s) >= max_len else (s or "—")


def _reaction_names(record, max_len=35):
    """First reaction term(s) from record, truncated. Reaction list may be under patient."""
    reactions = record.get("reaction") or (record.get("patient") or {}).get("reaction") or []
    if not reactions:
        return "—"
    names = [r.get("reactionmeddrapt", "?") for r in reactions[:2] if isinstance(r, dict)]
    s = ", ".join(names)[:max_len]
    return s + "..." if len(s) >= max_len else s


# --- Summary (compact) ---
print("QUERY SUMMARY")
print("  Status:", response.status_code, "| Records returned:", num_records, "| Total matching:", total_matching)
print("")

if not results:
    print("No records returned (filter may be too strict or API changed).")
else:
    # --- Table: one line per record (easy to scan) ---
    print("RECORDS (date | report_id | drug(s) | reaction(s))")
    print("  " + "-" * 88)
    for r in results:
        rec_date = r.get("receivedate", "—")
        report_id = (r.get("safetyreportid") or r.get("report_num") or "—")
        drugs = _drug_names(r)
        reactions = _reaction_names(r)
        print(f"  {rec_date}  {report_id:12}  {drugs:40}  {reactions}")
    print("")

    # --- One example record (key fields only, compact) ---
    first = results[0]
    print("EXAMPLE RECORD (first)")
    print("  receivedate:", first.get("receivedate"))
    print("  safetyreportid:", first.get("safetyreportid"))
    patient = first.get("patient") or {}
    if patient:
        print("  patient: sex=", patient.get("patientsex"), " age=", patient.get("patientonsetage"), sep="")
    drugs = first.get("drug") or (first.get("patient") or {}).get("drug") or []
    print("  drugs:", len(drugs), "→", _drug_names(first, max_len=60))
    reactions = first.get("reaction") or (first.get("patient") or {}).get("reaction") or []
    print("  reactions:", len(reactions), "→", _reaction_names(first, max_len=60))
