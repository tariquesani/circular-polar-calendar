import json
import os
import signal
import webbrowser
from time import time
from datetime import datetime
from threading import Thread
from stravalib.client import Client
from bottle import Bottle, request, run
from dotenv import load_dotenv

# Load environment config
load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TOKENS_FILE = "strava_tokens.json"
OUTPUT_FILE = "../data/strava_activities.json"

# Initialize Bottle app and global auth state
app = Bottle()
auth_code = None
bottle_thread = None


def load_tokens():
    """Load tokens from file."""
    return json.load(open(TOKENS_FILE)) if os.path.exists(TOKENS_FILE) else {}


def save_tokens(tokens):
    """Save tokens to file."""
    json.dump(tokens, open(TOKENS_FILE, 'w'))


def stop_bottle_server():
    """Force stop the Bottle server."""
    if bottle_thread:
        print("Stopping Bottle server...")
        os._exit(0)


# Set up graceful shutdown on Ctrl+C
signal.signal(signal.SIGINT, lambda sig, frame: stop_bottle_server())


def get_valid_access_token(client):
    """Get or refresh Strava access token."""
    global auth_code
    tokens = load_tokens()

    # Handle first-time authentication
    if not tokens:
        print("Starting authentication flow...")
        global bottle_thread
        bottle_thread = Thread(target=lambda: run(
            app, host="localhost", port=8080), daemon=True)
        bottle_thread.start()

        auth_url = f"https://www.strava.com/oauth/authorize?client_id={
            CLIENT_ID}&response_type=code&redirect_uri=http://localhost:8080/exchange_token&scope=activity:read_all&approval_prompt=force"
        webbrowser.open(auth_url)

        while not auth_code:
            pass  # Wait for auth callback
        tokens = client.exchange_code_for_token(
            client_id=CLIENT_ID, client_secret=CLIENT_SECRET, code=auth_code)
        save_tokens(tokens)

    # Refresh token if expired
    if tokens.get("expires_at", 0) <= time():
        print("Refreshing access token...")
        tokens = client.refresh_access_token(
            client_id=CLIENT_ID, client_secret=CLIENT_SECRET, refresh_token=tokens["refresh_token"])
        save_tokens(tokens)

    client.access_token = tokens["access_token"]


@app.route("/exchange_token")
def exchange_token():
    """Callback endpoint for Strava OAuth."""
    global auth_code
    auth_code = request.query.code
    return "Authorization successful! You can close this window."


def fetch_activities(client, start_date, end_date):
    """Fetch and format Strava activities."""
    activities = list(client.get_activities(after=start_date, before=end_date))
    
    if not activities:
        return []
    
    # Fetch detailed activity data for each activity
    detailed_activities = []
    for i, activity in enumerate(activities):
        print(f"Fetching detailed data for activity {i+1}/{len(activities)}: {activity.name}")
        try:
            # Get detailed activity data
            detailed_activity = client.get_activity(activity.id)
            
            detailed_activities.append({
                "id": detailed_activity.id,
                "name": detailed_activity.name,
                "start_date": detailed_activity.start_date_local.isoformat(),
                "distance": detailed_activity.distance,
                "moving_time": detailed_activity.moving_time,
                "elapsed_time": detailed_activity.elapsed_time,
                "type": detailed_activity.type.root,
                "average_speed": detailed_activity.average_speed,
                # Optional fields: not all activities have calories or heart rate info
                "calories": getattr(detailed_activity, 'calories', None),
                "average_heartrate": getattr(detailed_activity, 'average_heartrate', None),
                "max_heartrate": getattr(detailed_activity, 'max_heartrate', None)
            })
        except Exception as e:
            print(f"Error fetching detailed data for activity {activity.id}: {e}")
            # Fall back to basic data if detailed fetch fails
            detailed_activities.append({
                "id": activity.id,
                "name": activity.name,
                "start_date": activity.start_date_local.isoformat(),
                "distance": activity.distance,
                "moving_time": activity.moving_time,
                "elapsed_time": activity.elapsed_time,
                "type": activity.type.root,
                "average_speed": activity.average_speed,
                "calories": None,
                "average_heartrate": None,
                "max_heartrate": None
            })
    
    return detailed_activities


def get_last_activity_date():
    """Get the last activity date from the output file."""
    if os.path.exists(OUTPUT_FILE):
        activities = json.load(open(OUTPUT_FILE))
        if activities:
            last_activity = max(activities, key=lambda x: x["start_date"])
            return datetime.fromisoformat(last_activity["start_date"])
    return None


def main():
    client = Client()
    try:
        get_valid_access_token(client)

        # Check if incremental mode is enabled
        incremental = input("Do you want to fetch activities incrementally? (yes/no): ").strip().lower() == "yes"
        if incremental:
            start_date = get_last_activity_date() or datetime.strptime(input("Enter start date (YYYY-MM-DD): "), "%Y-%m-%d")
        else:
            start_date = datetime.strptime(input("Enter start date (YYYY-MM-DD): "), "%Y-%m-%d")

        end_date = datetime.today() if not (end_date_input := input(
            "Just press enter for today or Enter end date (YYYY-MM-DD): ").strip()) else datetime.strptime(end_date_input, "%Y-%m-%d")

        # Fetch and save activities
        print("Fetching activities...")
        activities = fetch_activities(client, start_date, end_date)
        
        if activities:
            print(f"{len(activities)} new activities found.")
        else:
            print("No new activities found.")
            return

        # Load existing activities if incremental mode is enabled
        existing_activities = []
        if incremental and os.path.exists(OUTPUT_FILE):
            try:
                existing_activities = json.load(open(OUTPUT_FILE))
            except Exception as e:
                print(f"Warning: could not read existing activities from {OUTPUT_FILE}: {e}")

        # Combine existing and newly-fetched activities
        combined = existing_activities + activities

        # Deduplicate by activity id, preferring the activity with the later start_date
        activity_by_id = {}
        for a in combined:
            aid = a.get("id")
            if aid is None:
                continue
            if aid not in activity_by_id:
                activity_by_id[aid] = a
            else:
                # keep the one with the newer start_date (assume more complete)
                try:
                    existing_dt = datetime.fromisoformat(activity_by_id[aid]["start_date"])
                    new_dt = datetime.fromisoformat(a["start_date"])
                    if new_dt > existing_dt:
                        activity_by_id[aid] = a
                except Exception:
                    activity_by_id[aid] = a

        # Sort activities chronologically: oldest first, latest last
        try:
            activities_sorted = sorted(activity_by_id.values(), key=lambda x: datetime.fromisoformat(x["start_date"]))
        except Exception:
            # Fallback to lexical sort of ISO strings
            activities_sorted = sorted(activity_by_id.values(), key=lambda x: x.get("start_date", ""))

        json.dump(activities_sorted, open(OUTPUT_FILE, 'w'), indent=4)
        print(f"Saved {len(activities_sorted)} activities to {OUTPUT_FILE}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        stop_bottle_server()


if __name__ == "__main__":
    main()
