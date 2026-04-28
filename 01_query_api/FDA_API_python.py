# FDA_API_python.py
# FDA Open Data API example
# William Manno

import os  # for reading environment variables
import requests  # for making HTTP requests
from dotenv import load_dotenv  # for loading variables from env file

# Load FDA_API_KEY from FDA.env (current dir or project root)
if os.path.exists("FDA.env"):
    load_dotenv("FDA.env")
elif os.path.exists("../FDA.env"):
    load_dotenv("../FDA.env")
else:
    print("FDA.env not found. Set FDA_API_KEY in FDA.env or in your environment.")

# Get the API key from the environment
FDA_API_KEY = os.getenv("FDA_API_KEY")

# Make the API request
response = requests.get("https://api.fda.gov/drug/event.json?limit=1", headers={"x-api-key": FDA_API_KEY})

# Print the response
print(response.status_code)
print(response.json())
globals().clear()