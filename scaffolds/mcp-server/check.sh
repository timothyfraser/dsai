#!/usr/bin/env bash
# check.sh
# Proves the eight Push 4 waypoints (W1-W8), one line each
#
# NEW for the push (not part of the 2026 course files). It starts the course's
# own MCP server exactly as its README says, talks JSON-RPC to it, runs the
# new CLI door beside it, reads your files, and prints `Wn PASS|FAIL|SKIP <reason>`.
#
# Usage (from this folder):
#   bash check.sh                      # R track (default): mcp_plumber/
#   bash check.sh --lang python        # Python track: mcp_fastapi/
#   bash check.sh --remote             # also W5: ping your deployed MCP_URL
#   bash check.sh --scaffold-selftest  # the scaffold as shipped: one tool is expected
#
# Exit 0 only if no line says FAIL. The server is always killed on exit.
#
# Needs: bash, curl, python3 (for JSON parsing), plus your track's runtime.
# Arguments for W2 come from check-args.json: add your own tool's example there.

set -u

LANG_TRACK="r"
REMOTE=0
SELFTEST=0
while [ $# -gt 0 ]; do
  case "$1" in
    --lang) LANG_TRACK="${2:-}"; shift 2 ;;
    --lang=*) LANG_TRACK="${1#--lang=}"; shift ;;
    --remote) REMOTE=1; shift ;;
    --scaffold-selftest) SELFTEST=1; shift ;;
    -h|--help) sed -n '2,18p' "$0"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

if ! command -v python3 >/dev/null 2>&1; then
  echo "check.sh needs python3 (only to parse JSON)." >&2; exit 2
fi

TMP="$(mktemp -d)"
SERVER_PID=""
cleanup() {
  if [ -n "$SERVER_PID" ]; then
    pkill -P "$SERVER_PID" 2>/dev/null
    kill "$SERVER_PID" 2>/dev/null
    wait "$SERVER_PID" 2>/dev/null
  fi
  rm -rf "$TMP"
}
trap cleanup EXIT INT TERM

FAILS=0
say() {  # say W1 PASS "reason"
  echo "$1 $2 ${3:-}"
  [ "$2" = "FAIL" ] && FAILS=$((FAILS + 1))
  return 0
}

# ── Track setup ──────────────────────────────────────────────
# DIR is the course's folder, copied unchanged. SERVER is the file that holds
# TOOLS + run_tool(); CLI is the one new file beside it.
case "$LANG_TRACK" in
  r)      DIR="mcp_plumber"; SERVER="plumber.R"; CLI_FILE="cli.R";  CLI=(Rscript "$DIR/cli.R") ;;
  python) DIR="mcp_fastapi"; SERVER="server.py"; CLI_FILE="cli.py"; CLI=(python3 "$DIR/cli.py") ;;
  *) echo "--lang must be r or python" >&2; exit 2 ;;
esac

PORT="$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1]); s.close()')"
URL="http://127.0.0.1:${PORT}/mcp"

# No __pycache__ left behind in the course folder.
export PYTHONDONTWRITEBYTECODE=1

# Start the server the way the course README does, from inside its folder.
# R: plumber.R uses `%||%`, base R only from 4.4, so on an older R it is
# defined first in the same Rscript -e call. plumber.R itself is not touched.
if [ "$LANG_TRACK" = "r" ]; then
  ( cd "$DIR" && exec Rscript -e "if (!exists('%||%', mode = 'function')) \`%||%\` <- function(x, y) if (is.null(x)) y else x; plumber::plumb('plumber.R')\$run(host = '127.0.0.1', port = ${PORT})" ) >"$TMP/server.log" 2>&1 &
else
  ( cd "$DIR" && exec python3 -m uvicorn server:app --host 127.0.0.1 --port "$PORT" ) >"$TMP/server.log" 2>&1 &
fi
SERVER_PID=$!

