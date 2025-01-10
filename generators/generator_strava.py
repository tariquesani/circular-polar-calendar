import requests, json, os
from time import time
from datetime import datetime
from stravalib.client import Client
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TOKENS_FILE = "strava_tokens.json"
OUTPUT_FILE = "../data/strava_activities.json"

def load_tokens():
    """Load tokens from a file."""
    return json.load(open(TOKENS_FILE)) if os.path.exists(TOKENS_FILE) else {}

def save_tokens(tokens):
    """Save tokens to a file."""
    json.dump(tokens, open(TOKENS_FILE, 'w'))

def get_initial_tokens(client_id, client_secret, auth_code):
    """Exchange the authorization code for initial tokens."""
    response = requests.post("https://www.strava.com/oauth/token", data={
        'client_id': client_id, 'client_secret': client_secret,
        'code': auth_code, 'grant_type': 'authorization_code'
    })
    response.raise_for_status()
    return response.json()

def refresh_access_token(client_id, client_secret, refresh_token):
    """Refresh the access token using the refresh token."""
    response = requests.post("https://www.strava.com/oauth/token", data={
        'client_id': client_id, 'client_secret': client_secret,
        'grant_type': 'refresh_token', 'refresh_token': refresh_token
    })
    response.raise_for_status()
    return response.json()

def get_valid_access_token():
    """Ensure we have a valid access token, refreshing if necessary."""
    tokens = load_tokens()
    if not tokens:
        auth_url = f"https://www.strava.com/oauth/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri=http://localhost&scope=activity:read_all&approval_prompt=force"
        print(f"No tokens found. Get authorization code at:\n{auth_url}")
        tokens = get_initial_tokens(CLIENT_ID, CLIENT_SECRET, input("Enter authorization code: "))
        save_tokens(tokens)
    elif tokens.get("expires_at", 0) <= time():
        print("Refreshing access token...")
        tokens = refresh_access_token(CLIENT_ID, CLIENT_SECRET, tokens.get("refresh_token"))
        save_tokens(tokens)
    return tokens["access_token"], tokens["refresh_token"]

def fetch_activities(client, start_date, end_date):
    """Fetch activities within the specified date range."""
    return [{
        "id": activity.id,
        "start_date": activity.start_date_local.isoformat(),
        "distance": activity.distance,
        "moving_time": activity.moving_time,
        "elapsed_time": activity.elapsed_time,
        "type": activity.type.root,
        "average_speed": activity.average_speed
    } for activity in client.get_activities(after=start_date, before=end_date)
    if activity.type.root in ("Walk", "Run")]

def main():
    client = Client(access_token=get_valid_access_token()[0])
    try:
        start_date = datetime.strptime(input("Enter start date (YYYY-MM-DD): "), "%Y-%m-%d")
        end_date = datetime.strptime(input("Enter end date (YYYY-MM-DD): "), "%Y-%m-%d")
        activities = fetch_activities(client, start_date, end_date)
        print(f"Found {len(activities)} walk or run activities.")
        json.dump(activities, open(OUTPUT_FILE, 'w'), indent=4)
        print(f"Activities saved to {OUTPUT_FILE}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()