"""
Times Module
Fetches time entries from McTime API
"""

import requests


def get_times(api_key, user_ids, date_from, date_to):
    """
    Fetch time entries for specified users and date range.
    
    Args:
        api_key: McTime API key
        user_ids: Comma-separated string of user IDs or a single user ID
        date_from: Start date in ISO format (e.g., "2025-09-01T08:00:00+02:00")
        date_to: End date in ISO format (e.g., "2025-09-01T17:00:00+02:00")
    
    Returns:
        Response object or None on error
    """
    url = "https://mctime.com/api/v2/auth/times"
    headers = {
        "content-type": "application/json",
        "API_KEY": api_key
    }
    params = {
        "userIds": user_ids,
        "from": date_from,
        "to": date_to,
    }
    
    response = requests.get(url, headers=headers, params=params)
    return response


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
    
    # Example call
    response = get_times(
        api_key,
        user_ids="6b1dfeb5-9f94-4814-bac6-c1e760990669",
        date_from="2025-09-01T08:00:00+02:00",
        date_to="2025-09-01T17:00:00+02:00"
    )
    
    print(response.status_code)
    print(response.text)
