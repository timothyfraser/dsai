#!/usr/bin/env bash
# check.sh
# Run the lab's six checks on a team folder and print one line for each.
# Course kit, module 22
#
# Usage:
#   bash check.sh                 # stub mode on this folder's worked example (no database, no server)
#   bash check.sh path/to/team    # stub mode on your team folder
#   LIVE=1 bash check.sh path/to/team   # the lineage check reads your real store, API and page
#   BREAK=1 bash check.sh         # break a copy of the example on purpose, to watch every check fail

set -uo pipefail
KIT="$(cd "$(dirname "$0")" && pwd)"
TEAM="$(cd "${1:-$KIT}" && pwd)"

# 0. BREAK A COPY, IF ASKED ###################################

# A check you have never seen fail is a check you cannot trust. This breaks one thing per check.
if [ "${BREAK:-0}" = "1" ]; then
  COPY="$(mktemp -d)"
  cp -R "$TEAM"/. "$COPY"
  TEAM="$COPY"
  sed -i 's/`python3 build_cache.py --all`/rebuild by hand/' "$TEAM/ARCHITECTURE.md"   # C1
  sed -i '/^speed_mean_kmh,/d' "$TEAM/data_dictionary.csv"                             # C2
  sed -i '/"built_at_utc"/d; s/"n_minutes": 4,/"n_minutes": 4/' "$TEAM/saved/api_response.json"  # C3
  sed -i 's/id="vehicles-total">412/id="vehicles-total">421/' "$TEAM/saved/page.html"  # C4
  printf 'const KEY = "sb_%s_%s";\n' secret abcdefghijklmnop >> "$TEAM/saved/page.html" # C5
  sed -i 's/"run_records", "rowsecurity": true/"run_records", "rowsecurity": false/' "$TEAM/saved/rls.json"  # C6
  echo "BREAK=1: checking a broken copy in $TEAM"
fi

# 1. RUN THE CHECKS ###################################

if [ "${LIVE:-0}" = "1" ]; then STUB=0; else STUB=1; fi
cd "$TEAM"
OUT="$( {
  python3 "$KIT/check_architecture.py" .
  python3 "$KIT/check_dictionary.py" .
  python3 "$KIT/check_contract.py" .
  LINEAGE_STUB=$STUB python3 "$KIT/check_lineage.py" .
  python3 "$KIT/check_no_keys.py" .
} 2>&1 )"
echo "$OUT"

# 2. COUNT ###################################

PASSED=$(echo "$OUT" | grep -c '^PASS  C')
echo "CHECKS $PASSED of 6 passed"
[ "$PASSED" -eq 6 ]
