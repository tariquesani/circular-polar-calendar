import json
import matplotlib.pyplot as plt
import numpy as np
import sys
import yaml
import math
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from typing import List, Tuple
from matplotlib.font_manager import FontProperties


@dataclass
class Config:
    name: str
    year: int = 2025
    smoothen: bool = False

    @property
    def days_in_year(self) -> int:
        """Calculate number of days in the year accounting for leap years."""
        return 366 if self.year % 4 == 0 and (self.year % 100 != 0 or self.year % 400 == 0) else 365


@dataclass
class DawnData:
    sunrise: List[float]
    days_in_month: List[int]
    civil_dawn: List[float]
    nautical_dawn: List[float]
    astro_dawn: List[float]
    coordinates: dict
    year: int


class ConfigurationError(Exception):
    """Raised when there's an error in configuration file."""
    pass


class DawnCalendarPlotter:
    def __init__(self, city: Config):
        self.city = city
        self.num_points = self.city.days_in_year
        # Load dawn and twilight data, but now also city coordinates TODO: separate this
        self.dawn_data = self.load_dawn_data()
        self.coordinates = self.dawn_data.coordinates
        self.year = self.dawn_data.year

        # Default values
        self.month_labels = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                             'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']

        # Calculate plotting time boundaries based on astronomical data.
        self.start_time = math.floor(min(self.dawn_data.astro_dawn)*4)/4
        self.end_time = (math.ceil(max(self.dawn_data.sunrise)*4)/4)+0.25

        print(f"Start time: {self.start_time}, End time: {self.end_time}")

        self.hour_labels = self.generate_hour_labels(
            self.start_time, self.end_time)
        self.hour_ticks = self.generate_hour_ticks(
            self.start_time, self.end_time)

    @staticmethod
    def generate_hour_ticks(start, end):
        return [h / 24 for h in DawnCalendarPlotter.frange(start, end, 0.25)]

    @staticmethod
    def frange(start, stop, step):
        """Generate a range of floating-point numbers."""
        while start < stop:
            yield round(start, 10)  # Avoid floating-point imprecision
            start += step

    @staticmethod
    def generate_hour_labels(start, end):
        labels = [' ']  # Start with a blank space
        time = start + 0.25  # Start from the first quarter past the start time
        while time < end - 0.25:  # Stop before the end time
            hours = int(time)
            minutes = int((time % 1) * 60)
            am_pm = "AM" if hours < 12 else "PM"
            labels.append(f"{(hours - 1) % 12 + 1}:{minutes:02}{am_pm}")
            time += 0.25  # Increment by 15 minutes
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

    def load_dawn_data(self) -> DawnData:
        """Load and extract only dawn-related data from the JSON file."""
        try:
            data_file = f"data/{self.city.name}_data.json"
            with open(data_file, 'r') as f:
                data = json.load(f)

            return DawnData(
                sunrise=data['sunrise'],
                days_in_month=data['days_in_month'],
                civil_dawn=[d[0] for d in data['civil']],
                nautical_dawn=[d[0] for d in data['nautical']],
                astro_dawn=[d[0] for d in data['astro']],
                coordinates=data['coordinates'],
                year=data['year']
            )
        except FileNotFoundError:
            raise ConfigurationError(f"Sun data file not found: {
                                     self.city.data_file}")
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            raise ConfigurationError(f"Error processing sun data: {str(e)}")

    def smooth_data(self, data: List[float], num_points: int) -> np.ndarray:
        if not self.city.smoothen:
            return np.array(data)

        """Create smooth periodic data using Fourier series."""
        fft_coeffs = np.fft.rfft(data)
        # Keep only lower frequencies
        fft_coeffs[int(len(fft_coeffs) * 0.1):] = 0
        return np.fft.irfft(fft_coeffs, num_points)

    def setup_plot(self) -> Tuple[plt.Figure, plt.Axes]:
        """Initialize and configure the plot."""
        fig, ax = plt.subplots(
            figsize=(24, 24), subplot_kw=dict(polar=True), dpi=300)
        fig.patch.set_facecolor('#faf0e6')
        ax.set_theta_direction(-1)
        ax.set_theta_offset(np.pi / 2)
        ax.set_ylim(self.start_time/24, self.end_time/24)
        return fig, ax

    def plot_layers(self, ax: plt.Axes, data: DawnData) -> None:
        """Plot the dawn twilight layers."""
        theta = np.linspace(0, 2*np.pi, self.num_points)

        # Smooth only the required data
        smooth_data = {
            'sunrise': self.smooth_data(data.sunrise, self.num_points) / 24,
            'civil_dawn': self.smooth_data(data.civil_dawn, self.num_points) / 24,
            'nautical_dawn': self.smooth_data(data.nautical_dawn, self.num_points) / 24,
            'astro_dawn': self.smooth_data(data.astro_dawn, self.num_points) / 24
        }

        # Plot dawn layers
        ax.fill_between(
            theta, 0, smooth_data['sunrise'], color='#011F26', zorder=2)
        ax.fill_between(theta, smooth_data['sunrise'], (self.end_time/24)-0.005,
                        color='#fbba43', zorder=2)
        ax.fill_between(theta, smooth_data['astro_dawn'], smooth_data['nautical_dawn'],
                        color='#092A38', zorder=2, alpha=0.8)
        ax.fill_between(theta, smooth_data['nautical_dawn'], smooth_data['civil_dawn'],
                        color='#0A3F4D', zorder=2, alpha=0.7)
        ax.fill_between(theta, smooth_data['civil_dawn'], smooth_data['sunrise'],
                        color='#1C5C7C', zorder=2, alpha=0.85)

    def add_month_labels(self, ax: plt.Axes, days_in_month: List[int]) -> None:
        """Add month labels and dividing lines."""
        cumulative_days = np.cumsum(days_in_month)
        month_ticks = [(cumulative_days[i - 1] if i > 0 else 0) + days_in_month[i] / 2
                       for i in range(12)]
        month_ticks_rad = [tick / self.num_points *
                           2 * np.pi for tick in month_ticks]

        ax.set_xticks(month_ticks_rad)
        ax.set_xticklabels([])
        ax.set_yticklabels([])

        # Add labels and lines
        label_height = (self.end_time/24) + 0.006
        for i, (angle, label) in enumerate(zip(month_ticks_rad, self.month_labels)):
            ax.text(angle, label_height, label, ha='center',
                    fontsize=22, color="#2F4F4F", fontweight='bold')

            # Add dividing line
            if i < 11:
                line_angle = cumulative_days[i] / self.num_points * 2 * np.pi
            else:
                line_angle = 2 * np.pi
            ax.plot([line_angle, line_angle], [self.start_time/24, self.end_time/24],
                    color='#02735E', linewidth=0.5, zorder=10)

    def add_time_labels(self, ax: plt.Axes) -> None:
        """Add hour labels and tick marks."""
        theta = np.linspace(
            0, 2 * np.pi, self.num_points)  # Circular positions
        base_angle_rad = 75 * np.pi / 180  # Base angle in radians for label placement

        for i, label in enumerate(self.hour_labels):
            radius = self.hour_ticks[i]  # Distance from the center
            angle_rad = base_angle_rad  # Adjust if needed for different placement

            # Convert radians to degrees for label rotation
            angle_deg = np.degrees(angle_rad)

            # Add hour label with rotation to align along the radial direction
            ax.text(angle_rad, radius, label,
                    ha='left', va='center', fontsize=6,
                    color='#e7fdeb', zorder=10,
                    # Align with the radial direction
                    rotation=-(angle_deg - 90),
                    rotation_mode='anchor')  # Rotate around the anchor point

            # Add tick marks around the circle
            ax.fill_between(theta, radius - 0.0001, radius + 0.0001,
                            color='gray', alpha=0.4, zorder=3, linewidth=0)

    def add_sunday_labels(self, ax: plt.Axes, days_in_month: List[int]) -> None:
        """Add Sunday date labels."""
        first_sunday = self.find_first_sunday(
            self.city.year)  # Calculate dynamically
        sundays = range(first_sunday, self.num_points, 7)
        fixed_label_radius = (self.end_time/24) - 0.008
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
                    ha='center', va='center', fontsize=14, color='#696969',
                    rotation=rotation, zorder=5, fontweight='bold')

    def create_plot(self) -> None:
        """Create and save the complete dawn calendar plot."""
        data = self.dawn_data
        fig, ax = self.setup_plot()

        self.plot_layers(ax, data)
        self.add_month_labels(ax, data.days_in_month)
        self.add_sunday_labels(ax, data.days_in_month)
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

        ax.text(0.5, 1.18, self.city.name, ha='center', va='center',
                fontproperties=font_props['bold'], transform=ax.transAxes)

        coordinate_label = self.format_coordinates(self.coordinates)
        ax.text(0.5, 1.14, coordinate_label, ha='center', va='center',
                fontproperties=font_props['regular'], transform=ax.transAxes)
        ax.text(0.5, 1.23, str(self.year), ha='center', va='center',
                fontproperties=font_props['year'], transform=ax.transAxes)

        plt.subplots_adjust(top=0.9)
        plt.savefig(f'./pdf/{self.city.name}_dawn.pdf',
                    bbox_inches='tight', pad_inches=1)
        plt.savefig(f'./png/{self.city.name}_dawn.png',
                    bbox_inches='tight', pad_inches=1)
        plt.close()


def load_config(config_path: str = "config.yaml") -> Config:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        required_fields = ['name']
        missing_fields = [
            field for field in required_fields if field not in config]
        if missing_fields:
            raise ConfigurationError(f"Missing required fields: {
                ', '.join(missing_fields)}")

        return Config(**config)
    except FileNotFoundError:
        raise ConfigurationError(
            f"Configuration file not found: {config_path}")
    except yaml.YAMLError as e:
        raise ConfigurationError(
            f"Error parsing YAML configuration: {str(e)}")


def main():
    try:
        city_name = sys.argv[1] if len(sys.argv) > 1 else None
        config = load_config()

        if city_name:
            config.name = city_name

        plotter = DawnCalendarPlotter(config)
        plotter.create_plot()
    except ConfigurationError as e:
        print(f"Configuration error: {str(e)}")
        exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()
