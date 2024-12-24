import json
from dataclasses import dataclass
from typing import List, Tuple
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.font_manager import FontProperties
import yaml
from datetime import datetime, date, timedelta


@dataclass
class CityData:
    name: str
    coordinates: str
    year: int = 2025
    smoothen: bool = True

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


class ConfigurationError(Exception):
    """Raised when there's an error in configuration file."""
    pass


class DawnCalendarPlotter:
    def __init__(self, city: CityData):
        self.city = city
        self.num_points = self.city.days_in_year
        self.start_time = 4 / 24  # 4 AM
        self.end_time = 7.25 / 24  # 7:15 AM

        # Configuration
        self.month_labels = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                             'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
        self.hour_labels = [
            ' ', '4:15AM', '4:30AM', '4:45AM', '5:00AM', '5:15AM',
            '5:30AM', '5:45AM', '6:00AM', '6:15AM', '6:30AM', '6:45AM'
        ]
        self.hour_ticks = [
            h/24 for h in [4, 4.25, 4.5, 4.75, 5, 5.25, 5.5, 5.75, 6, 6.25, 6.5, 6.75, 7]
        ]

    @staticmethod
    def find_first_sunday(year: int) -> int:
        """Calculate the day number (0-based) of the first Sunday in the year."""
        first_day = date(year, 1, 1)
        first_sunday = first_day + \
            timedelta(days=(6 - first_day.weekday()) % 7)
        return (first_sunday - first_day).days

    @staticmethod
    def load_config(config_path: str = "config.yaml") -> CityData:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            required_fields = ['name', 'coordinates']
            missing_fields = [
                field for field in required_fields if field not in config]
            if missing_fields:
                raise ConfigurationError(f"Missing required fields: {
                                         ', '.join(missing_fields)}")

            return CityData(**config)
        except FileNotFoundError:
            raise ConfigurationError(
                f"Configuration file not found: {config_path}")
        except yaml.YAMLError as e:
            raise ConfigurationError(
                f"Error parsing YAML configuration: {str(e)}")

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
                astro_dawn=[d[0] for d in data['astro']]
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
        ax.set_ylim(self.start_time, self.end_time)
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
        ax.fill_between(theta, smooth_data['sunrise'], self.end_time-0.005,
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
        label_height = self.end_time + 0.006
        for i, (angle, label) in enumerate(zip(month_ticks_rad, self.month_labels)):
            ax.text(angle, label_height, label, ha='center',
                    fontsize=22, color="#2F4F4F", fontweight='bold')

            # Add dividing line
            if i < 11:
                line_angle = cumulative_days[i] / self.num_points * 2 * np.pi
            else:
                line_angle = 2 * np.pi
            ax.plot([line_angle, line_angle], [self.start_time, self.end_time],
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
                    ha='left', va='center', fontsize=9,
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
        fixed_label_radius = self.end_time - 0.008
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
        data = self.load_dawn_data()
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
        ax.text(0.5, 1.14, self.city.coordinates, ha='center', va='center',
                fontproperties=font_props['regular'], transform=ax.transAxes)
        ax.text(0.5, 1.23, str(self.city.year), ha='center', va='center',
                fontproperties=font_props['year'], transform=ax.transAxes)

        plt.subplots_adjust(top=0.9)
        plt.savefig(f'./pdf/{self.city.name}_dawn.pdf',
                    bbox_inches='tight', pad_inches=1)
        plt.savefig(f'./png/{self.city.name}_dawn.png',
                    bbox_inches='tight', pad_inches=1)
        plt.close()


def main():
    try:
        city_data = DawnCalendarPlotter.load_config()
        plotter = DawnCalendarPlotter(city_data)
        plotter.create_plot()
    except ConfigurationError as e:
        print(f"Configuration error: {str(e)}")
        exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()
