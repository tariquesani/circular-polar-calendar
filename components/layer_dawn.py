from components.data_handler import DataHandler
from components.base_calendar_plotter import BaseCalendarPlotter
from components.layer import Layer
import numpy as np
import matplotlib.pyplot as plt
import math

class DawnLayer(Layer):
    PHASES = [
        ('daylight', 'Daylight', 'Sun above horizon'),
        ('civil', 'Civil Twilight', 'Sun ≤6° below horizon'),
        ('nautical', 'Nautical Twilight', 'Sun 6° to 12° below horizon'),
        ('astro', 'Astronomical Twilight', 'Sun 12° to 18° below horizon'),
        ('night', 'Night', 'Sun > 18° below horizon')
    ]

    def __init__(self, config):
        self.config = config
        self.dawn_data = config.dawn_data
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
        days, smoothen = self.config.days_in_year, self.config.smoothen
        smooth = lambda x: self.data_handler.smooth_data(x, days, smoothen) / 24
        
        data = {
            k: smooth(getattr(self.dawn_data, k))
            for k in ['sunrise', 'civil_dawn', 'nautical_dawn', 'astro_dawn']
        }
        
        x = np.linspace(0, 2*np.pi, days)
        daylight_offset = (self.end_time - self.start_time)/24 * 0.03
        top = (self.end_time/24) - daylight_offset
        
        layers = [
            (0, data['sunrise'], 'night', 2),
            (data['sunrise'], top, 'daylight', 2),
            (data['astro_dawn'], data['nautical_dawn'], 'astro', 3),
            (data['nautical_dawn'], data['civil_dawn'], 'nautical', 3),
            (data['civil_dawn'], data['sunrise'], 'civil', 3)
        ]
        
        for bottom, top, color, zorder in layers:
            ax.fill_between(x, bottom, top, color=self.config.colors[color], zorder=zorder)

    def footer(self, fig: plt.Figure, dims, base: BaseCalendarPlotter):
        ax = fig.add_axes([dims['left'], dims['bottom'], dims['width'], 0.1])
        ax.set_aspect('equal', adjustable='box')
        ax.axis('off')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 0.2)
        
        x_pos = np.linspace(0.1, 0.9, len(self.PHASES))
        for x, (color_key, label, desc) in zip(x_pos, self.PHASES):
            ax.add_patch(plt.Circle((x, 0.15), 0.015, color=self.config.colors[color_key]))
            ax.text(x, 0.125, label, ha='center', va='center', 
                   color=self.config.colors['title_text'], fontsize=8, 
                   alpha=0.7, fontweight='bold')
            ax.text(x, 0.117, desc, ha='center', va='center',
                   color=self.config.colors['title_text'], fontsize=6, alpha=0.5)
