
import requests

def get_employee_emails(api_key):
    url = "https://mctime.com/api/v2/auth/users"
    headers = {
        "content-type": "application/json",
        "API_KEY": api_key
    }
    params = {
        "roles": "employee"
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        users = data.get("items", [{}])[0].get("data", {}).get("users", [])
        emails = [user.get("email") for user in users if user.get("email")]
        return emails
    else:
        print(response.status_code)
        print(response.text)
        return []

# Example usage:
if __name__ == "__main__":
    import os
    # SECURITY: Load API key from environment variable
    api_key = os.getenv('MCTIME_API_KEY')
    if not api_key:
        print("ERROR: MCTIME_API_KEY environment variable not set!")
        print("Please set it in your .env file")
        exit(1)
    emails = get_employee_emails(api_key)
    print(emails)