rpc() {  # rpc <url> <json body> [extra curl args...]
  local url="$1" body="$2"; shift 2
  curl -sS -m 30 -X POST "$url" -H "Content-Type: application/json" "$@" -d "$body"
}

UP=0
for _ in $(seq 1 90); do
  if rpc "$URL" '{"jsonrpc":"2.0","id":0,"method":"ping"}' 2>/dev/null | grep -q '"result"'; then UP=1; break; fi
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then break; fi
  sleep 0.5
done

# server.py downloads mtcars/iris from vincentarelbundock.github.io when it is
# imported. Offline (or behind a proxy that blocks it) it cannot start: that is
# the environment, not your code, so W1-W3 SKIP with the reason instead of FAIL.
DATA_HOST="vincentarelbundock.github.io"
OFFLINE=0
if [ "$UP" -ne 1 ]; then
  if [ "$LANG_TRACK" = "python" ] && grep -qE "HTTPError|URLError|Forbidden|Name or service|urlopen|ProxyError" "$TMP/server.log"; then
    OFFLINE=1
    REASON="server.py could not download its datasets from $DATA_HOST at import ($(grep -oE 'urlopen error [^>]*|HTTP Error [0-9]+[^>]*' "$TMP/server.log" | head -1)); needs that host reachable"
    for w in W1 W2 W3; do say "$w" SKIP "$REASON"; done
  else
    echo "local server did not start on port $PORT. Last log lines:" >&2
    tail -20 "$TMP/server.log" >&2
    for w in W1 W2 W3; do say "$w" FAIL "local MCP server did not start (see log above)"; done
  fi
fi

# Pull one value out of JSON with python3: py_json <file> <python expression on d>
py_json() { python3 -c "import json,sys; d=json.load(open(sys.argv[1])); $2" "$1"; }

# ── W1: tools/list = his tool plus yours, each valid ─────────
if [ "$UP" -eq 1 ]; then
  rpc "$URL" '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' >"$TMP/list.json"
  W1="$(python3 - "$TMP/list.json" "$SELFTEST" <<'PY'
import json, sys
# The parts of JSON Schema an MCP client relies on.
selftest = sys.argv[2] == "1"
try:
    tools = json.load(open(sys.argv[1]))["result"]["tools"]
except Exception as e:
    print(f"FAIL tools/list did not return result.tools ({e})"); sys.exit()
probs = []
names = [t.get("name") for t in tools]
if "summarize_dataset" not in names:
    probs.append("summarize_dataset (the course's tool) is missing")
note = ""
if len(tools) < 2:
    if selftest and names == ["summarize_dataset"]:
        note = " (selftest: the course's single tool, as shipped; a team adds its own)"
    else:
        probs.append(f"expected at least 2 tools (the course's + yours), got {len(tools)}: add yours to TOOLS and run_tool() (CONTRACT.yaml T1)")
for t in tools:
    n = t.get("name") or "?"
    if not isinstance(t.get("name"), str) or not t["name"].strip(): probs.append("a tool has no name")
    if not isinstance(t.get("description"), str) or not t["description"].strip(): probs.append(f"{n}: empty description")
    s = t.get("inputSchema")
    if not isinstance(s, dict) or s.get("type") != "object": probs.append(f"{n}: inputSchema.type must be 'object'"); continue
    props = s.get("properties", {})
    if not isinstance(props, dict): probs.append(f"{n}: properties must be an object"); continue
    for k, v in props.items():
        if not isinstance(v, dict) or "type" not in v: probs.append(f"{n}.{k}: property needs a type")
    req = s.get("required", [])
    if not isinstance(req, list) or any(r not in props for r in req): probs.append(f"{n}: required must list existing properties")
print("FAIL " + "; ".join(probs) if probs else f"PASS {len(tools)} tool(s): " + ", ".join(names) + note)
PY
)"
  say W1 "${W1%% *}" "${W1#* }"
  py_json "$TMP/list.json" 'print("\n".join(t["name"] for t in d["result"]["tools"]))' >"$TMP/mcp_names.txt" 2>/dev/null
