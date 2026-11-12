# example_bad/

FIXTURE: the same store and questions with an answers log broken on purpose (low hit rate, an answer with no citation, a citation to an item not in the store, an unanswerable question answered). Used by `LLM_STUB=bad bash check.sh`.

Its `DECISION.md` is broken on purpose too: a store the lab does not name, one thin alternative, settings that are not numbers, a hit rate that does not match the log, and grounding rows read by "the model".
