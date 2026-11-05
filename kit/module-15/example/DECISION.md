# DECISION

FIXTURE: hand-written to show a passing file. No model produced it, and the run record below is a stand-in for the one you paste from your own copy.

## Stakeholder
The duty officer at the county emergency operations centre, at 3 am. She reads the brief on a phone, has no time to open a second tab, and needs the first useful answer in about three minutes.

## Bounds
- Turns: 4
- Web searches: 2
- Skill reads: 4
- Seconds per model call: 40

## Unattended
- Alone: read the skill notes, run up to 2 web searches, and write a brief that is marked as a draft and sent only to the duty officer.
- Needs a person: sending the brief to anyone else, any claim with no cited source, and every paused_for_human reply. The stop switch (/hooks/control) is kept by the duty officer's supervisor.

## Alternatives
- Turns 10, searches 3, reads 8, 120 seconds (the instructor's defaults): worst case 1200 seconds, twenty minutes, far past what a 3 am reader will wait, and more search spend per run than a first draft needs.
- Turns 2, searches 0, reads 2, 20 seconds: worst case 40 seconds, but with no search the brief has no outside source and cannot cite anything, so every reply would need a person to rewrite it.

## Reason
Against the table: the duty officer's limit is time to answer, so the worst case is the product of turns and seconds, 4 x 40 = 160 seconds, inside three minutes. Completeness is lower than the defaults, and I accept that because a late brief is worth less to her than a short one, and a paused reply hands the rest to a person. Two searches keep the brief citable, which holds down the blast radius if the brief is wrong: less outside text comes in and less money is spent per run. Four reads are enough for the skill notes this brief uses.

## Evidence
Run record from my copy, sent with max_turns 4:
- status: ok
- turns_used: 3
- turn_cap: 4
- Fence held: yes. The cap in the reply is the 4 I chose, the run used fewer turns than the cap, and the 3 turns fit inside the 160 second worst case.
