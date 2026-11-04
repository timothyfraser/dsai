# Known-answer and degenerate tests for R/logic.R.
# Run from the plumber folder: Rscript tests/test_logic.R
source("R/logic.R")

# Known answer, worked by hand: 1+2+3+4+5 = 15, 15 / 5 = 3
out = summarize(list(1, 2, 3, 4, 5))
stopifnot(out$n == 5, out$mean == 3, out$min == 1, out$max == 5)

# One value
out = summarize(list(7))
stopifnot(out$n == 1, out$mean == 7)

# Degenerate: empty input must be an error, not a number
stopifnot(inherits(try(summarize(list()), silent = TRUE), "try-error"))

# Text must be an error
stopifnot(inherits(try(summarize(list(1, "two")), silent = TRUE), "try-error"))

cat("PASS: all logic tests\n")
