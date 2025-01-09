import requests
import json
import os
from time import time
from datetime import datetime
from stravalib.client import Client

# Replace these with your Strava app credentials
CLIENT_ID = "9967"
CLIENT_SECRET = "4c7662f04bb2376e8b7d7bda6b624a8740643607"
TOKENS_FILE = "strava_tokens.json"
OUTPUT_FILE = "strava_activities.json"

def load_tokens():
    """
    Load tokens from a file.
    """
    if os.path.exists(TOKENS_FILE):
        with open(TOKENS_FILE, 'r') as file:
            return json.load(file)
    return {}

def save_tokens(tokens):
    """
    Save tokens to a file.
    """
    with open(TOKENS_FILE, 'w') as file:
        json.dump(tokens, file)

def get_initial_tokens(client_id, client_secret, auth_code):
    """
    Exchange the authorization code for initial tokens.
    """
    url = "https://www.strava.com/oauth/token"
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': auth_code,
        'grant_type': 'authorization_code',
    }
    response = requests.post(url, data=payload)
    response.raise_for_status()  # Raise error for non-2xx responses
    return response.json()

def refresh_access_token(client_id, client_secret, refresh_token):
    """
    Refresh the access token using the refresh token.
    """
    url = "https://www.strava.com/oauth/token"
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
    }
    response = requests.post(url, data=payload)
    response.raise_for_status()  # Raise error for non-2xx responses
    return response.json()

def get_valid_access_token():
    """
    Ensure we have a valid access token, refreshing it if necessary.
    """
    tokens = load_tokens()

    # If tokens do not exist, get initial tokens using an authorization code
    if not tokens:
        print("No tokens found. Please obtain an authorization code by visiting:")
        print(f"https://www.strava.com/oauth/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri=http://localhost&scope=activity:read_all&approval_prompt=force")
        auth_code = input("Enter the authorization code: ")
        tokens = get_initial_tokens(CLIENT_ID, CLIENT_SECRET, auth_code)
        save_tokens(tokens)

    # Check if access token is still valid
    if tokens.get("expires_at", 0) > time():
        print("Access token is still valid.")
        return tokens["access_token"], tokens["refresh_token"]

    # Refresh the access token if needed
    print("Refreshing access token...")
    new_tokens = refresh_access_token(CLIENT_ID, CLIENT_SECRET, tokens.get("refresh_token"))
    save_tokens(new_tokens)
    return new_tokens["access_token"], new_tokens["refresh_token"]

def fetch_activities(client, start_date, end_date):
    """
    Fetch activities within the specified date range.
    """
    activities = []
    
    for activity in client.get_activities(after=start_date, before=end_date):
        
        if activity.type.root == "Walk" or activity.type.root == "Run":
            # print(f"Processing activity {activity.id}: {activity.type.root}")
            activities.append({
                "id": activity.id,
                "start_date": activity.start_date_local.isoformat(),
                "distance": activity.distance,  # Distance in meters
                "moving_time": activity.moving_time,  # Moving time in seconds
                "elapsed_time": activity.elapsed_time,  # Elapsed time in seconds
                "type": activity.type.root,
                "average_speed": activity.average_speed,  # Speed in meters/second
            })
    return activities

def save_activities_to_file(file_name, activities):
    """
    Save fetched activities to a JSON file.
    """
    with open(file_name, 'w') as file:
        json.dump(activities, file, indent=4)
    print(f"Activities saved to {file_name}")

def main():
    # Get a valid access token
    access_token, refresh_token = get_valid_access_token()

    # Initialize the Strava client with the valid access token
    client = Client()
    client.access_token = access_token

    try:
        # Ask user for date range
        start_date_str = input("Enter start date (YYYY-MM-DD): ")
        end_date_str = input("Enter end date (YYYY-MM-DD): ")
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

        # Fetch activities within the range
        print("Fetching activities...")
        activities = fetch_activities(client, start_date, end_date)
        print(f"There are {len(activities)} walk or run activities.")

        # Save to JSON file
        save_activities_to_file(OUTPUT_FILE, activities)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
