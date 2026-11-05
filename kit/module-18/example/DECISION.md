# Decision: which fields a person confirms

Form: work order. Three notes recorded for this decision: clear, noisy, and one that leaves out the location.

## Field sorting

| field | bucket | cost of a wrong value | why |
|---|---|---|---|
| asset | person-confirms | high | A crew goes to the wrong pump. "Pump three" is heard as "pump tree" in the noisy note, and the record still looks normal. |
| location | person-confirms | high | The omitted-location note shows the model can leave this blank or guess it; a guess sends a crew to the wrong site. |
| problem | model-drafts | low | The technician's own words sit in the transcript column next to it, and the read-back says it aloud. |
| priority | person-confirms | medium | A wrong "low" delays a repair; the model has no basis to know how urgent this site is. |
| safety_hazard | person-confirms | high | A wrong "false" is the worst error on the form, and it is the one nobody questions. |
| action_requested | model-drafts | low | A reader sees it in the read-back, and a wrong request is caught when the crew calls. |
| confirmed_by | never-automated | high | The name of the person who signed is theirs to type; a model has no basis to know it. |

## Alternatives rejected

- Confirm every field of every note. Rejected: three of seven fields are cheap and visible, and a person asked to confirm everything stops reading.
- Confirm only the fields where the model seemed unsure. Rejected: the model is as confident on a wrong asset as on a right one, so its confidence cannot choose the fields.

## Reason

Transcriber chosen: base.en, run locally. The word error rate on our own notes was 4 percent for the clear note, 21 percent for the noisy note and 6 percent for the omitted-fact note. The errors in the noisy note fell on numbers and codes ("three" heard as "tree"), which is where a wrong value costs most, so asset and location go to a person. small.en cut the noisy note to 9 percent for about three times the run time, which we accept only for noisy sites. The cloud model was not used because the recordings include other people's voices and nobody agreed to a copy leaving the computer.

## Evidence

- wer_by_note.csv: the three word error rates above, one row per note, counted against our own listening transcripts.
- work_orders.csv: the omitted-location note came back as "not stated", not a guessed place; 05_check_refusal.py passes on it.
- 04_check.sh output with the stubs off.
