import requests

url = "https://httpbin.org/post"
payload = {"name": "test"}

response = requests.post(url, json=payload)

# Raise an error for bad responses (4xx/5xx)
response.raise_for_status()

# Print JSON response from server
print(response.json())