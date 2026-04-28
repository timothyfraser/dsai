# api_client.py
# FDA Drug Event API client and record helpers
# Pairs with app.py (Shiny reporter). Loads env from FDA.env or .env.

import os
from pathlib import Path

import pandas as pd
import requests

# Load API key from FDA.env or .env (search upward from this file)
_here = Path(__file__).resolve().parent
for parent in [_here, _here.parent, _here.parent.parent]:
    for name in ("FDA.env", ".env"):
        env_file = parent / name
        if env_file.exists():
            from dotenv import load_dotenv
            load_dotenv(env_file)
            break

BASE_URL = "https://api.fda.gov/drug/event.json"


def _drug_names(record, max_len=80):
    """First product name(s) from record. Drug list may be under patient."""
    drugs = record.get("drug") or (record.get("patient") or {}).get("drug") or []
    names = []
    for d in (drugs[:3] if isinstance(drugs, list) else []):
        n = d.get("medicinalproduct") or d.get("brand_name") or "—"
        names.append(str(n)[:30] if n else "—")
    s = ", ".join(names)[:max_len]
    return s + "..." if len(s) >= max_len else (s or "—")


def _reaction_names(record, max_len=80):
    """First reaction term(s) from record. Reaction list may be under patient."""
    reactions = record.get("reaction") or (record.get("patient") or {}).get("reaction") or []
    if not reactions:
        return "—"
    names = [r.get("reactionmeddrapt", "?") for r in reactions[:3] if isinstance(r, dict)]
    s = ", ".join(names)[:max_len]
    return s + "..." if len(s) >= max_len else s


def record_to_row(record):
    """Turn one FDA event record into a flat dict for table display."""
    return {
        "Receive date": record.get("receivedate", "—"),
        "Report ID": record.get("safetyreportid") or record.get("report_num") or "—",
        "Drug(s)": _drug_names(record),
        "Reaction(s)": _reaction_names(record),
    }


def get_fda_events(limit=50, search_expr=None, sort="receivedate:desc", api_key=None, timeout=30):
    """
    Fetch adverse event reports from the openFDA Drug Event API.

    Parameters
    ----------
    limit : int
        Max records to return (1–1000).
    search_expr : str or None
        Optional search expression (e.g. receivedate:[20230101 TO 20241231]).
    sort : str
        Sort field and order (default receivedate:desc).
    api_key : str or None
        Optional API key for higher rate limits.
    timeout : int
        Request timeout in seconds.

    Returns
    -------
    dict
        On success: {"ok": True, "meta": meta, "results": list of records, "df": DataFrame}.
        On failure: {"ok": False, "error": str}.
    """
    limit = max(1, min(1000, int(limit)))
    params = {"limit": limit, "sort": sort}
    if api_key:
        params["api_key"] = api_key
    if search_expr and search_expr.strip():
        params["search"] = search_expr.strip()

    try:
        response = requests.get(BASE_URL, params=params, timeout=timeout)
    except requests.RequestException as e:
        return {"ok": False, "error": f"Request failed: {e}"}

    if response.status_code == 500:
        # Fallback: retry without search (API parse errors on some date ranges)
        params_fallback = {"limit": limit, "sort": sort}
        if api_key:
            params_fallback["api_key"] = api_key
        try:
            response = requests.get(BASE_URL, params=params_fallback, timeout=timeout)
        except requests.RequestException as e:
            return {"ok": False, "error": f"Request failed: {e}"}

    if not response.ok:
        return {
            "ok": False,
            "error": f"HTTP {response.status_code}: {(response.text or '')[:300]}",
        }

    try:
        data = response.json()
    except Exception as e:
        return {"ok": False, "error": f"Invalid JSON: {e}"}

    meta = data.get("meta", {})
    results = data.get("results", [])
    rows = [record_to_row(r) for r in results]
    df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["Receive date", "Report ID", "Drug(s)", "Reaction(s)"])

    return {
        "ok": True,
        "meta": meta,
        "results": results,
        "df": df,
    }


def get_api_key():
    """Return FDA_API_KEY from environment."""
    return os.getenv("FDA_API_KEY") or ""
