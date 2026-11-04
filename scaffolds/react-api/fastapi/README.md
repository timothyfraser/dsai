# FastAPI starter

A minimal Python API for a React page. Copy this folder into your own repo;
do not edit it in place.

## Routes

- `GET /health` returns `{"status": "ok", "version": "..."}`. Check this first.
- `POST /summary` takes `{"values": [1, 2, 3]}` and returns the count, mean,
  min and max.
- `GET /docs` is the interactive page FastAPI writes for you.

## Files

- `logic.py` is the real work. It does not import FastAPI.
- `test_logic.py` has a known-answer test and a degenerate test. Run `python -m pytest -q`.
- `app.py` is routes only. CORS reads the `CORS_ORIGIN` environment variable.

## The four-script contract

| File | Job |
|---|---|
| `testme.sh` | run it locally on port 8000 |
| `manifestme.sh` | write `manifest.json` for Posit Connect |
| `deployme.sh` | push it to Posit Connect from your machine |
| `README.md` | this file |

```bash
./testme.sh        # then visit http://localhost:8000/docs
./manifestme.sh
./deployme.sh
```

## Notes

- Pin every dependency in `requirements.txt` with `==`, and regenerate the
  manifest after any change.
- The Connect mode for this app is `fastapi`, not `api`.
- Keys go in Connect's environment settings (Vars), never in the repo and never
  in the React page.
- How to get a publisher key: see `.claude/skills/connect-publish/SKILL.md`.
