# Decision: which fields a person confirms

Form: work order. Three notes recorded for this decision: clear, noisy, and one that leaves out the location.

## Field sorting

| field | bucket | cost of a wrong value | why |
|---|---|---|---|
| asset | person-confirms | high | A crew goes to the wrong pump. "Pump three" is heard as "pump tree" in the noisy note, and the record still looks normal. |
| location | person-confirms | high | The omitted-location note shows the model can leave this blank or guess it; a guess sends a crew to the wrong site. |
| problem | model-drafts | low | The technician's own words sit in the transcript column next to it, and the read-back says it aloud. |
| priority | person-confirms | medium | A wrong "low" delays a repair; the model has no basis to know how urgent this site is. |
| safety_hazard | model-drafts | high | A wrong "false" is the worst error on the form, and it is the one nobody questions. |
| confirmed_by | never-automated | high | The name of the person who signed is theirs to type; a model has no basis to know it. |

## Alternatives rejected

- Confirm every field. Rejected: too slow.

## Reason

We used base.en because it is the default and it felt accurate.

## Evidence

It worked.
