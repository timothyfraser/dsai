# Design: pump station rebuild order, how far the tool goes

## Rung
Rung: recommend
The tool lists three options with reasons and sources, ranks them, and says which it would pick. The operations manager reads the sources and decides.

## Rejected
- Inform only: it would list the options and stop. Rejected because the manager asked which to rebuild first, and a list with no ranking leaves the hard part to a tired reader.
- Rule-based code: rank by trip count alone. Rejected because it would put River first or ignore the hospital feeder, and the reasons for each option are not in one column.
- A solver: pick the best rebuild order under a budget. Rejected because we have no costs for the first two options, so it would invent numbers.

## Reason
The decision is small, the sources are in files, and a wrong rank is cheap to catch because the manager opens each source. A recommendation saves reading time. The tool never decides: a named person does, and the audit log shows the order.

## Evidence
Audit log: audit_log.jsonl, 5 lines
It shows a person asked, the model ranked, a person reviewed both sources, and then a person decided.
