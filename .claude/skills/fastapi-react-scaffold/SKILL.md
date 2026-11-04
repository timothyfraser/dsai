---
name: fastapi-react-scaffold
description: Scaffold a Python FastAPI backend with a React front end for a DSAI module project - project shape, the four-script contract, CORS from an environment variable, the Vite dev proxy, the one API address in src/api.js, and why VITE_ values are public. Use when a student picks Python for the API behind a React page.
---

# FastAPI + React scaffold

Start from [`scaffolds/react-api/fastapi/`](../../../scaffolds/react-api/fastapi/) and
[`scaffolds/react-api/reactfront/`](../../../scaffolds/react-api/reactfront/). Copy them into
your own repo (the API into `api/`, the page into `web/`) rather than editing them in place.

## Shape

```
yourproject/
  api/
    logic.py           <- the real work. plain functions. no framework.
    test_logic.py      <- known-answer and degenerate tests. write this early.
    app.py             <- FastAPI routes. thin. calls logic.py.
    requirements.txt   <- pinned versions
    testme.sh manifestme.sh deployme.sh README.md
  web/
    src/api.js         <- the ONLY place the API address lives
    src/App.jsx ...
    package.json package-lock.json vite.config.js README.md
```

**`logic.py` must not import FastAPI.** That separation is what lets you test the logic
without running a server. See the `logic-first-steering` skill.

## Backend

`app.py` stays thin: parse input, call a function from `logic.py`, return JSON. Two routes
are enough to start: `/health` and one data route.

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from logic import summarize

app = FastAPI(title="...", version="1.0.0")

class Values(BaseModel):
    values: list[float]

@app.get("/health")
async def health():
    return {"status": "ok", "version": app.version}

@app.post("/summary")
async def summary(body: Values):
    try:
        return summarize(body.values)
    except ValueError as err:
        raise HTTPException(status_code=422, detail=str(err))
```

FastAPI gives you interactive docs at `/docs` for free. Check `/health` first, from the
outside, before you wire the page to anything.

## CORS

A page on one address (the browser calls it an origin) cannot read answers from an API on
another address unless the API says yes. Wide open, for your own machine:

```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware, allow_origins=["*"],
    allow_methods=["*"], allow_headers=["*"],
)
```

Wide-open CORS is fine while you work on your own machine. Do not carry it into anything real.
Read the allowed origin from an environment variable instead, so one setting on Connect narrows it
to your deployed page's address:

```python
import os
app.add_middleware(
    CORSMiddleware, allow_origins=[os.environ.get("CORS_ORIGIN", "*")],
    allow_methods=["*"], allow_headers=["*"],
)
```

Set `CORS_ORIGIN` in the Connect content's Vars panel, never in code.

**The local option with no CORS at all:** the Vite dev proxy. `web/vite.config.js` forwards
`/api/...` to `http://127.0.0.1:8000`, so the browser only ever sees the page's own address.
Use `127.0.0.1`, not `localhost`: on Windows `localhost` can resolve to IPv6 and miss an API
listening on IPv4.

## Front end

Vite + React, kept deliberately small:

```bash
npm create vite@latest web -- --template react
cd web && npm install && npm run dev
```

Put the API address in one place, `src/api.js`, read from `VITE_API_URL`:

```js
export const API_URL = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '')
```

Every call in the page goes through that file, so the switch from the local proxy to your
Connect address is one environment variable, not a grep across the codebase.

**WARNING: anything named `VITE_` is printed into the public JavaScript.** Every visitor to
your page can read it in their browser. The API address is fine there. A key, a token or a
password is never fine there. The API holds the key (in its own environment); the page never does.

Build with `npm run build -- --base=./`; deploy the `dist/` folder as static content. Do not
commit `node_modules/` or `dist/`; both are gitignored. Do commit `package-lock.json`.

## Deploy

The API and the page deploy as two separate pieces of content on Posit Connect, and the
FastAPI Connect mode is `fastapi`, not `api`. Deploy the API first, get its address, set
`VITE_API_URL` to it, rebuild (Vite bakes the value in at build time), then deploy the page.
Set `CORS_ORIGIN` on the API to the page's address. See the `connect-publish` skill.
