"""
User ID Module
Fetches user IDs from McTime API
"""

import requests


def get_user_ids(api_key, roles="employee"):
    """
    Fetch all user IDs with specified role.
    
    Args:
        api_key: McTime API key
        roles: User role filter (default: "employee")
    
    Returns:
        Response object with user data
    """
    url = "https://mctime.com/api/v2/auth/users"
    headers = {
        "content-type": "application/json",
        "API_KEY": api_key
    }
    params = {
        "roles": roles
    }
    
    response = requests.get(url, headers=headers, params=params)
    return response


def get_user_id_list(api_key, roles="employee"):
    """
    Fetch user IDs and return as a list.
    
    Returns:
        List of user ID strings
    """
    response = get_user_ids(api_key, roles)
    
    if response.status_code == 200:
        data = response.json()
        users = data.get("items", [{}])[0].get("data", {}).get("users", [])
        return [user.get("id") for user in users if user.get("id")]
    else:
        print(f"Error: {response.status_code}")
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
    
    response = get_user_ids(api_key)
    print(response.status_code)
    print(response.text)
