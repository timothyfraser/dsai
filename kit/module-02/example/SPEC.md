# SPEC

## Goal
A React page over a small API that looks up a character in a public API and shows the rows in a table.

## Who it is for
A classmate who wants to try the API without writing a request.

## Contract
1. The API starts with one command and /health answers 200 with JSON: yes
2. GET /rows returns at least one real row, and the page shows it: yes
3. With the API stopped, the page shows a message and does not go blank: yes
4. No key-shaped string is in the built page: yes
5. The README says how to install, run, and which key is needed: yes

## Owners
- api/app.py: Ana
- web/src/: Ben
- docs/: Chi
- README.md, SPEC.md and DECISION.md: Chi
