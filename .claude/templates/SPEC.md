# SPEC: <tool name>

What this tool IS. Where the code and this file disagree, the code is the bug: change this file first,
then the code. Keep it to one page. Replace every `<...>`.

## 1. User
<One named kind of person, e.g. "a classmate who wants to try the API without writing a request". Not "everyone".>

## 2. Use case
<The one thing this tool helps them do, and when they do it. One or two sentences.>
Problem or brief this answers: <one line, or a link>

## 3. Inputs (keep these few)
Only things this user can actually measure or already knows.

| Input | Type / units | Where the user gets it |
|---|---|---|
| <e.g. a list of numbers> | <numeric> | <typed into the page> |

## 4. The logic, and why
Say the rule in words before any code exists.
- **Rule:** <e.g. the API returns the count, mean, min and max of the list>
- **Why this rule fits the use case:** <one sentence>
- **Assumptions and how we check them:** <e.g. the list is non-empty and every item is a number; the API rejects anything else>
- **Known-answer check:** <a recorded API response, a stub LLM reply, a known query result or a hand-worked example the function must reproduce>

## 5. Outputs
<What the user sees: a number, a table, a pass/fail, with units, and how to read it.>

## 6. Delivery
<a React page over an API (FastAPI or plumber)>, deployed to <where>.

## 7. Test datasets
<2-3 small CSVs and what each one demonstrates, e.g. typical / edge case / bad input.>

## 8. Out of scope
<What we will NOT build in this round, so nobody (human or agent) builds it by accident.>
