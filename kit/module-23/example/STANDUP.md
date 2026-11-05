# Stand-up: Street Count

## What it is
A city mobility planner types a street counter, a day and an hour, and gets the number of
vehicles to expect. When our model is unsure, the page says so before it shows the number.

## Why this architecture
Two boxes mattered. We store counts in one SQLite file instead of a hosted database, because
there is one writer and under a million rows. We run the API so it scales to zero instead of
always on, because the planner asks a few times a day.

## What it costs
Close to nothing a month at today's traffic, and about an hour a week of a person's time to read
the error number after the weekly retrain.

## Where it fails
A holiday week skews the weekly model. The planner would notice forecasts that are too high.
Our check reads the saved error after each retrain and turns on the warning when it is over the limit.
