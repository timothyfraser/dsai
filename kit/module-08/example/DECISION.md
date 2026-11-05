# Agent decision: team example

## Job

Turn the FDA drug-shortage data into a one-page press release for the campus pharmacy office, with every drug named in the release listed in the data.

## Choice

Many agents: an analyst agent, then a press release agent, with plain code between them.

## Alternatives

- One agent with one long prompt that analyzes and writes
- No agent: a template that fills a sentence per shortage row, with no model at all

## Reason

The template wins on calls, tokens and latency (zero model calls) and is the easiest to test, but its sentences read as a table in prose and the pharmacy office wants a headline and a summary. One agent costs one call, yet when it fails we cannot tell whether the analysis or the writing was wrong. Two agents cost two calls and about twice the latency. We accept that, because the analyst's output is a table we can test before the writer sees it. An error in the analyst would otherwise travel into the release unseen.

## Evidence

Run 3 of the chain, where the analyst invented a drug "Zolmaxin" that the data never listed:

```
analyst  rows=12 drugs=11
check    FAIL  1 drug not in data: Zolmaxin
writer   skipped (check failed)
```

## Checks

Between the analyst and the writer, plain code parses the table, counts the rows and rejects any drug name that is not in the data. The writer runs only after that check passes. After the writer, a second check compares the drug names in the release with the same list.
