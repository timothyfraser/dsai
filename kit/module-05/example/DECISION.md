# Tool server decision: team example

## Behind

- summarize_dataset, because three of our agents and a classmate's agent all need it and none should hold our code
- fetch_permits, which reads our team's API; reuse across agents is the whole point

## Kept

- clean_headers: a function inside the agent script; only that script calls it, so a server would add a hop for no reuse
- /health: a plain REST route that our page calls; no agent needs to discover it

## Alternatives

- Keep both tools as functions in each agent script: no hop and no key, but every agent copies the code and a fix must be made four times
- Expose fetch_permits only as a REST route: simple, but an agent cannot discover it, so each prompt would have to describe the route by hand

## Reason

Callers: more than one agent, and not only ours, so discovery and reuse win and the server earns its place. The costs are real. Every call is a network hop, the address is public, the key must be kept, and the server holds no state, so anything that must be remembered lives in the caller. We accept the hop because each call takes about a second against a model call of ten. We kept clean_headers a function because one script calls it.

## Evidence

- Address: https://connect.example.edu/team-example-mcp/mcp answers ping with {}
- Tool call log from our agent, asked "how many permits were filed in March?":

```
tools/call fetch_permits {"month": "March"}  ->  412 rows
tools/call summarize_dataset {"rows": 412}   ->  mean 3.1 days
```

## Callers

- Who may call: our four agents and the teaching team's agent, each with a Viewer key; nobody else
- Publisher key: Priya, as a GitHub repository secret named CONNECT_API_KEY; nobody else holds one
