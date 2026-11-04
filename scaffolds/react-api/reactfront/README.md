# React page starter

A one-screen React page that talks to an API. It pings `GET /health`, then sends
a list of numbers to `POST /summary` and shows the count, mean, min and max the
API sends back. Plain Vite and React, no UI kit.

The page does no real work. The work is in the API's `logic.py` (FastAPI) or
`R/logic.R` (plumber). The API address lives in `src/api.js` and nowhere else.

## Run it

You need Node.js 20 or newer, and the API running (`../fastapi/testme.sh` or
`../plumber/testme.R`).

```bash
npm install
npm run dev        # open the http://localhost:5173 link it prints
```

With no setup, the page calls `/api/...` and the Vite dev proxy in
`vite.config.js` forwards it to the API on your machine. The browser sees one
address, so you need no CORS yet. The proxy points at port 8000 (FastAPI); for
plumber change the target to port 5762.

## Point it at a deployed API

Create a file named `.env.local` in this folder:

```
VITE_API_URL=https://the-address-of-your-deployed-api
```

then restart `npm run dev` (or rebuild). Now the browser does see a second
address, so the API needs CORS. Both starter APIs read the `CORS_ORIGIN`
environment variable: set it to the address of your deployed page.

**Anything named `VITE_` is printed into the public JavaScript.** Every visitor
can read it. The API address is fine there. A key, a token or a password is
never fine there. The API holds the key; the page never does.

## Build and test

```bash
npm run build      # writes dist/, a static site that works under any URL path
npm test           # runs the page's small tests
```

## Deploy to Posit Connect

Deploy the API first and get its address. Then set `VITE_API_URL` to it and
rebuild: Vite bakes the value into `dist/` at build time, so a new address needs
a new build.

Easiest: copy
[`.claude/skills/connect-publish/workflows/deploy-react-static.yml`](../../../.claude/skills/connect-publish/workflows/deploy-react-static.yml)
into your repo's `.github/workflows/` and both scripts in
[`.claude/skills/connect-publish/scripts/`](../../../.claude/skills/connect-publish/scripts/)
into `.github/scripts/`, add the two repository secrets it names, and push. It
runs `npm ci && npm run build` and publishes `dist/` as static content.

Manual: run `npm run build`, then publish the `dist/` folder as static content
(see the [`connect-publish`](../../../.claude/skills/connect-publish/SKILL.md) skill).

Never commit `node_modules/` or `dist/` (both are in `.gitignore`). Do commit
`package-lock.json`, so `npm ci` installs the same versions everywhere.
