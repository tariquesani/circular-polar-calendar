import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy as np
from typing import List, Tuple

from datetime import date, timedelta

from components.data_types import Config
from components.data_handler import DataHandler


class BaseCalendarPlotter:
    def __init__(self, config: Config, layers=None):
        self.config = config
        self.config.file_name = getattr(
            self.config, 'file_name', self.config.city_name)
        self.layers = layers if layers else []
        self.num_points = self.config.days_in_year
        self.colors = self.config.colors
        self.city_data = self.config.city_data
        self.coordinates = self.city_data.coordinates
        self.year = self.city_data.year
        self.days_in_month = self.city_data.days_in_month
        self.theta_offset = 1.5707963267948966

    @property
    def start_time(self):
        """Calculate the earliest start time across all layers."""
        times = [
            layer.start_time for layer in self.layers if layer.start_time is not None]
        return min(times) if times else 0

    @property
    def end_time(self):
        """Calculate the latest end time across all layers."""
        times = [
            layer.end_time for layer in self.layers if layer.end_time is not None]
        return max(times) if times else 24

    @staticmethod
    def format_coordinates(coords):
        """ Converts a dictionary with latitude and longitude into a formatted string with degree sign and N/S, E/W postfixes. """
        latitude = coords.get('latitude', 0.0)
        longitude = coords.get('longitude', 0.0)

        return f"{abs(latitude):.6f}°{'N' if latitude >= 0 else 'S'},   " \
            f"{abs(longitude):.6f}°{'E' if longitude >= 0 else 'W'}"

    def setup_plot(self) -> Tuple[plt.Figure, plt.Axes]:
        """Initialize and configure the plot."""
        fig, ax = plt.subplots(
            figsize=(24, 24), subplot_kw=dict(polar=True, facecolor=self.config.colors['dial']), dpi=300)
        fig.patch.set_facecolor(self.config.colors['background'])
        ax.set_theta_direction(-1)
        ax.set_theta_offset(np.pi / 2)
        ax.set_ylim(self.start_time/24, self.end_time/24)
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.set_xticks([])
        ax.set_yticks([])

        return fig, ax

    def add_footer(self, fig: plt.Figure) -> None:
        """Add footers from the layers."""
        footer_dimensions = {
            "height": 0.15,
            "width": 0.8,
            "left": (1 - 0.8) / 2,  # Derived from width
            "bottom": 0.15
        }

        # Ask each layer to render its footer
        for layer in self.layers:
            if hasattr(layer, "footer"):
                layer.footer(fig, footer_dimensions, self)

    def add_title(self, ax: plt.Axes) -> None:
        """Add title to the plot."""
        try:
            font_props = {k: FontProperties(fname=f'./fonts/Arvo-{v}.ttf', size=s)
                          for k, v, s in [('bold', 'Bold', 64),
                                          ('regular', 'Regular', 20),
                                          ('year', 'Regular', 48)]}
        except:
            font_props = {k: FontProperties(weight=w, size=s)
                          for k, (w, s) in {'bold': ('bold', 64),
                                            'regular': (None, 20),
                                            'year': (None, 48)}.items()}

        common_props = {'ha': 'center',
                        'va': 'center', 'transform': ax.transAxes}
        ax.text(0.5, 1.23, str(self.year),
                fontproperties=font_props['year'], **common_props)
        ax.text(0.5, 1.18, self.config.city_name,
                fontproperties=font_props['bold'], **common_props)
        ax.text(0.5, 1.13, self.format_coordinates(self.coordinates),
                fontproperties=font_props['regular'], **common_props)

    def create_plot(self, layers) -> None:
        """Create and save the complete dawn calendar plot."""
        # Get layers
        self.layers = layers

        if getattr(self.config, "use_sunday_layer", True):
            from components.layer_sunday import SundayLayer
            self.layers.append(SundayLayer(self.config))

        if getattr(self.config, "use_months_layer", True):
            from components.layer_months import MonthsLayer
            self.layers.append(MonthsLayer(self.config))

        if getattr(self.config, "use_time_layer", True):
            from components.layer_time import TimeLayer
            self.layers.append(TimeLayer(self.config))

        fig, ax = self.setup_plot()

        for layer in layers:
            layer.plot(ax, self)

        # Add title
        self.add_title(ax)

        # Add footer
        self.add_footer(fig)

        # Save plot
        plt.subplots_adjust(top=0.95, bottom=0.3)

        plt.savefig(f'./pdf/{self.config.file_name}.pdf',
                    bbox_inches='tight', pad_inches=1)
        plt.savefig(f'./png/{self.config.file_name}.png',
                    bbox_inches='tight', pad_inches=1)
        plt.close()
