# Decision: keep warm, scale to zero, or something else (an example, on the pretend host)

This example reads the kit's example files, measured on stub_host.py. Your team writes its own from its own numbers.

Latency requirement: a first request after a quiet spell may take up to 1 second, because the users are a class that opens the app once a day.

## Host

Host: Connect
Cold start: Connect 401.9 ms, Fly.io 1180 ms
Why: both meet the 1 second requirement, but Connect has no per-team bill and no card on file, while the Fly.io container starts slower and is billed by the second while it runs. The Fly.io figure is a pretend number typed into `fly_cold_median_ms`.

## 100 requests a day

Choice: scale to zero
Why: almost every request is cold at this rate, but `cold_median_ms` is under the 1 second requirement, and keeping one process warm would hold memory all month for a few minutes of use.
Evidence: `cold_fraction`, `cold_median_ms`, `memory_gb_hours_month`

## 10,000 requests a day

Choice: scale to zero
Why: about half the requests are still cold, the host bill stays inside the free tier, and the wait is inside the requirement.
Evidence: `cold_fraction`, `host_cost`, `warm_p95_ms`

## 100,000 requests a day

Choice: keep warm
Why: at this rate the process almost never sleeps, so keeping one warm changes little either way and guarantees nobody waits; the model calls are the real bill.
Evidence: `cold_starts_month`, `model_calls_month`

## Alternatives considered

A fixed instance (the DigitalOcean plan) costs the same at every level and never sleeps. A cache in front of the slow route would cut the model calls, which no hosting choice does.
