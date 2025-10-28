import json
from datetime import datetime
import csv

def convert_to_kilometers(meters):
    return round(meters / 1000, 2)

def convert_to_hms(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02}:{seconds:02}"
    else:
        return f"{minutes}:{seconds:02}"

def calculate_average_speed(distance_km, moving_time_seconds):
    return round(distance_km / (moving_time_seconds / 3600), 2)

def calculate_pace(moving_time_seconds, distance_km):
    pace_seconds_per_km = moving_time_seconds / distance_km
    minutes = int(pace_seconds_per_km // 60)
    seconds = int(pace_seconds_per_km % 60)
    return f"{minutes}:{seconds:02}"

# Read JSON file
with open('data/strava_activities.json', 'r') as file:
    data = json.load(file)

# Get the last three Run or Yoga activities
last_three_runs = []
for activity in reversed(data):
    if activity.get('type') in ('Run', 'Yoga'):
        last_three_runs.append(activity)
        if len(last_three_runs) == 3:
            break

# Sort runs by date (earliest first)
last_three_runs.sort(key=lambda x: x['start_date'])

# Write to CSV file
with open('data/lastruns.csv', 'w', newline='') as csvfile:
    fieldnames = ['Name', 'Date', 'Distance (km)', 'Moving Time', 'Average Speed (km/h)', 'Pace (min/km)', 'Activity Type']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    # writer.writeheader()
    
    for run in last_three_runs:
        name = run.get('name', '')
        # Handle both date formats: with and without timezone
        start_date_str = run['start_date']
        try:
            # Try parsing with timezone first
            date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M:%S%z')
        except ValueError:
            # If that fails, try parsing without timezone
            date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M:%S')
        
        date = date.strftime('%A %d-%b-%Y at %I:%M %p')
        activity_type = run.get('type', '')

        if activity_type == 'Yoga':
            # Map Yoga-specific fields into the existing CSV columns
            # Distance column -> elapsed_time (seconds -> H:MM:SS)
            elapsed_seconds = run.get('elapsed_time', 0)
            distance_col = convert_to_hms(elapsed_seconds)

            # Moving Time column -> max_heartrate
            moving_time_col = str(run.get('max_heartrate', ''))

            # Average Speed column -> average_heartrate
            avg_speed_col = str(run.get('average_heartrate', ''))

            # Pace column -> calories
            pace_col = str(run.get('calories', ''))

            writer.writerow({
                'Name': name,
                'Date': date,
                'Distance (km)': distance_col,
                'Moving Time': moving_time_col,
                'Average Speed (km/h)': avg_speed_col,
                'Pace (min/km)': pace_col,
                'Activity Type': activity_type
            })
        else:
            # Treat as a Run (default)
            distance_km = convert_to_kilometers(run.get('distance', 0))
            moving_time_hms = convert_to_hms(run.get('moving_time', 0))
            # Avoid division by zero
            if distance_km > 0 and run.get('moving_time', 0) > 0:
                average_speed_kmh = calculate_average_speed(distance_km, run.get('moving_time', 0))
                pace_min_km = calculate_pace(run.get('moving_time', 0), distance_km)
            else:
                average_speed_kmh = 0
                pace_min_km = ''

            writer.writerow({
                'Name': name,
                'Date': date,
                'Distance (km)': f"{distance_km:.2f}",
                'Moving Time': moving_time_hms,
                'Average Speed (km/h)': f"{average_speed_kmh:.2f}",
                'Pace (min/km)': pace_min_km,
                'Activity Type': activity_type
            })