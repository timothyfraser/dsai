---
name: plumber-react-scaffold
description: Scaffold an R plumber backend with a React front end for a DSAI module project - project shape, the four-script contract, roxygen-style route annotations, a CORS filter driven by an environment variable, the Vite dev proxy, and separating logic from the API layer. Use when a student picks R for the API behind a React page.
---

# plumber + React scaffold

Start from [`scaffolds/react-api/plumber/`](../../../scaffolds/react-api/plumber/) and
[`scaffolds/react-api/reactfront/`](../../../scaffolds/react-api/reactfront/). Copy them into
your own repo (the API into `api/`, the page into `web/`) rather than editing them in place.

## Shape

```
yourproject/
  api/
    R/logic.R          <- the real work. plain functions. no plumber.
    tests/test_logic.R <- known-answer and degenerate tests. write this early.
    plumber.R          <- routes. thin. sources R/logic.R.
    testme.R manifestme.R deployme.R README.md
  web/
    src/api.js         <- the ONLY place the API address lives
    src/App.jsx ...
    package.json package-lock.json vite.config.js README.md
```

**`R/logic.R` must not call plumber.** Keeping the logic in ordinary functions is what lets
you check it in a console in ten seconds. See the `logic-first-steering` skill.

## Routes

plumber uses roxygen-style `#*` comments above each function. Two routes are enough to start:
`/health` and one data route. Course style: `=` for assignment, not `<-`.

```r
library(plumber)
source("R/logic.R")

#* @apiTitle Example API

#* Is the API up?
#* @get /health
function() {
  list(status = "ok", version = "1.0.0")
}

#* Count, mean, min and max of a list of numbers
#* @post /summary
function(req, res) {
  tryCatch(
    summarize(req$body$values),
    error = function(e) {
      res$status = 422
      list(detail = conditionMessage(e))
    }
  )
}
```

plumber serves interactive Swagger docs at `/__docs__/`. Check `/health` first, from the
outside, before you wire the page to anything.

## CORS

A page on one address (the browser calls it an origin) cannot read answers from an API on
another address unless the API says yes. This filter must be the first one in `plumber.R`.
Wide open, for your own machine:

```r
#* @filter cors
function(req, res) {
  res$setHeader("Access-Control-Allow-Origin", "*")
  if (req$REQUEST_METHOD == "OPTIONS") {
    res$setHeader("Access-Control-Allow-Methods", "*")
    res$setHeader("Access-Control-Allow-Headers", "*")
    res$status = 200
    return(list())
  }
  plumber::forward()
}
```

Read the allowed origin from an environment variable instead, so one setting on Connect
narrows it to your deployed page's address: replace `"*"` with
`Sys.getenv("CORS_ORIGIN", "*")`, and set `CORS_ORIGIN` in the Connect content's Vars panel,
never in code.

**The local option with no CORS at all:** the Vite dev proxy. `web/vite.config.js` forwards
`/api/...` to the API on your machine (plumber's starter port is 5762, so change the target to
`http://127.0.0.1:5762`), so the browser only ever sees the page's own address.

## Front end

Vite + React (see the `fastapi-react-scaffold` skill; the front end is identical, only the
address differs). The API address lives in `src/api.js`, read from `VITE_API_URL`.

**WARNING: anything named `VITE_` is printed into the public JavaScript.** Every visitor to
your page can read it. The API address is fine there. A key, a token or a password is never
fine there. The API holds the key; the page never does.

## Dependencies

plumber deploys fail most often on unavailable packages. Keep the package list short and
mainstream, and regenerate `manifest.json` (`manifestme.R`, on your machine) every time you add
one. `rsconnect::writeManifest()` scans your code for `library()` calls: if you load a package
dynamically, it is not detected and the deploy will 500.

## Deploy

API and page are two separate pieces of content on Connect. Deploy the API first, set
`VITE_API_URL` to its address, rebuild, then deploy the page. Set `CORS_ORIGIN` on the API to the
page's address. See the `connect-publish` skill.

## The Module 4 baseline

Shiny is the Module 4 baseline: one deployable artifact instead of two, no CORS, no npm. React is
the project: a separate page over an API you can test on its own, which is the shape the rest of
the course builds on. Build the baseline first if you are new to Posit Connect; then build the project.
