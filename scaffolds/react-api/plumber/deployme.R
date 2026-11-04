# deployme.R
#
# Deploy the Plumber API to Posit Connect (not Connect Cloud).
# Run this script from the plumber folder.
#
# This script does NOT write the manifest. Run manifestme.R first, read the
# result, and commit manifest.json. A manifest rewritten silently on every
# deploy hides a dependency change nobody looked at.

if (!requireNamespace("rsconnect", quietly = TRUE)) {
  stop("Please install 'rsconnect' first: install.packages('rsconnect')")
}

if (!file.exists("manifest.json")) {
  stop("manifest.json is missing. Run manifestme.R first, then commit it.")
}

# Option A: the server and account are already configured in rsconnect.
rsconnect::deployApp(appDir = ".")

# Option B (commented): an explicit Connect server and key, read from
# environment variables. Never type the key into this file.
# rsconnect::addServer(url = Sys.getenv("CONNECT_SERVER"), name = "course-connect")
# rsconnect::connectApiUser(server = "course-connect", apiKey = Sys.getenv("CONNECT_API_KEY"))
# rsconnect::deployApp(appDir = ".", server = "course-connect")
