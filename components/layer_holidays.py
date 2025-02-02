from components.base_calendar_plotter import BaseCalendarPlotter
from components.layer import Layer
import numpy as np
import matplotlib.pyplot as plt
from datetime import date, datetime, timedelta
import json
from pathlib import Path
import matplotlib.font_manager as fm  # Add import for font manager

class HolidaysLayer(Layer):
    def __init__(self, config):
        self.config = config
        self.holidays = self._load_holidays()
        self.include_sundays = getattr(config, 'include_sundays', True)  # Add config for including Sundays
        self.font_path = 'fonts/BPmono.ttf'  # Path to the monospaced font
        self.font_prop = fm.FontProperties(fname=self.font_path)  # Load the font properties

    def _load_holidays(self):
        """Load holidays from JSON file."""
        try:
            with open('data/holidays.json', 'r') as f:
                data = json.load(f)
                return [
                    {
                        'name': h['name'],
                        'date': datetime.strptime(h['date'], '%Y-%m-%d').date()
                    }
                    for h in data['holidays']
                ]
        except FileNotFoundError:
            print("Warning: holidays.json not found")
            return []
        except json.JSONDecodeError:
            print("Warning: Invalid JSON in holidays.json")
            return []

    @property
    def start_time(self):
        return None
    
    @property
    def end_time(self):
        return None

    def plot(self, ax: plt.Axes, base: BaseCalendarPlotter):
        if not self.holidays and not self.include_sundays:
            return

        # Calculate positioning
        relative_offset = (base.end_time - base.start_time)/24 * 0.013
        label_radius = (base.end_time/24) - relative_offset
        cum_days = np.cumsum(base.days_in_month)
        
        # Calculate the maximum length of holiday names for padding
        max_name_length = max(len(holiday['name']) for holiday in self.holidays) if self.holidays else 0

        # Plot holidays
        for holiday in self.holidays:
            if holiday['date'].year != base.year:
                continue
                
            day_of_year = (holiday['date'] - date(base.year, 1, 1)).days
            angle = (day_of_year + 0.5) / base.config.days_in_year * 2 * np.pi  # Offset by 0.5 days for 12 PM
            
            month_idx = next((i for i, total in enumerate(cum_days) if day_of_year < total), 11)
            month_day = day_of_year - (cum_days[month_idx - 1] if month_idx > 0 else 0) + 1
            
            rotation = (-np.degrees(angle) + 180) % 360 - 180
            adjusted_rotation = rotation + np.degrees(base.theta_offset) - 90
            
            # Plot date marker
            ax.text(angle, label_radius, str(month_day),
                ha='center', va='center', 
                fontsize=8,
                color=getattr(self.config.colors, 'holiday_label', '#FF0000'),
                rotation=adjusted_rotation,
                zorder=5)
            
            # Determine if the holiday is in the second half of the year
            is_second_half = holiday['date'].month > 6
            
            # Add holiday name with padding and monospaced font
            if is_second_half:
                padded_name = holiday['name'].ljust(max_name_length)  # Left padding for second half
            else:
                padded_name = holiday['name'].rjust(max_name_length)  # Right padding for first half
            
            name_radius = label_radius - relative_offset * 10.5 # Adjust offset as needed
            rotation = (-np.degrees(angle) + 180) % 360 - 90                
            rotation = rotation + np.degrees(base.theta_offset) - 90

            if is_second_half:
                rotation += 180  # Flip the name for the second half of the year
            
            ax.text(angle, name_radius, padded_name,
                ha='center', va='center',  # Keep alignment centered
                fontsize=8,
                fontproperties=self.font_prop,  # Use loaded monospaced font
                color=getattr(self.config.colors, 'holiday_name', '#FF0000'),
                rotation=rotation,
                zorder=50)
            
            # Add marker dot
            marker_radius = label_radius + relative_offset
            ax.plot(angle, marker_radius, 'o',
                color=getattr(self.config.colors, 'holiday_marker', '#FF0000'),
                markersize=3,
                zorder=5)

        # Plot Sundays if configured
        if self.include_sundays:
            first = date(base.year, 1, 1)
            first_sunday = ((first + timedelta(days=(6 - first.weekday()) % 7)) - first).days
            sundays = range(first_sunday, base.config.days_in_year, 7)
            
            for day_idx in sundays:
                angle = (day_idx + 0.5) / base.config.days_in_year * 2 * np.pi
                month_idx = next((i for i, total in enumerate(cum_days) if day_idx < total), 11)
                month_day = day_idx - (cum_days[month_idx - 1] if month_idx > 0 else 0) + 1
                rotation = (-np.degrees(angle) + 180) % 360 - 180
                adjusted_rotation = rotation + np.degrees(base.theta_offset) - 90
                
                ax.text(angle, label_radius, str(month_day),
                    ha='center', va='center', fontsize=7, 
                    color=getattr(self.config.colors, 'sunday_label', '#0000FF'),
                    rotation=adjusted_rotation, 
                    zorder=5, fontweight='normal')

    def footer(self, fig: plt.Figure, dims, base: BaseCalendarPlotter):
        pass