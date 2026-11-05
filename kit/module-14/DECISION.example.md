# Decision: congestion tracker, practice run

The three prompts below are made up for practice; the real ones are shown at the kickoff.

## The prompt
Chosen: a city congestion tracker that summarises one day of road speeds for a traffic planner
Rejected:
- A chatbot for bus timetables: the team has no way to check its answers against a known timetable in a day.
- A parking photo counter: it needs a vision model the team has not used, and a camera feed it does not have.

## The cut
User: a traffic planner who reads one summary each morning
Dropped first: the live map, because the planner reads a summary and a table, and the map cost the most hours for the least use.
Also dropped: real road feeds, because synthetic data with known answers is what lets a check pass on stage.

## The evidence
Check: checks/check_summary.py
Data: data/test_speeds_known.csv
Cases: 3 of 3
Result: PASS on the deployed system, on three test datasets, with the empty-input case refused politely.
One run is not enough: the check runs on three datasets whose answers we wrote down first, so a pass means the numbers are right, not only that the system answered once.
