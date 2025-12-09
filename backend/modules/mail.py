"""
Mail Module
Fetches employee email addresses from McTime API
"""

import requests


def get_employee_emails(api_key):
    """
    Fetch all employee email addresses.
    Returns a list of email strings.
    """
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
    import sys
    
    # Add parent directory for config import
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
    try:
        from config.settings import get_settings
        api_key = get_settings().MCTIME_API_KEY
    except ImportError:
        api_key = os.getenv('MCTIME_API_KEY')
    
    if not api_key:
        print("ERROR: MCTIME_API_KEY not set!")
        exit(1)
    
    emails = get_employee_emails(api_key)
    print(emails)
