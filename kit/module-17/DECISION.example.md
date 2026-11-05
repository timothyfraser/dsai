# Decision: room_check, who reads the count

## The job
Draft one row per photo of a room for a safety walk-through: how many people, whether an exit sign is visible, whether a walkway is blocked. A person reads the rows the next morning.

## The rule
Threshold: 80%
A field may be drafted by the model when a person agreed with it on at least 80% of at least 5 photos, and a wrong value would be caught at the next morning's read. A field a person must decide is one where agreement is lower, or where a wrong value would not be caught.
Draft: n_people, n_sitting, n_standing, exit_sign_visible, confidence, notes
Person decides: walkway_blocked

## Alternatives
- A person counts and types every row. It never miscounts a half-hidden person, but it costs a few minutes per photo, so it is kept only for the walkway field.
- An object detector counts the people. It is fast and local, but it cannot tell whether an exit sign is visible or a walkway is blocked, so it covers only the counts.
- OCR reads the exit sign. It reads printed text well, but a sign with no words on it, or a blurred one, comes back empty.

## The reason
Agreement: 4 of 5
In the agreement column, a person agreed with the model on 4 of the 5 rows. The one miss was a walkway the model called clear. That is why the walkway stays with a person and the counts are drafted. Five photos is a small sample, so the threshold is a starting point to be tested again on more photos.
Verdict: draft

## Local or cloud
Local. The photos show people who did not agree to be sent to a provider, and the job has a day, not a minute, to finish, so a few minutes per photo costs nothing that matters.
