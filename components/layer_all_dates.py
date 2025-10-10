from components.base_calendar_plotter import BaseCalendarPlotter
from components.layer import Layer
import numpy as np
import matplotlib.pyplot as plt
from datetime import date, timedelta


class AllDatesLayer(Layer):
    def __init__(self, config):
        self.config = config

    @property
    def start_time(self):
        return None

    @property
    def end_time(self):
        return None

    def plot(self, ax: plt.Axes, base: BaseCalendarPlotter):
        # Get all dates of the year
        first = date(base.year, 1, 1)
        all_dates = [first + timedelta(days=i)
                     for i in range(base.config.days_in_year)]
        relative_offset = (base.end_time - base.start_time)/24 * 0.01
        label_radius = (base.end_time/24) - relative_offset
        cum_days = np.cumsum(base.days_in_month)

        for day in all_dates:
            day_of_year = (day - first).days
            angle = (day_of_year + 0.5) / base.config.days_in_year * 2 * np.pi  # Offset by 0.5 days for 12 PM
            ax.text(angle, label_radius, day.strftime('%d'), ha='center',
                    va='center', rotation=(-np.degrees(angle) + 180) % 360 - 180, fontsize=7, zorder=5)

    def footer(self, fig: plt.Figure, dims, base: BaseCalendarPlotter):
        pass
