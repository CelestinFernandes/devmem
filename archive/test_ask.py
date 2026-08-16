import requests
import json

url = "http://localhost:8000/ask"
data = {"question": "How do I set up PostgreSQL connection pool?"}

response = requests.post(url, json=data)
print("Status Code:", response.status_code)
print("Response:", json.dumps(response.json(), indent=2))