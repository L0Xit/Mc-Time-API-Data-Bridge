import requests
import os

# SECURITY: Load API key from environment variable
api_key = os.getenv('MCTIME_API_KEY')
if not api_key:
    print("ERROR: MCTIME_API_KEY environment variable not set!")
    print("Please set it in your .env file")
    exit(1)

url = "https://mctime.com/api/v2/auth/times"
headers = {
    "content-type": "application/json",
    "API_KEY": api_key
}

params = {
    "userIds": "6b1dfeb5-9f94-4814-bac6-c1e760990669", # da muss id von user sein 
            "from": "2025-09-01T08:00:00+02:00", # da muss man gui daten nehmen
            "to": "2025-09-01T17:00:00+02:00", # hier auch machma mit parameter etc später erst

}

response = requests.get(url, headers=headers, params=params)
print(response.status_code)
print(response.text)