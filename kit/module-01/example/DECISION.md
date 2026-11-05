## Source
Open-Meteo forecast API (a sample choice for a stakeholder who needs hourly temperatures for one city).

## Alternatives
- A national weather service API: free, but it covers one country and its terms page limits commercial reuse.
- A paid weather vendor: reliable and documented, but the key costs money and the terms bar storing the data.

## Reason
Against the table: authentication is none for light use, so no key can leak; the rate limit is high enough for one request per hour; the data format is JSON with units named in the reply; the licence allows reuse with credit; reliability is a public status page; the data is updated hourly. The two alternatives lose on the licence and on cost for this stakeholder.

## Evidence
Request: GET https://api.open-meteo.com/v1/forecast?latitude=42.44&longitude=-76.50&hourly=temperature_2m
Reply: status 200, 168 rows under "hourly", units "°C" stated in the reply. Checked the terms page by hand.
