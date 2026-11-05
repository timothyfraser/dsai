# Character lookup

FIXTURE: hand-written to show a passing folder. No model produced it.

A React page that looks up characters through a small FastAPI API and shows them in a table.
The page never calls the public API itself: it calls our API, and our API calls the public one.

## Install
`pip install fastapi uvicorn` in `api/`, then `npm ci` in `web/`.

## Run
1. The API: `uvicorn app:app --port 8000` from `api/`.
2. The page: `npm run dev` from `web/`, with `VITE_API_URL=http://127.0.0.1:8000` in `web/.env.local`.

## Key
The public API needs no key. If yours does, the API reads it from `.env` as `API_KEY`; the page never sees it, and `.env` is never committed.