fi
touch "$TMP/mcp_names.txt"

# ── W2: tools/call each tool → isError false, non-empty text ─
if [ "$UP" -eq 1 ]; then
  W2_FAIL=""; W2_OK=""
  while IFS= read -r tool; do
    [ -z "$tool" ] && continue
    if ! python3 -c 'import json,sys; sys.exit(0 if sys.argv[1] in json.load(open("check-args.json")) else 1)' "$tool" 2>/dev/null; then
      W2_FAIL="$W2_FAIL; $tool has no example in check-args.json (CONTRACT.yaml T1)"; continue
    fi
    args="$(python3 -c 'import json,sys; print(json.dumps(json.load(open("check-args.json"))[sys.argv[1]]))' "$tool")"
    printf '%s' "$args" >"$TMP/args_$tool.json"
    body="$(python3 -c 'import json,sys; print(json.dumps({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":sys.argv[1],"arguments":json.loads(sys.argv[2])}}))' "$tool" "$args")"
    rpc "$URL" "$body" >"$TMP/call_$tool.json"
    verdict="$(py_json "$TMP/call_$tool.json" '
r = d.get("result") or {}
c = r.get("content") or [{}]
txt = c[0].get("text") or ""
if "error" in d: print("ERR jsonrpc error: " + d["error"].get("message", ""))
elif r.get("isError"): print("ERR isError: " + txt[:120])
elif not txt.strip(): print("ERR empty text block")
else: print("OK")')"
    if [ "$verdict" = "OK" ]; then W2_OK="$W2_OK $tool"; else W2_FAIL="$W2_FAIL; $tool ${verdict#ERR }"; fi
  done <"$TMP/mcp_names.txt"
  if [ -n "$W2_FAIL" ]; then say W2 FAIL "${W2_FAIL#; }"; else say W2 PASS "isError false + text:${W2_OK}"; fi
fi

# ── W3: CLI door = MCP door, byte for byte ───────────────────
if [ "$UP" -eq 1 ]; then
  "${CLI[@]}" list >"$TMP/cli_names.txt" 2>"$TMP/cli_err.txt"
  W3_FAIL=""; W3_OK=""
  if ! diff <(sort "$TMP/mcp_names.txt") <(sort "$TMP/cli_names.txt") >/dev/null; then
    W3_FAIL="; CLI list names ($(tr '\n' ' ' <"$TMP/cli_names.txt")) != tools/list names ($(tr '\n' ' ' <"$TMP/mcp_names.txt"))"
  fi
  while IFS= read -r tool; do
    [ -f "$TMP/call_$tool.json" ] && [ -f "$TMP/args_$tool.json" ] || continue
    "${CLI[@]}" call "$tool" --args "$(cat "$TMP/args_$tool.json")" >"$TMP/cli_$tool.txt" 2>>"$TMP/cli_err.txt"
    # The MCP text block, written with no added newline, for a byte-for-byte cmp
    py_json "$TMP/call_$tool.json" 'sys.stdout.write(d["result"]["content"][0]["text"])' >"$TMP/mcp_$tool.txt" 2>/dev/null
    if cmp -s "$TMP/mcp_$tool.txt" "$TMP/cli_$tool.txt"; then
      W3_OK="$W3_OK $tool($(wc -c <"$TMP/cli_$tool.txt" | tr -d ' ') bytes)"
    else
      W3_FAIL="$W3_FAIL; call $tool differs from the MCP text block: $(diff "$TMP/mcp_$tool.txt" "$TMP/cli_$tool.txt" | head -3 | tr '\n' ' ')"
    fi
  done <"$TMP/mcp_names.txt"
  if [ -n "$W3_FAIL" ]; then say W3 FAIL "${W3_FAIL#; }"; else say W3 PASS "list names match; call byte-identical:${W3_OK}"; fi
