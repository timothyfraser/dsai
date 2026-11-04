# Plumber starter

A minimal R API for a React page. Copy this folder into your own repo; do not
edit it in place.

## Routes

- `GET /health` returns `{"status": "ok", "version": "1.0.0"}`. Check this first.
- `POST /summary` takes `{"values": [1, 2, 3]}` and returns the count, mean,
  min and max.
- `/__docs__/` is the interactive page plumber writes for you.

## Files

- `R/logic.R` is the real work. It does not load plumber.
- `tests/test_logic.R` has a known-answer test and a degenerate test. Run
  `Rscript tests/test_logic.R`.
- `plumber.R` is routes only. The CORS filter reads the `CORS_ORIGIN`
  environment variable.

## The four-script contract

| File | Job |
|---|---|
| `testme.R` | run it locally on port 5762 |
| `manifestme.R` | write `manifest.json` for Posit Connect |
| `deployme.R` | push it to Posit Connect from your machine |
| `README.md` | this file |

```r
source("testme.R")
source("manifestme.R")
source("deployme.R")
```

## Notes

- `rsconnect::writeManifest()` finds packages by scanning for `library()`
  calls. Load packages the normal way or they are missed and the deploy fails.
- There is no `manifest.json` here on purpose: generate one with `manifestme.R`
  on your machine, then commit it. `deployme.R` refuses to run without one.
- Keys go in Connect's environment settings (Vars), never in the repo and never
  in the React page.
- How to get a publisher key: see `.claude/skills/connect-publish/SKILL.md`.
