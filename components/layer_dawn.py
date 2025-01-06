from components.data_handler import DataHandler
from components.base_calendar_plotter import BaseCalendarPlotter
from components.layer import Layer
import numpy as np
import matplotlib.pyplot as plt
import math


class DawnLayer(Layer):
    def __init__(self, dawn_data, config):
        self.dawn_data = dawn_data
        self.config = config
        self.data_handler = DataHandler(self.config)

    @property
    def start_time(self):
        """Calculate the earliest astronomical dawn."""
        return math.floor(min(self.dawn_data.astro_dawn) * 4) / 4

    @property
    def end_time(self):
        """Calculate the latest sunrise."""
        return math.ceil(max(self.dawn_data.sunrise) * 4) / 4 + 0.25

    def plot(self, ax: plt.Axes, base: BaseCalendarPlotter):
        # Plot dawn layers
        smooth_data = {
            'sunrise': self.data_handler.smooth_data(self.dawn_data.sunrise, self.config.days_in_year, self.config.smoothen) / 24,
            'civil_dawn': self.data_handler.smooth_data(self.dawn_data.civil_dawn, self.config.days_in_year, self.config.smoothen) / 24,
            'nautical_dawn': self.data_handler.smooth_data(self.dawn_data.nautical_dawn, self.config.days_in_year, self.config.smoothen) / 24,
            'astro_dawn': self.data_handler.smooth_data(self.dawn_data.astro_dawn, self.config.days_in_year, self.config.smoothen) / 24
        }

        time_range = self.end_time - self.start_time
        daylight_offset = time_range/24 * 0.03  # 3% of time range

        ax.fill_between(
            np.linspace(0, 2*np.pi, self.config.days_in_year), 0, smooth_data['sunrise'], color=self.config.colors['night'], zorder=2)
        ax.fill_between(np.linspace(0, 2*np.pi, self.config.days_in_year), smooth_data['sunrise'], (self.end_time/24)-daylight_offset,
                        color=self.config.colors['daylight'], zorder=2)
        ax.fill_between(np.linspace(0, 2*np.pi, self.config.days_in_year), smooth_data['astro_dawn'], smooth_data['nautical_dawn'],
                        color=self.config.colors['astro'], zorder=3)
        ax.fill_between(np.linspace(0, 2*np.pi, self.config.days_in_year), smooth_data['nautical_dawn'], smooth_data['civil_dawn'],
                        color=self.config.colors['nautical'], zorder=3)
        ax.fill_between(np.linspace(0, 2*np.pi, self.config.days_in_year), smooth_data['civil_dawn'], smooth_data['sunrise'],
                        color=self.config.colors['civil'], zorder=3)
