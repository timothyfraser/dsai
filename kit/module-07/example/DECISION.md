# Decision: flood plan retrieval, how we store and find passages

## Store
Store: csv
One row per plan paragraph, with an id and the text, read straight into the search.

## Alternatives
- Embedding search over chunks. It finds paraphrases, but for forty short paragraphs it adds an index to build and watch, and our hit rate did not need it.
- A long-context prompt with the whole plan pasted in. It is simple, but it cites nothing we can check and cost grows with every question.
- Fine-tuning a model on the plan. It would bake in facts that go stale the next time the plan changes.

## Settings
k: 3
chunk: n/a

## Evidence
Hit rate: 0.80
At k: 3
We ran the ten held-out questions and counted how often the cited id was the expected one. Two misses, both on questions that paraphrase the plan.

## Grounding
- How many pumps are at Pier 4? | supported: yes | read by: Alex Rivera
- At what river level do the gates close? | supported: yes | read by: Alex Rivera
- Where do Water Street residents park cars? | supported: no | read by: Sam Okafor
