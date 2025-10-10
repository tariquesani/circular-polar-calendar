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

# Get the last three runs
last_three_runs = []
for activity in reversed(data):
    if activity['type'] == 'Run':
        last_three_runs.append(activity)
        if len(last_three_runs) == 3:
            break

# Sort runs by date (earliest first)
last_three_runs.sort(key=lambda x: x['start_date'])

# Write to CSV file
with open('data/lastruns.csv', 'w', newline='') as csvfile:
    fieldnames = ['Name', 'Date', 'Distance (km)', 'Moving Time', 'Average Speed (km/h)', 'Pace (min/km)']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    # writer.writeheader()
    
    for run in last_three_runs:
        name = run['name']
        date = datetime.strptime(run['start_date'], '%Y-%m-%dT%H:%M:%S%z').strftime('%A %d-%b-%Y at %I:%M %p')
        distance_km = convert_to_kilometers(run['distance'])
        moving_time_hms = convert_to_hms(run['moving_time'])
        average_speed_kmh = calculate_average_speed(distance_km, run['moving_time'])
        pace_min_km = calculate_pace(run['moving_time'], distance_km)
        
        writer.writerow({
            'Name': name,
            'Date': date,
            'Distance (km)': f"{distance_km:.2f}",
            'Moving Time': moving_time_hms,
            'Average Speed (km/h)': f"{average_speed_kmh:.2f}",
            'Pace (min/km)': pace_min_km
        })