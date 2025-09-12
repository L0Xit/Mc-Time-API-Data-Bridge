import requests

url = "https://mctime.com/api/v2/auth/times"
headers = {
    #"content-type": "application/json",
    "API_KEY": "TcaUQdZ50CejHsAUDC6Jw4GyLgL0bt6rtTeqdERGGA3cizNc"
}

response = requests.get(url, headers=headers)
print(response.status_code)
print(response.text)