# ARCHITECTURE.md (template)

Copy this file to the top of your team repo as `ARCHITECTURE.md` and fill in every cell.
`check_architecture.py` reads the two tables and the decision section, so keep the headings
and the column names exactly as they are.

## Drawing

Draw the boxes and arrows here (Mermaid, or a photo of a paper drawing). Truth flows one way:
sources, then the store, then the API, then the cache, then the page. Put a star on the one box
where each number is defined. If an arrow points back up, explain it below or remove it.

```
sources ──▶ [store ★] ──▶ API ──▶ cache ──▶ page
```

## Stores

One row per place your system keeps data between runs: tables, files, buckets, caches, logs,
run records. Role is exactly `source of truth` or `derived`. A derived store needs the command
that rebuilds it from its source; a source of truth needs a backup line instead.

| Store | Holds | Role | Rebuild or backup | Writers | Readers |
|---|---|---|---|---|---|
| (name and rung, e.g. "Supabase Postgres table `readings`") | (what facts) | source of truth | (how it is backed up) | (who or what writes) | (who or what reads) |
| (e.g. "nightly JSON cache in object storage") | (what answers) | derived | (the exact rebuild command) | (the job that writes it) | (who reads it, and through what) |

## Decision

One decision, the one your system depends on most: where the source of truth lives.

**Chosen:** (the store and its rung on the ladder)

**Alternative 1:** (a rung you did not choose, and when it would win)

**Alternative 2:** (another rung you did not choose, and when it would win)

**Reason:** (why the chosen one fits your writers, size, cost and readers)

**Evidence:** (a number or a file: rows per day, file size, writers per hour, a check output)
