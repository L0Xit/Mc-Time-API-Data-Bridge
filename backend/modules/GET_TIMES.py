import requests

url = "https://mctime.com/api/v2/auth/times"
headers = {
    "content-type": "application/json",
    "API_KEY": "bvtA7WVi52MBmu69bRSEEWYSOggNSRKRXJxQc5bPmBPqBXhS"
}

params = {
    "userIds": "6b1dfeb5-9f94-4814-bac6-c1e760990669", # da muss id von user sein 
            "from": "2025-09-01T08:00:00+02:00", # da muss man gui daten nehmen
            "to": "2025-09-01T17:00:00+02:00", # hier auch machma mit parameter etc später erst

}

response = requests.get(url, headers=headers, params=params)
print(response.status_code)
print(response.text)