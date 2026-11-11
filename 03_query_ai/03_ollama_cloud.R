# 03_ollama_cloud.R

# Query Google's free Gemini tier with an API key
# This script calls Google's free Gemini tier through its OpenAI-compatible endpoint,
# using your API key stored in the .env file
# The free tier may use your prompts to improve Google's products, so send only public or made-up data.

# Starting message
cat("\n🚀 Querying Google's Gemini in R...\n")

# If you haven't already, install these packages...
# install.packages(c("httr2", "jsonlite"))

# Load libraries
library(httr2)    # For HTTP requests
library(jsonlite) # For working with JSON

# Load environment variables from .env file
# readRenviron() is a built-in R function that reads .env files
# No external package needed!
if (file.exists(".env")){  readRenviron(".env")  } else {  warning(".env file not found. Make sure it exists in the project root.") }

# Get API key from environment variable
GEMINI_API_KEY = Sys.getenv("GEMINI_API_KEY")

# Check if API key is set
if (GEMINI_API_KEY == "") { stop("GEMINI_API_KEY not found in .env file. Please set it up first.") }

# Gemini API endpoint (OpenAI-compatible)
url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"

MODEL = "gemini-flash-lite-latest"  # Free cloud model

# Construct the request body as a list
body = list(
  model = MODEL,
  messages = list(
    list(
      role = "user",
      content = "Hello! Please respond with: Model is working."
    )
  )
)

# Build and send the POST request to the Gemini API
# If the server is busy (429, 500, 503), httr2 waits and tries again, up to 3 times
res = request(url) %>%
  req_headers(
    "Authorization" = paste0("Bearer ", GEMINI_API_KEY),
    "Content-Type" = "application/json"
  ) %>%
  req_body_json(body) %>%   # Attach the JSON body
  req_method("POST") %>%   # Set HTTP method
  req_retry(max_tries = 3, is_transient = function(r) resp_status(r) %in% c(429, 500, 503)) %>%
  req_error(is_error = function(r) FALSE) %>%
  req_perform()             # Execute the request

# Stop with one plain line if the request still failed
if (resp_status(res) != 200) { stop("Gemini request failed with HTTP status ", resp_status(res), ".") }

# Parse the response JSON
response = resp_body_json(res)

# Extract the model's reply
# The OpenAI-compatible API returns the text in choices[[1]]$message$content
output = response$choices[[1]]$message$content

# Print the model's reply
cat("\n📝 Model Response:\n")
cat(output)
cat("\n")

# Closing message
cat("✅ Gemini query complete.\n")

# Close out of R, and don't save the environment.
q(save = "no")
