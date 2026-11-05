# Decision: the confidence cut-off

## Cut-off
2

## Alternatives
- Cut-off 1: accept every reading that has a street. It sends fewer rows to a person, but it lets the model's guesses, such as a state it assumed, reach the map unchecked.
- Cut-off 3: accept only readings the model is sure of. It sends row 4 to a person as well, which costs review hours and catches the one assumed state.

## Reason
The audit log output/changes.jsonl holds 37 logged changes, 2 of them guard drops where the model offered a coordinate it may not give. Only 2 rows end unresolved, and 6 rows resolve. Row 4 has confidence 2 and its reason says the state was assumed, so a wrong guess there would put a point in the wrong town. A wrong place here costs one mailing, not a dispatch, so I accept the risk at 2 and spend review time on the 2 unresolved rows. If these addresses fed an ambulance dispatcher I would move to 3.

## Routed to the model
- house_number
- street
- unit
- city
- state

## Measured by code
- lat
- lon

## Model or geocoder
For standardising text the model is cheap and its accuracy is good enough to check against a held-out file. For coordinates a real geocoder costs a little per lookup, but its accuracy is measured and it can be held to a quality score; a model's coordinate can be held to nothing. So the model reads, the gazetteer (a real geocoder in production) measures.
