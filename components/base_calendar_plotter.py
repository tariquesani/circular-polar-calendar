import math
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
        self.layers = layers if layers else []
        self.num_points = self.config.days_in_year
        self.colors = self.config.colors
        self.data_handler = DataHandler(self.config)
        self.city_data = self.data_handler.load_data()[2]
        self.coordinates = self.city_data.coordinates
        self.year = self.city_data.year
        self.days_in_month = self.city_data.days_in_month

        # Default values
        self.month_labels = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                             'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']


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
    def generate_hour_ticks(start, end, interval=0.25):
        return [h / 24 for h in BaseCalendarPlotter.frange(start, end, interval)]

    @staticmethod
    def frange(start, stop, step):
        """Generate a range of floating-point numbers."""
        while start < stop:
            yield round(start, 10)  # Avoid floating-point imprecision
            start += step

    @staticmethod
    def generate_hour_labels(start, end, interval=0.25):
        labels = [' ']  # Start with a blank space
        time = start + interval  # Start from the first quarter past the start time
        while time < end - interval:  # Stop before the end time
            hours = int(time)
            minutes = int((time % 1) * 60)
            am_pm = "AM" if hours < 12 else "PM"
            labels.append(f"{(hours - 1) % 12 + 1}:{minutes:02}{am_pm}")
            time += interval  # Increment by the specified interval in minutes
        return labels

    @staticmethod
    def find_first_sunday(year: int) -> int:
        """Calculate the day number (0-based) of the first Sunday in the year."""
        first_day = date(year, 1, 1)
        first_sunday = first_day + \
            timedelta(days=(6 - first_day.weekday()) % 7)
        return (first_sunday - first_day).days

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

    def add_month_labels(self, ax: plt.Axes, days_in_month: List[int]) -> None:
        """Add month labels and dividing lines."""
        cumulative_days = np.cumsum(days_in_month)
        month_ticks = [(cumulative_days[i - 1] if i > 0 else 0) + days_in_month[i] / 2
                       for i in range(12)]
        month_ticks_rad = [tick / self.num_points *
                           2 * np.pi for tick in month_ticks]

        # ax.set_xticks(month_ticks_rad) # Uncomment to see month ticks

        # Add labels and lines
        time_range = self.end_time - self.start_time
        label_height = (self.end_time/24) + (time_range /
                                             24 * 0.03)  # %age of the time range
        for i, (angle, label) in enumerate(zip(month_ticks_rad, self.month_labels)):
            rotation = (-np.degrees(angle) + 180) % 360 - 180
            ax.text(angle, label_height, label, ha='center', va='center', rotation=rotation,
                    fontsize=22, color=self.colors['month_label'], fontweight='bold')

            # Add dividing line
            if i < 11:
                line_angle = cumulative_days[i] / self.num_points * 2 * np.pi
            else:
                line_angle = 2 * np.pi
            ax.plot([line_angle, line_angle], [self.start_time/24, self.end_time/24],
                    color=self.colors['divider'], linewidth=0.5, zorder=10)

    def add_time_labels(self, ax: plt.Axes) -> None:
        """Add hour labels and tick marks."""
        theta = np.linspace(
            0, 2 * np.pi, self.num_points)  # Circular positions
        base_angle_rad = 0 * np.pi / 180  # Base angle in radians for label placement

        for i, label in enumerate(self.hour_labels):
            label = " "+label  # Dirty hack to add some space between axes and labels
            radius = self.hour_ticks[i]  # Distance from the center
            angle_rad = base_angle_rad  # Adjust if needed for different placement

            # Convert radians to degrees for label rotation
            angle_deg = np.degrees(angle_rad)

            # Add hour label with rotation to align along the radial direction
            ax.text(angle_rad, radius, label,
                    ha='left', va='center', fontsize=6,
                    color=self.colors['time_label'], zorder=10,
                    # Align with the radial direction
                    # rotation=-(angle_deg - 90),
                    # Rotate around the anchor point
                    # rotation_mode='anchor'
                    )

            # Add tick marks around the circle
            ax.fill_between(theta, radius - 0.0001, radius + 0.0001,
                            color='gray', alpha=0.4, zorder=3, linewidth=0)

    def add_sunday_labels(self, ax: plt.Axes, days_in_month: List[int]) -> None:
        """Add Sunday date labels."""
        first_sunday = self.find_first_sunday(
            self.config.year)  # Calculate dynamically
        sundays = range(first_sunday, self.num_points, 7)
        fixed_label_radius = (self.end_time/24) - 0.003

        # Calculate offset based on the time range
        time_range = self.end_time - self.start_time
        relative_offset = time_range/24 * 0.018  # %age of the time range
        fixed_label_radius = (self.end_time/24) - relative_offset

        cumulative_days = np.cumsum(days_in_month)

        for day_index in sundays:
            angle = day_index / self.num_points * 2 * np.pi
            month_index = next((i for i, total in enumerate(cumulative_days)
                                if day_index < total), 11)
            days_before_month = cumulative_days[month_index -
                                                1] if month_index > 0 else 0
            month_day = day_index - days_before_month + 1

            rotation = (-np.degrees(angle) + 180) % 360 - 180
            ax.text(angle, fixed_label_radius, str(month_day),
                    ha='center', va='center', fontsize=14, color=self.colors['sunday_label'],
                    rotation=rotation, zorder=5, fontweight='normal')

    def add_footer(self, fig: plt.Figure) -> None:
        """Add a footer with legend explaining different twilight phases and temperature scale."""
        # Define labels and descriptions
        legend_data = [
            {
                "label": "Daylight",
                "description": "Sun above horizon",
                "color": self.colors['daylight']
            },
            {
                "label": "Civil Twilight",
                "description": "Sun ≤6° below horizon",
                "color": self.colors['civil']
            },
            {
                "label": "Nautical Twilight",
                "description": "Sun 6° to 12° below horizon",
                "color": self.colors['nautical']
            },
            {
                "label": "Astronomical Twilight",
                "description": "Sun 12° to 18° below horizon",
                "color": self.colors['astro']
            },
            {
                "label": "Night",
                "description": "Sun > 18° below horizon",
                "color": self.colors['night']
            }
        ]

        # Create footer axes
        footer_height = 0.15
        footer_width = 0.8
        footer_left = (1 - footer_width) / 2
        footer_bottom = 0.15

        # Adjust heights and spacing
        legend_height = 0.1  # Height for the twilight legend
        colorbar_height = 0.005  # Reduced height for the colorbar
        colorbar_bottom = footer_bottom + 0.04  # Move colorbar up

        # Create legend axes
        legend_ax = fig.add_axes([footer_left, colorbar_bottom + colorbar_height - 0.03,
                                  footer_width, legend_height])
        legend_ax.set_aspect('equal', adjustable='box')
        legend_ax.axis('off')

        # Set fixed boundaries for legend
        legend_ax.set_xlim(0, 1)
        legend_ax.set_ylim(0, 0.2)

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
            legend_ax.add_patch(circle)

            legend_ax.text(x, label_y, item['label'],
                           ha='center', va='center',
                           color=self.colors['title_text'],
                           fontsize=8,
                           alpha=0.7,
                           fontweight='bold')

            legend_ax.text(x, desc_y, item['description'],
                           ha='center', va='center',
                           color=self.colors['title_text'],
                           fontsize=6,
                           alpha=0.5,
                           wrap=True)

        # Create colorbar axes and colorbar
        if hasattr(self, 'temp_plot'):
            # Match the x-coordinates with the legend
            colorbar_ax = fig.add_axes([footer_left + 0.2, colorbar_bottom,
                                        footer_width - 0.4, colorbar_height])
            colorbar = plt.colorbar(self.temp_plot, cax=colorbar_ax,
                                    orientation='horizontal')

            # Remove outline and ticks
            colorbar.outline.set_visible(False)
            colorbar.ax.tick_params(size=0)

            # Add temperature label above the colorbar
            colorbar_ax.text(0.5, 1.5, 'Average temperature (°C)',
                             ha='center', va='bottom',
                             transform=colorbar_ax.transAxes,
                             color=self.colors['title_text'],
                             fontsize=8)

            # Set custom ticks to show min, middle, and max temperatures
            ticks = np.linspace(self.temp_min, self.temp_max, 5)
            colorbar.set_ticks(ticks)
            colorbar.set_ticklabels([f'{t:.1f}°C' for t in ticks])

            colorbar.ax.tick_params(labelsize=6)  # Adjust tick label size
            for label in colorbar.ax.get_xticklabels():
                label.set_alpha(0.5)  # Add transparency
                # Match color with other text
                label.set_color(self.colors['title_text'])

    def create_plot(self, layers) -> None:
        """Create and save the complete dawn calendar plot."""
        # Get layers
        self.layers = layers

        self.hour_labels = self.generate_hour_labels(
            self.start_time, self.end_time, self.config.interval)
        self.hour_ticks = self.generate_hour_ticks(
            self.start_time, self.end_time, self.config.interval)

        fig, ax = self.setup_plot()

        for layer in layers:
            layer.plot(ax, self)

        self.add_month_labels(ax, self.days_in_month)
        self.add_sunday_labels(ax, self.days_in_month)
        self.add_time_labels(ax)

        # Add title
        try:
            font_props = {
                'bold': FontProperties(fname='./fonts/Arvo-Bold.ttf', size=64),
                'regular': FontProperties(fname='./fonts/Arvo-Regular.ttf', size=20),
                'year': FontProperties(fname='./fonts/Arvo-Regular.ttf', size=48)
            }
        except:
            font_props = {
                'bold': FontProperties(weight='bold', size=64),
                'regular': FontProperties(size=20),
                'year': FontProperties(size=48)
            }

        ax.text(0.5, 1.18, self.config.city_name, ha='center', va='center',
                fontproperties=font_props['bold'], transform=ax.transAxes)

        coordinate_label = self.format_coordinates(self.coordinates)
        ax.text(0.5, 1.13, coordinate_label, ha='center', va='center',
                fontproperties=font_props['regular'], transform=ax.transAxes)
        ax.text(0.5, 1.23, str(self.year), ha='center', va='center',
                fontproperties=font_props['year'], transform=ax.transAxes)

        # Add footer
        self.add_footer(fig)

        # Save plot
        plt.subplots_adjust(top=0.95, bottom=0.3)

        plt.savefig(f'./pdf/{self.config.city_name}_dawn.pdf',
                    bbox_inches='tight', pad_inches=1)
        plt.savefig(f'./png/{self.config.city_name}_dawn.png',
                    bbox_inches='tight', pad_inches=1)
        plt.close()
