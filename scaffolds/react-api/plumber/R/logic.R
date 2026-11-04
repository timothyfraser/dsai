# The real work, as plain functions. No plumber is loaded here.
# Keeping this file free of plumber is what lets you test it in a console.

summarize = function(values) {
  # Count, mean, min and max of a list of numbers.
  # Stops with a clear message on an empty input or on anything that is not a number.
  if (length(values) == 0) {
    stop("values must be a non-empty list of numbers")
  }
  nums = suppressWarnings(as.numeric(unlist(values)))
  if (anyNA(nums)) {
    stop("every value must be a number")
  }
  list(
    n = length(nums),
    mean = mean(nums),
    min = min(nums),
    max = max(nums)
  )
}
