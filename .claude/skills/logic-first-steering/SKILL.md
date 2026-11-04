---
name: logic-first-steering
description: How to steer a coding agent so the logic of a React-page-over-an-API project stays correct and central, by verifying it against known cases (a recorded API response, a stub LLM reply, a known query result, an eval set) before any API route, page or styling work. Load at the start of any DSAI module project and before accepting agent-written logic code.
---

# Logic-first steering

**The logic is the graded core. The API and the page are the delivery vehicle.**

An agent will happily produce a beautiful page over a function that returns the wrong
answer. Nothing in the code will look broken. This skill exists to stop that.

## The order of work

1. **State the rule in words first**, before any code exists. "The API takes a list of numbers
   and returns the count, mean, min and max; an empty list is an error." If nobody on the team can
   write that sentence, no amount of code will fix it.
2. **Implement the logic alone**, as a plain function with plain inputs, in its own file
   (`logic.py` or `R/logic.R`). No web framework, no page, no styling.
3. **Verify it against a known case** (see below) before anything else happens.
4. **Only then** wrap it in an API route.
5. **Only then** call the route from the page.
6. **Style last.** Always last.

Teams that style first lose the time they needed for step 3.

## Verify against a known case: non-negotiable

Before you accept any agent-written logic, check it against something whose answer you
already know. Pick the one that fits what the function does:

- **A recorded API response.** Save one real answer from the API you call (a JSON file in
  `data/`), then assert that your parsing function turns it into the fields you expect. The test
  never touches the network.
- **A stub LLM reply.** If the function calls a model, run it in stub mode (`LLM_STUB=1`, a fixed
  reply in `data/`) and assert on what your code does with that reply: parse it, reject a
  malformed one, retry once. The test never spends tokens and gives the same answer every time.
- **A known query result.** For a database or file query, build a tiny table whose answer you
  can count by hand, and assert the query returns exactly that.
- **An eval set.** For model output you cannot predict exactly, write 10 or more questions with
  answers you wrote down first (`eval/questions.csv`), run the system, and report the share it
  got right. Write the target before you run it.
- **A hand-worked example.** For arithmetic, work one small case on paper and assert the function
  reproduces it.

Then add the other half:

- **A degenerate case.** Empty input, one item, a missing field, a wrong type, a 500 from the
  API you call. The function must raise a clear error or return a message saying what is
  wrong. If it returns a confident-looking answer here (0, an empty result passed off as a
  result), it is wrong.
- **A wrong-address case.** Point the code at an address that does not exist. It should fail
  with a readable message, not hang and not crash silently.

Write these as actual tests. Two or three assertions is enough and takes five minutes;
discovering a wrong rule after the page is built does not.

## Traps to name explicitly in your prompt

- **Logic in the page.** If the page computes a number the API also computes, they will drift.
  The API computes; the page displays.
- **Logic in the route.** A route that does the work cannot be tested without starting a server.
  The route parses input, calls the function, returns JSON.
- **A key in the page.** The page never holds a key; the API does. Anything named `VITE_` is
  printed into public JavaScript.
- **A test that accepts the wrong answer.** If the test was written after the code, by the same
  agent, from the code's own output, it proves nothing. Take the expected value from `SPEC.md` or
  a hand calculation.
- **Invented data.** Test data lives in `data/` with a codebook. Never present made-up numbers as real.

## Prompts that work

Weak: *"Build me an app that summarizes numbers."*

Strong: *"Write one Python function `summarize(values)` in `api/logic.py` returning the count, mean,
min and max of a list of numbers. It must not import FastAPI. Raise ValueError on an empty list or
a non-number. Then write three tests: a hand-worked case with this expected answer, an empty list,
and a list containing text."*

Then, separately: *"Now expose that function as `POST /summary` in `api/app.py`."* Then, separately:
*"Now call that route from the page, through `web/src/api.js`."*

Small, verifiable, one thing at a time. The agent is fast; your job is to keep it pointed at the
right thing.

## Before you demo

- Every number on screen traces to a function you can open.
- Someone on the team can answer "why is that the answer?" out loud.
- The tool behaves sensibly on your degenerate test, live, in front of the class.
