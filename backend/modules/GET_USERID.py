import requests
import os

# SECURITY: Load API key from environment variable
api_key = os.getenv('MCTIME_API_KEY')
if not api_key:
    print("ERROR: MCTIME_API_KEY environment variable not set!")
    print("Please set it in your .env file")
    exit(1)

url = "https://mctime.com/api/v2/auth/users"
headers = {
    "content-type": "application/json",
    "API_KEY": api_key
}

params = {
    "roles": "employee"

}

response = requests.get(url, headers=headers, params=params)
print(response.status_code)
print(response.text)