fi

# ── W4: one tool layer ───────────────────────────────────────
# (a) every tool in TOOLS is handled inside run_tool() in the server file;
# (b) the CLI file holds no data-analysis code (comments ignored): it only
#     calls run_tool(). If the server is down, tool names are read from the source.
if [ ! -s "$TMP/mcp_names.txt" ]; then
  python3 - "$DIR/$SERVER" >"$TMP/mcp_names.txt" <<'PY'
import re, sys
src = open(sys.argv[1], encoding="utf-8").read()
# only the TOOLS block: from the TOOLS assignment to run_tool()
m = re.search(r"^TOOLS\s*(?:<-|=)(.*?)^(?:run_tool|def run_tool|_DATASET_URLS|# ── Tool logic)", src, re.S | re.M)
src = m.group(1) if m else ""
for n in re.findall(r'(?:^|[\s,{(])"?name"?\s*[:=]\s*"([^"]+)"', src): print(n)
PY
fi
W4="$(python3 - "$DIR/$SERVER" "$LANG_TRACK" "$TMP/mcp_names.txt" <<'PY'
import re, sys
lines = open(sys.argv[1], encoding="utf-8").read().splitlines()
lang = sys.argv[2]
start = next((i for i, l in enumerate(lines) if re.match(r"^run_tool\s*<-\s*function|^def run_tool\b", l)), None)
if start is None: print("FAIL no run_tool() found in " + sys.argv[1]); sys.exit()
body = []
for l in lines[start + 1:]:
    if lang == "r" and l.startswith("}"): break
    if lang == "python" and l and not l[0].isspace() and not l.startswith("#"): break
    body.append(l)
body = "\n".join(body)
names = [n for n in open(sys.argv[3]).read().split() if n]
missing = [n for n in names if f'"{n}"' not in body and f"'{n}'" not in body]
print(("FAIL run_tool() does not handle: " + ", ".join(missing)) if missing else "PASS " + ", ".join(names))
PY
)"
HITS="$(grep -nvE '^[[:space:]]*#' "$DIR/$CLI_FILE" | grep -E 'summarise\(|mean\(|sd\(|across\(|pivot_|pandas|\.agg\(|read_csv|select_dtypes' )"
if [ "${W4%% *}" != "PASS" ]; then
  say W4 FAIL "${W4#* }"
elif [ -n "$HITS" ]; then
  say W4 FAIL "analysis code in $DIR/$CLI_FILE (belongs in run_tool()): $(echo "$HITS" | head -3 | tr '\n' ' ')"
else
  say W4 PASS "run_tool() in $DIR/$SERVER handles ${W4#PASS }; no analysis code in $DIR/$CLI_FILE"
fi

# ── W5: the deployed beacon answers ping with {} ─────────────
env_get() {  # read KEY from .env without eval and without printing it
  [ -f .env ] || return 0
  grep -E "^[[:space:]]*$1[[:space:]]*=" .env | tail -1 | sed -E "s/^[^=]*=[[:space:]]*//; s/^[\"']//; s/[\"'][[:space:]]*\$//"
}
if [ "$REMOTE" -ne 1 ]; then
  say W5 SKIP "pass --remote to ping your deployed MCP_URL"
else
  R_URL="${MCP_URL:-$(env_get MCP_URL)}"
  R_KEY="${CONNECT_API_KEY:-$(env_get CONNECT_API_KEY)}"
  if [ -z "$R_URL" ] || [ -z "$R_KEY" ]; then
    say W5 SKIP "MCP_URL and CONNECT_API_KEY must be set in .env"
  else
    rpc "$R_URL" '{"jsonrpc":"2.0","id":5,"method":"ping"}' -H "Authorization: Key ${R_KEY}" >"$TMP/ping.json" 2>/dev/null
    if py_json "$TMP/ping.json" 'sys.exit(0 if d.get("result") == {} else 1)' 2>/dev/null; then
      say W5 PASS "ping at MCP_URL returned {}"
    else
      say W5 FAIL "ping at MCP_URL did not return {} (check the URL ends in /mcp and the key is a viewer key)"
    fi
  fi
