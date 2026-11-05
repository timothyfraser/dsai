#!/usr/bin/env bash
# deploy_page.sh
# Build a React page against the live API, then publish the built files to Posit Connect.
# Course kit, module 4
#
# Topic: The page is files, the API is a process
#
# A React page is built once into plain files (HTML, JavaScript, CSS) in dist/.
# The API address is baked into that JavaScript at build time, so the order
# matters: deploy the API first, learn its live address, then build the page
# with that address, then publish dist/ as static content. Change the API
# address later and you must rebuild and republish the page.
#
# If you haven't already: install Node.js, and `pip install rsconnect-python`.
#
# Run it from your web/ folder, after the API is live:
#   API_URL=https://your-server/your-api PAGE_GUID=... bash deploy_page.sh
# Reads CONNECT_SERVER and CONNECT_API_KEY from .env, never from this file.

set -euo pipefail

# 0. SETUP ###################################

# Load the server address and the Publisher key from .env, which git ignores.
# Read, not exported: rsconnect fails when CONNECT_API_KEY is in the environment
# and is also passed as a flag, so we pass flags only.
source .env
export -n CONNECT_API_KEY CONNECT_SERVER 2>/dev/null || true
: "${API_URL:?Set API_URL to the live API address first: the API deploys before the page}"
: "${PAGE_GUID:?Set PAGE_GUID to the page content GUID, read from Connect, never guessed}"

# 1. CONFIRM THE TARGET (GATE 2) ###################################

# A wrong GUID overwrites whatever content it points at, with no undo.
# Read the title that lives there and stop unless a person says yes.
rsconnect content describe --server "$CONNECT_SERVER" --api-key "$CONNECT_API_KEY" --guid "$PAGE_GUID" | grep -i '"title"'
read -r -p "Is that the page you mean to replace? Type yes: " answer
[ "$answer" = "yes" ] || { echo "Stopped: target not confirmed."; exit 1; }

# 2. BUILD THE PAGE AGAINST THE LIVE API ###################################

# Anything named VITE_ ends up inside the public JavaScript. An address is fine
# there. A key never is: the page calls the API, and the API holds the key.
npm ci
VITE_API_URL="$API_URL" npm run build -- --base=./

# 3. PUBLISH THE FILES, THEN VERIFY ###################################

rsconnect deploy html --server "$CONNECT_SERVER" --api-key "$CONNECT_API_KEY" --app-id "$PAGE_GUID" dist/

# Green is not live: a page counts as deployed when check.sh says it loads
# and names its API, not when the command above finishes.
echo "Now run: PAGE_URL=<the page address> API_URL=$API_URL bash check.sh"
