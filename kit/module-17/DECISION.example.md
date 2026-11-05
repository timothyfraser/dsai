# Decision: coffee_shop_count, who reads the count

## The job
Draft one row per photo of the coffee shop, taken once an hour: the time, how many people, how long the line to order is, and how many seats are free. The owner reads the rows each evening to plan how many baristas to put on the counter the next day.

## The rule
Threshold: 80%
A field may be drafted by the model when a person agreed with it on at least 80% of at least 5 photos, and a wrong value would be caught at the evening read. A field a person must decide is one where agreement is lower, or where a wrong value would not be caught.
Draft: clock_time, n_people, n_in_queue, confidence, notes
Person decides: seats_free

## Alternatives
- A person counts and types every row. It never miscounts a half-hidden customer, but it costs a few minutes per photo, so it is kept only for the seats field.
- An object detector counts the people. It is fast and local, but it cannot tell who is in the line and who is waiting for a drink, or whether a chair with a coat on it is free, so it covers only the total.
- OCR reads the clock or the till screen. It reads printed digits well, but a clock with hands, or a blurred screen, comes back empty, which is why the time may be "unknown".

## The reason
Agreement: 4 of 5
In the agreement column, a person agreed with the model on 4 of the 5 rows. The one miss was a seat the model called free that had a bag on it. That is why the seats stay with a person and the counts are drafted. Five photos is a small sample, so the threshold is a starting point to be tested again on more photos.
Verdict: draft

## Local or cloud
Local. The photos show customers who did not agree to be sent to a provider, and the job has a day, not a minute, to finish, so a few minutes per photo costs nothing that matters.
