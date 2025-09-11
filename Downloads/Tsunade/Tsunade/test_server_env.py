import requests
import json

# Test what environment the server is actually using
url = "http://localhost:8000/api/v1/chat"
headers = {"Content-Type": "application/json"}
data = {"message": "test"}

print("Testing server environment...")
response = requests.post(url, headers=headers, json=data)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

# Also test a simple endpoint to see if server is responding
health_response = requests.get("http://localhost:8000/health")
print(f"\nHealth check: {health_response.status_code}")
print(f"Health response: {health_response.text}")