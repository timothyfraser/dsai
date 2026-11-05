# ARCHITECTURE.md (worked example: the traffic counts system)

A worked example for the course's traffic counts job, as a team might redesign it once a
deployed app must show new rows without a redeploy. It is an example to read and to run the
checks on, not the instructor's design.

## Drawing

```
Brussels traffic API ──▶ ingest job (every 15 min) ──▶ [Postgres table traffic ★]
                                                              │
                                                              ▼
                                                   API /traffic/hourly
                                                      │            │
                                    nightly cache job ▼            ▼ app asks the API
                                         JSON files in object storage ◀── API redirects here
                                                                   │
                                                                   ▼
                                                                  page
```

## Stores

| Store | Holds | Role | Rebuild or backup | Writers | Readers |
|---|---|---|---|---|---|
| Supabase Postgres table `traffic` | one row per monitor per minute: vehicles, speed, occupancy | source of truth | daily export to CSV in object storage, restore tested with `psql -f restore.sql` | the ingest job, with the secret key, on the server | the API, with the secret key, on the server |
| Supabase Postgres table `monitors` | monitor id, name, location | source of truth | seeded from `data/monitors.csv` in git by `python3 seed_monitors.py` | the team, by pull request to `data/monitors.csv` | the API; the browser, with the publishable key and a read-only RLS policy |
| JSON files `hourly/<monitor>.json` in object storage | the API's hourly answers, each with `built_at_utc` | derived | `python3 build_cache.py --all` | the nightly cache job | the page, only through the API's redirect |
| Postgres table `run_records` | one row per model call: prompt version, model, input id, output, time, cost | source of truth | included in the daily export | the API, on the server | the team, in the Supabase dashboard |

## Decision

**Chosen:** a hosted Postgres database (Supabase free plan) as the source of truth for `traffic`.

**Alternative 1:** SQLite committed to git, as the course job does; it wins for a class demo with one writer and no deployed reader.

**Alternative 2:** CSV files in git, one per day; they win when a person edits a small table by hand and wants a reviewable diff.

**Reason:** the job writes every 15 minutes and the deployed app must see new rows without a redeploy; a file in git cannot do that, and Postgres takes many writers and per-row access rules.

**Evidence:** the course's `traffic.db` held 59,420 rows in 8.1 MB after 1,187 scheduled runs, far under the free plan's 500 MB database limit, and the 1,187 scheduled commits are 1,187 copies of a binary file in git history.
