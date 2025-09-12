import requests
import json
from typing import Optional

def delete_working_hours(times_id: str, api_key: str, base_url: str = "https://mctime.com/api/v2/auth") -> bool:
    """
    Delete working hours by ID using the API.
    
    Args:
        times_id (str): The ID of the working hours to delete
        api_key (str): Your API key for authentication
        base_url (str): Base URL of the API (default: https://mctime.com/api/v2/auth)
    
    Returns:
        bool: True if deletion was successful, False otherwise
    """
    
    # Construct the endpoint URL
    url = f"{base_url}/times/{times_id}"
    
    # Set up headers with API key
    headers = {
        "API_KEY": api_key,
        "Content-Type": "application/json"
    }
    
    def fetch_times(api_key: str, base_url: str = "https://mctime.com/api/v2/auth", start_date: str = None, end_date: str = None):
        """
        Fetch times from the API and print times IDs, optionally filtering by date range.
        Args:
            api_key (str): Your API key for authentication
            base_url (str): Base URL of the API
            start_date (str): Start date in 'YYYY-MM-DD' format
            end_date (str): End date in 'YYYY-MM-DD' format
        """
        url = f"{base_url}/times"
        headers = {
            "API_KEY": api_key,
            "Content-Type": "application/json"
        }
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                times = response.json()
                for entry in times:
                    entry_date = entry.get("date")
                    if start_date and end_date:
                        if start_date <= entry_date <= end_date:
                            print(f"ID: {entry.get('id')}, Date: {entry_date}")
                    else:
                        print(f"ID: {entry.get('id')}, Date: {entry_date}")
            else:
                print(f"Failed to fetch times. Status code: {response.status_code}")
                print(f"Response: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Error making request: {e}")
    try:
        # Make the DELETE request
        response = requests.delete(url, headers=headers)
        
        # Check if the request was successful
        if response.status_code == 200 or response.status_code == 204:
            print(f"Successfully deleted working hours with ID: {times_id}")
            return True
        # Fetch times and print IDs for the period 2025-09-01 to 2025-09-05
        fetch_times(API_KEY, BASE_URL, start_date="2025-09-01", end_date="2025-09-05")
        print(f"Failed to delete working hours. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return False
            
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return False

# Example usage
if __name__ == "__main__":
    API_KEY = "bvtA7WVi52MBmu69bRSEEWYSOggNSRKRXJxQc5bPmBPqBXhS"
    BASE_URL = "https://mctime.com/api/v2/auth"
    START_DATE = "2025-09-01"
    END_DATE = "2025-09-05"

    # Fetch times and collect IDs for the specified period
    def get_times_ids(api_key, base_url, start_date, end_date):
        url = f"{base_url}/times"
        headers = {
            "API_KEY": api_key,
            "Content-Type": "application/json"
        }
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                times = response.json()
                ids = [entry.get("id") for entry in times if start_date <= entry.get("date", "") <= end_date]
                return ids
            else:
                print(f"Failed to fetch times. Status code: {response.status_code}")
                print(f"Response: {response.text}")
                return []
        except requests.exceptions.RequestException as e:
            print(f"Error making request: {e}")
            return []

    times_ids = get_times_ids(API_KEY, BASE_URL, START_DATE, END_DATE)
    print(f"Found times IDs for {START_DATE} to {END_DATE}: {times_ids}")
    for times_id in times_ids:
        success = delete_working_hours(times_id, API_KEY, BASE_URL)
        if success:
            print(f"Working hours deleted successfully for ID: {times_id}")
        else:
            print(f"Failed to delete working hours for ID: {times_id}")