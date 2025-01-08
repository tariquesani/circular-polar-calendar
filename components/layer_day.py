from components.data_handler import DataHandler
from components.base_calendar_plotter import BaseCalendarPlotter
from components.layer import Layer
import numpy as np
import matplotlib.pyplot as plt
import math


class DayLayer(Layer):
    def __init__(self, config):
        self.config = config
        self.day_data = config.sun_data
        self.data_handler = DataHandler(self.config)

    @property
    def start_time(self):
        """Calculate the earliest astronomical dawn."""
        return 0
    
    @property
    def end_time(self):
        """Calculate the latest sunrise."""
        return 24

    def plot(self, ax: plt.Axes, base: BaseCalendarPlotter):
        # Plot day layers
        smooth_data = {
            'sunrise': self.data_handler.smooth_data(self.day_data.sunrise, self.config.days_in_year, self.config.smoothen) / 24,
            'sunset': self.data_handler.smooth_data(self.day_data.sunset, self.config.days_in_year, self.config.smoothen) / 24,
            'civil_dawn': self.data_handler.smooth_data(self.day_data.civil_dawn, self.config.days_in_year, self.config.smoothen) / 24,
            'nautical_dawn': self.data_handler.smooth_data(self.day_data.nautical_dawn, self.config.days_in_year, self.config.smoothen) / 24,
            'astro_dawn': self.data_handler.smooth_data(self.day_data.astro_dawn, self.config.days_in_year, self.config.smoothen) / 24,
            'civil_dusk': self.data_handler.smooth_data(self.day_data.civil_dusk, self.config.days_in_year, self.config.smoothen) / 24,
            'nautical_dusk': self.data_handler.smooth_data(self.day_data.nautical_dusk, self.config.days_in_year, self.config.smoothen) / 24,
            'astro_dusk': self.data_handler.smooth_data(self.day_data.astro_dusk, self.config.days_in_year, self.config.smoothen) / 24
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
        ax.fill_between(
            np.linspace(0, 2*np.pi, self.config.days_in_year), smooth_data['sunset'],(self.end_time/24)-daylight_offset, color=self.config.colors['night'], zorder=2)
        ax.fill_between(np.linspace(0, 2*np.pi, self.config.days_in_year), smooth_data['sunset'], smooth_data['civil_dusk'],
                        color=self.config.colors['civil'], zorder=3)
        ax.fill_between(np.linspace(0, 2*np.pi, self.config.days_in_year), smooth_data['civil_dusk'], smooth_data['nautical_dusk'],
                        color=self.config.colors['nautical'], zorder=3)
        ax.fill_between(np.linspace(0, 2*np.pi, self.config.days_in_year), smooth_data['nautical_dusk'], smooth_data['astro_dusk'],
                        color=self.config.colors['astro'], zorder=3)        

    def footer(self, fig: plt.Figure, footer_dimensions, base: BaseCalendarPlotter):
        """Add a footer with legend explaining different twilight phases and temperature scale."""

        legend_data = [
            {
                "label": "Daylight",
                "description": "Sun above horizon",
                "color": self.config.colors['daylight']
            },
            {
                "label": "Civil Twilight",
                "description": "Sun ≤6° below horizon",
                "color": self.config.colors['civil']
            },
            {
                "label": "Nautical Twilight",
                "description": "Sun 6° to 12° below horizon",
                "color": self.config.colors['nautical']
            },
            {
                "label": "Astronomical Twilight",
                "description": "Sun 12° to 18° below horizon",
                "color": self.config.colors['astro']
            },
            {
                "label": "Night",
                "description": "Sun > 18° below horizon",
                "color": self.config.colors['night']
            }
        ]
        # Adjust heights and spacing
        legend_height = 0.1  # Height for the twilight legend

        # Create legend axes
        ax = fig.add_axes([footer_dimensions['left'], footer_dimensions['bottom'],
                           footer_dimensions['width'], legend_height])
        ax.set_aspect('equal', adjustable='box')
        ax.axis('off')

        # Set fixed boundaries for legend
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 0.2)

        # Draw legend elements
        num_items = len(legend_data)
        x_positions = np.linspace(0.1, 0.9, num_items)
        circle_radius = 0.015
        circle_y = 0.15
        label_y = 0.125
        desc_y = 0.117

        for x, item in zip(x_positions, legend_data):
            circle = plt.Circle((x, circle_y), circle_radius,
                                color=item['color'],
                                alpha=1)
            ax.add_patch(circle)

            ax.text(x, label_y, item['label'],
                    ha='center', va='center',
                    color=self.config.colors['title_text'],
                    fontsize=8,
                    alpha=0.7,
                    fontweight='bold')

            ax.text(x, desc_y, item['description'],
                    ha='center', va='center',
                    color=self.config.colors['title_text'],
                    fontsize=6,
                    alpha=0.5,
                    wrap=True)
