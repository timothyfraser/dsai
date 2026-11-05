# DECISION

FIXTURE: hand-written to show a passing file. No model produced it.

## Model chosen
Spec-driven development, with a closed loop under it: SPEC.md is the source of truth, and every round ends with `bash check.sh`.

## Models rejected
- Test-driven development: our tests would mostly check what the public API returns, which we do not control, so the tests would break for reasons that are not our bugs.
- Contract-driven work with a full ledger: three people and one afternoon do not need check-out and check-in; the Owners list in SPEC.md is enough to stop two people editing one file.

## Who does what
- Agent: writes api/app.py, the React page and the docs from SPEC.md, one contract line at a time.
- We check: each contract line by running it, the browser's network tab for the call to /rows, and that the built page holds no key.

## Evidence
- `bash check.sh` output from round 2, kept in the submission.
- A screenshot of the page with the API stopped, showing the message (contract line 3).
