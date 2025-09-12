import requests

url = "https://mctime.com/api/v2/auth/times"
headers = {
    "content-type": "application/json",
    "API_KEY": "TcaUQdZ50CejHsAUDC6Jw4GyLgL0bt6rtTeqdERGGA3cizNc"
}

data = {
    "userId": "123456fb-ae4a-422e-9e90-5ecdbb1af123",
    "times": [
        {
            "from": "2025-09-01T08:00:00+02:00",
            "to": "2025-09-01T17:00:00+02:00",
            "timeType": "work",
            "comment": "Worked on project X",
            "organization": {
                "id": "your_organization_id"
            }
        }
    ]
}

response = requests.post(url, headers=headers, json=data)
print(response.status_code)
print(response.text)