# manifestme.R
#
# Write a Posit deployment manifest for this Plumber API.
# Run from the plumber folder: Rscript manifestme.R
# Run it on your own machine, never in CI. Commit manifest.json.

if (!requireNamespace("rsconnect", quietly = TRUE)) {
  stop("Please install 'rsconnect' first: install.packages('rsconnect')")
}

# Generate manifest.json in the current app folder.
rsconnect::writeManifest(appDir = ".")

message("Done. manifest.json created in: ", normalizePath(".", winslash = "/"))
