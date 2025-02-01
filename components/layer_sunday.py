from components.base_calendar_plotter import BaseCalendarPlotter
from components.layer import Layer
import numpy as np
import matplotlib.pyplot as plt
from datetime import date, timedelta

class SundayLayer(Layer):
    def __init__(self, config):
        self.config = config

    @property
    def start_time(self):
        return None
    
    @property
    def end_time(self):
        return None

    def plot(self, ax: plt.Axes, base: BaseCalendarPlotter):
        # Get first Sunday and calculate positions
        first = date(base.year, 1, 1)
        first_sunday = ((first + timedelta(days=(6 - first.weekday()) % 7)) - first).days
        sundays = range(first_sunday, base.config.days_in_year, 7)
        relative_offset = (base.end_time - base.start_time)/24 * 0.013
        label_radius = (base.end_time/24) - relative_offset
        cum_days = np.cumsum(base.days_in_month)
        
        for day_idx in sundays:
            angle = (day_idx + 0.5) / base.config.days_in_year * 2 * np.pi
            month_idx = next((i for i, total in enumerate(cum_days) if day_idx < total), 11)
            month_day = day_idx - (cum_days[month_idx - 1] if month_idx > 0 else 0) + 1
            
            ax.text(angle, label_radius, str(month_day),
                   ha='center', va='center', fontsize=14, 
                   color=self.config.colors['sunday_label'],
                   rotation=(-np.degrees(angle) + 180) % 360 - 180, 
                   zorder=5, fontweight='normal')

    def footer(self, fig: plt.Figure, dims, base: BaseCalendarPlotter):
        pass