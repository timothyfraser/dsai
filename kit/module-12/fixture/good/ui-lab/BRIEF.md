# Design brief: Pump history

## Who

The maintenance lead on shift, standing at the pump bay with a phone.

## Task

Ask when a pump was last serviced and what was done.

## Decision supported

Whether to take the pump out of service today. The date of the last service decides it.

## Device first

Phone first: the lead is at the bay, not at a desk.

## Accessibility bar

WCAG 2.2 AA: 4.5 to 1 contrast, every control reachable by keyboard, labelled input, 44 px targets.

## Latency budget

Say "Looking it up" at once; give up after 8 seconds with a sentence and a retry button.

## States

Empty: one example question to tap. Loading: "Looking it up". Success: the date first, then the
work, then the source row. Error: one sentence and a retry. Stale: an answer with no source says so
in the danger colour.

## Scale rung

Team: about twenty staff behind the Connect login.

## Contract

POST /ask with {"question"}; reply {"answer", "source"}; 8 second timeout; every failure becomes
one plain sentence.
