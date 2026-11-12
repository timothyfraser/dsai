# Decision: flood plan retrieval, broken on purpose

## Store
Store: a vector thing
Broken on purpose: this is not one of the four stores the lab names.

## Alternatives
- Keyword search.
Broken on purpose: one bullet, and it says nothing about why it lost.

## Settings
k: a few
Broken on purpose: k is not a whole number, and chunk is missing.

## Evidence
Hit rate: 0.95
At k: 5
Broken on purpose: the answers log gives 0.30, and k does not match Settings.

## Grounding
- How many pumps are at Pier 4? | supported: yes | read by: the model
- At what river level do the gates close? | supported: yes | read by: AI
Broken on purpose: two rows, read by the model.
