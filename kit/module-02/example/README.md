# Character lookup

FIXTURE: hand-written to show a passing folder. No model produced it.

Looks up a character in a public API and shows a table.

## Install
`install.packages(c("shiny", "httr2"))`

## Run
`Rscript -e "shiny::runApp('app.R')"`

## Key
The API needs no key. If yours does, put it in `.env` as `API_KEY` and never commit that file.
