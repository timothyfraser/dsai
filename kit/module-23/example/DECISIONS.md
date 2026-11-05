# Decision log

An example decision log for the Finale lab's checks.

## D1: How often to pull the counter feed
Choice: every 15 minutes, on a schedule
Alternatives: a live stream; once an hour
Reason: the feed updates every 15 minutes, so faster costs more and slower loses data
Evidence: runs/check_output.txt
Replaces: none

## D2: Where the counts live
Choice: one SQLite file
Alternatives: hosted Postgres; CSV files
Reason: one writer and under a million rows; a hosted database adds a bill and a login for no gain
Evidence: SPEC.md
Replaces: none

## D3: How the API runs
Choice: scale to zero
Alternatives: an always-on server
Reason: a few requests a day; the cold start is a few seconds, which the planner accepted
Evidence: runs/cold_start.txt
Replaces: none

## D4: What the page shows when the model is unsure
Choice: a warning above the number when the saved error is over the limit
Alternatives: hide the number; show it with no warning
Reason: the planner said a number with a warning is still useful, a missing number is not
Evidence: SPEC.md
Replaces: none

## D5: What the model may not do
Choice: the model forecasts; it never edits or deletes a stored count
Alternatives: let it clean outliers in the Store
Reason: a forecast can be wrong and be replaced; a deleted count cannot be checked later
Evidence: runs/check_output.txt
Replaces: none
