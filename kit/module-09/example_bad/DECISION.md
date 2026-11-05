# Decision: Brussels traffic pipeline, broken on purpose

## Schedule
Cron: 0 6 * * 1
Runner: GitHub Actions schedule
Freshness needed: 6 hours
Broken on purpose: a weekly cron line cannot meet a six-hour need.

## Retrain trigger
Trigger: drift
Threshold: 8
Broken on purpose: 8 is below the recorded test_rmse, so every run would retrain.

## Alternatives
- Retrain on a clock, once a week (0 7 * * 1).

## Reason
It seemed fine.

## Evidence
Checks: 8 of 8
test_rmse: 10.22

## Paged
Who: nobody
How: we look sometimes

## Finale
Finale evidence: the dashboard looks good
