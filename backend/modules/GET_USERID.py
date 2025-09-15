import requests

url = "https://mctime.com/api/v2/auth/users"
headers = {
    "content-type": "application/json",
    "API_KEY": "bvtA7WVi52MBmu69bRSEEWYSOggNSRKRXJxQc5bPmBPqBXhS"
}

params = {
    "roles": "employee"

}

response = requests.get(url, headers=headers, params=params)
print(response.status_code)
print(response.text)