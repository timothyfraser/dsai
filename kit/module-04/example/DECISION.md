# Deployment decision: team example

## Host

Posit Connect, the course server

## Alternatives

- DigitalOcean App Platform, the $5 plan
- One teammate's laptop, opened to the internet for demos

## Reason

The API holds our model key, so it must run where a viewer cannot read the code: all three options do that. Connect wins on cost (the course pays) and on who can reach it (classmates and our agent sign in with Viewer keys). DigitalOcean gives more control over the machine, which we do not need for one Python API, and it bills by the month while the app runs. The laptop breaks at 3 am whenever its lid closes. We accept that Connect is shared, so a wrong content address could overwrite another team's work: we confirm the GUID before each deploy.

## Evidence

- API: https://connect.example.edu/team-example-api/ answers /health with {"status": "ok"}
- Page: https://connect.example.edu/team-example-page/ loads and calls the API above
- check.sh, run against the live addresses:

```
PASS  C3 /health answers 200  (got 200)
PASS  C8 the page names its API  (found the API address)
7 passed, 0 failed, 0 skipped
```

## Credentials

- Publisher key: Priya, as a GitHub repository secret named CONNECT_API_KEY; nobody else holds one
- Viewer key: in each teammate's own .env file, for scripts and the agent that call the API
- Model key: a Connect Var on the API content; the page never sees it

## Rollback

Two routes, and we can take both. First, Priya reactivates the previous bundle on Connect, which is fast and needs no rebuild, but works only while that bundle is still in the content's list. Second, if it is gone or the manifest was the cause, we redeploy the last good commit through the workflow, which rebuilds and leaves a record in GitHub. Either way we run check.sh against the live address, and the rollback is done when /health answers ok. The page is rebuilt only after the API answers.

## CORS

The API allows exactly one origin, https://connect.example.edu, which is where the page is served. No wildcard.
