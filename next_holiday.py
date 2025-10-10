import json
from datetime import datetime
import os
from pathlib import Path

# Get the project root directory
script_dir = Path(__file__).parent

# Read holidays data
with open(script_dir / 'data' / 'holidays.json', 'r') as f:
    holidays_data = json.load(f)

# Get current date
today = datetime.now().date()

# Find next holiday
next_holiday = min(
    (holiday for holiday in holidays_data['holidays']
     if datetime.fromisoformat(holiday['date']).date() > today),
    key=lambda x: datetime.fromisoformat(x['date']).date()
)

# Format and write output
output = f"[Variables]\nHolidayName={next_holiday['name']}\nHolidayDate={next_holiday['date']}"
with open(script_dir / 'data' / 'Variables.inc', 'w') as f:
    f.write(output)
