import requests
import json

url = "http://localhost:8000/capture"
data = {"raw_text": "I learned how to set up a PostgreSQL connection pool in Python. Setting max_connections to 50 reduced latency."}
response = requests.post(url, json=data)
print("Status Code:", response.status_code)
print("Response:", json.dumps(response.json(), indent=2))