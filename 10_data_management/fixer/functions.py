# functions.py
# Shared fixer helpers: OpenAI-compatible chat (httpx) + tool-call JSON parsing + table chunking.
# Imported by fixer_csv.py, fixer_parcels.py, fixer_pois.py, fixer_spatial_context.py, testme.py.
# Tim Fraser

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import httpx
import pandas as pd


def resolve_fixer_root() -> Path:
    """Match testme.R: FIXER_ROOT env, else cwd if helpers exist, else cwd/10_data_management/fixer."""
    r = os.environ.get("FIXER_ROOT", "").strip()
    if r and Path(r).is_dir():
        return Path(r).resolve()
    wd = Path.cwd().resolve()
    if (wd / "functions.py").is_file() or (wd / "functions.R").is_file():
        return wd
    cand = wd / "10_data_management" / "fixer"
    if (cand / "functions.py").is_file():
        return cand.resolve()
    raise RuntimeError("Run from fixer/, dsai repo root, or set FIXER_ROOT.")


def split_df_into_row_chunks(df: pd.DataFrame, n_rows: int) -> list[pd.DataFrame]:
    """Split into consecutive row slices of size n_rows (same semantics as functions.R)."""
    nr = len(df)
    if nr == 0:
        return []
    try:
        n = int(n_rows)
    except (TypeError, ValueError):
        n = 1
    if n < 1:
        n = 1
    out: list[pd.DataFrame] = []
    s = 0
    while s < nr:
        e = min(s + n, nr)
        out.append(df.iloc[s:e].copy())
        s = e
    return out


def llm_chat_once(
    base_url: str,
    api_key: str | None,
    model: str,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    format: str | None = None,
    max_output_tokens: int | None = None,
) -> dict[str, Any]:
    """Single chat completion (OpenAI-compatible). Pass tools for tool-calling; format='json' asks for JSON in the prompt."""
    url = base_url.rstrip("/") + "/chat/completions"
    body: dict[str, Any] = {
        "model": model,
        "messages": messages,
    }
    if tools is not None and len(tools) > 0:
        body["tools"] = tools
    if format is not None and str(format).strip():
        # Old Ollama format='json' had no schema; keep it that way and ask for JSON in the prompt.
        body["messages"] = messages + [
            {"role": "user", "content": "Reply with valid JSON only."}
        ]
    if max_output_tokens is not None:
        body["max_tokens"] = int(max_output_tokens)

    headers = {"Content-Type": "application/json"}
    ak = (api_key or "").strip()
    if ak:
        headers["Authorization"] = f"Bearer {ak}"

    data: dict[str, Any] = {}
    with httpx.Client(timeout=120.0) as client:
        for wait in (2, 4, 8, None):
            resp = client.post(url, json=body, headers=headers)
            if resp.status_code in (429, 500, 503) and wait is not None:
                time.sleep(wait)
                continue
            if resp.status_code in (429, 500, 503):
                raise RuntimeError(f"Model call failed with HTTP {resp.status_code} after 3 retries.")
            resp.raise_for_status()
            data = resp.json()
            break

    choices = data.get("choices") or [{}]
    msg = choices[0].get("message") or {}
    content = msg.get("content")
    if content is None:
        content = ""
    if not isinstance(content, str):
        content = str(content)
    content = content.strip()
    return {"content": content, "message": msg, "raw": data}


def llm_settings() -> tuple[str, str, str]:
    """Read LLM_BASE_URL, LLM_MODEL and the key. A localhost base URL needs no key (sends Bearer ollama)."""
    base = os.environ.get(
        "LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai"
    ).strip()
    model = os.environ.get("LLM_MODEL", "gemini-flash-lite-latest").strip()
    if base.startswith(("http://localhost", "http://127.0.0.1")):
        key = "ollama"
    else:
        key = os.environ.get("GEMINI_API_KEY", "").strip()
        if not key:
            raise SystemExit("Set GEMINI_API_KEY in the environment or in fixer/.env (copy from .env.example).")
    return base, model, key


def parse_function_arguments(raw: Any) -> dict[str, Any]:
    """Parse tool function.arguments (string JSON or dict) into a dict."""
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        s = raw.strip()
        if not s:
            return {}
        try:
            parsed = json.loads(s)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def truncate_tool_output(s: Any, limit: int = 12000) -> str:
    """Shorten long tool outputs for the model thread."""
    t = "" if s is None else str(s)
    lim = int(limit)
    if len(t) <= lim:
        return t
    return t[: max(0, lim - 30)] + "\n...[truncated]"
