# Decision: Brussels traffic pipeline, how it runs unattended

## Schedule
Cron: 0 */6 * * *
Runner: GitHub Actions schedule, in the team repo
Freshness needed: 6 hours
The dashboard shows today's counts by hour of day; a reading older than six hours would show a morning that has already ended.

## Retrain trigger
Trigger: drift
Threshold: 14
The retrain runs when the nightly check finds test_rmse on the newest week above 14 vehicles per minute, and at most once a day. The ingest workflow starts it as an event; no clock fires it on its own.

## Alternatives
- Ingest every 15 minutes. Fresher, but four times the commits and runner minutes for a chart that reads by the hour, and four times the failed runs to notice.
- Retrain on a clock, once a week (0 7 * * 1). Simple and predictable, but it spends a run when nothing changed and waits up to a week when something did.
- An orchestrator such as Airflow or Dagster. It would show the chain as one graph with retries, but it is one more service to host and watch for a two-stage pipeline.

## Reason
Freshness: six hours matches the hourly chart. Cost: four runs a day stay well inside the free runner minutes. Failure: each run is red when the payload is empty, so a failure is noticed at the next email, not at the next lecture. Staleness of the model is handled by the drift trigger, so the model changes only when the numbers say it should.

## Evidence
Checks: 8 of 8
test_rmse: 10.22
The threshold of 14 sits about 40% above the 10.22 our run recorded, so a normal week does not retrain.

## Paged
Who: the team member on duty this week, named in the repo README
How: the GitHub Actions failure email, and a pause by commenting out the schedule block

## Finale
Finale evidence: data/validation.json
It is a recorded test error written by the retrain itself, so it is evidence that the model was measured, not a claim that it is good.
