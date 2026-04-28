library(httr2)

# Create and perform the request
resp <- request("https://api.github.com/users/octocat") |>
  req_perform()

# Check status (will error if not 2xx)
resp <- resp_check_status(resp)

# Print the body as pretty JSON
user_info <- resp_body_json(resp)
print(user_info)