fi

# ── W6: SKILL.md frontmatter + names both tools ──────────────
if [ ! -f SKILL.md ]; then
  say W6 SKIP "no SKILL.md yet: cp SKILL.template.md SKILL.md and fill it in (CONTRACT.yaml T4)"
else
  W6="$(python3 - SKILL.md "$TMP/mcp_names.txt" <<'PY'
import sys, re
text = open(sys.argv[1], encoding="utf-8").read()
m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
if not m: print("FAIL SKILL.md has no --- frontmatter --- block"); sys.exit()
fm = {}
for line in m.group(1).splitlines():
    if ":" in line and not line.startswith(" "):
        k, v = line.split(":", 1); fm[k.strip()] = v.strip().strip('"').strip("'")
probs = []
if not fm.get("name"): probs.append("frontmatter needs name")
d = fm.get("description", "")
if not d: probs.append("frontmatter needs description")
elif len(d) > 1024: probs.append(f"description is {len(d)} chars (max 1024)")
try: names = [n for n in open(sys.argv[2]).read().split() if n]
except Exception: names = []
for n in names:
    if n not in text: probs.append(f"does not name tool {n}")
if "TODO" in text: probs.append("still has TODO lines")
print("FAIL " + "; ".join(probs) if probs else "PASS frontmatter ok; names " + ", ".join(names))
PY
)"
  say W6 "${W6%% *}" "${W6#* }"
fi

# ── W7: the log entry ────────────────────────────────────────
if [ ! -f docs/log-entry.md ]; then
  say W7 FAIL "docs/log-entry.md is missing"
else
  W7="$(python3 - docs/log-entry.md <<'PY'
import sys, re
text = open(sys.argv[1], encoding="utf-8").read()
parts = re.split(r"^## .*$", text, flags=re.M)[1:]
answers = [re.sub(r"<!--.*?-->", "", p, flags=re.S).strip() for p in parts[:3]]
probs = []
if len(answers) < 3: probs.append(f"expected three ## questions, found {len(answers)}")
unfilled = sum(1 for a in answers if not a or "FILL-IN" in a)
if unfilled: probs.append(f"{unfilled} of 3 answers still template (FILL-IN)")
if not re.search(r"^Recording:\s*https?://\S+", text, re.M): probs.append("no 'Recording: https://...' line")
print("FAIL template-unfilled: " + "; ".join(probs) if probs else "PASS three answers + recording link")
PY
)"
  # Selftest only: the shipped template is unfilled by design, so that is expected.
  if [ "$SELFTEST" -eq 1 ] && [ "${W7#FAIL template-unfilled}" != "$W7" ]; then
    W7="PASS template-unfilled (selftest)"
  fi
  say W7 "${W7%% *}" "${W7#* }"
fi

# ── W8: no key in git ────────────────────────────────────────
if [ ! -f .env.example ]; then
  say W8 FAIL ".env.example is missing"
elif ! grep -qxE '\.env' .gitignore 2>/dev/null; then
  say W8 FAIL ".env is not a line in .gitignore"
elif ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  say W8 SKIP ".env ignored; not a git repo, so git grep was not run"
else
  LEAK="$(git grep -nE "Key [A-Za-z0-9]{20,}" -- . 2>/dev/null | cut -d: -f1-2)"
  if [ -n "$LEAK" ]; then
    say W8 FAIL "something that looks like a Connect key is tracked in git at: $(echo "$LEAK" | tr '\n' ' ')"
  else
    say W8 PASS ".env ignored; git grep finds no Connect key"
  fi
fi

[ "$FAILS" -eq 0 ]
