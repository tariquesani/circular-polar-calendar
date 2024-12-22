import json
import sys
from dataclasses import dataclass
from typing import List, Tuple, Dict

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle
from matplotlib.font_manager import FontProperties
import yaml

@dataclass
class CityData:
    name: str
    coordinates: str
    data_file: str
    year: int = 2025

@dataclass
class SunData:
    sunrise: List[float]
    sunset: List[float]
    days_in_month: List[int]
    moon_phases: List[float]
    noon: List[float]
    civil: List[List[float]]
    nautical: List[List[float]]
    astro: List[List[float]]

class ConfigurationError(Exception):
    """Raised when there's an error in configuration file."""
    pass

class DawnCalendarPlotter:
    def __init__(self, city: CityData):
        self.city = city
        self.num_interpolated_points = 365
        self.start_time = 4 / 24
        self.end_time = 7.25 / 24
        
        # Configuration
        self.month_labels = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 
                           'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
        self.hour_labels = [
            '4:00AM', '4:15AM', '4:30AM', '4:45AM', '5:00AM', '5:15AM',
            '5:30AM', '5:45AM', '6:00AM', '6:15AM', '6:30AM', '6:45AM'
        ]
        self.hour_ticks = [
            h/24 for h in [4, 4.25, 4.5, 4.75, 5, 5.25, 5.5, 5.75, 6, 6.25, 6.5, 6.75, 7]
        ]

    @staticmethod
    def load_config(config_path: str = "config.yaml") -> CityData:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)

            required_fields = ['name', 'coordinates', 'data_file']
            for field in required_fields:
                if field not in config:
                    raise ConfigurationError(f"Missing required field '{field}' in config file")

            return CityData(
                name=config['name'],
                coordinates=config['coordinates'],
                data_file=config['data_file'],
                year=config.get('year', 2025)
            )
        except FileNotFoundError:
            raise ConfigurationError(f"Configuration file not found: {config_path}")
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Error parsing YAML configuration: {str(e)}")

    def load_sun_data(self) -> SunData:
        """Load sun data from the specified JSON file."""
        try:
            with open(self.city.data_file, 'r') as f:
                data = json.load(f)
            return SunData(**data)
        except FileNotFoundError:
            raise ConfigurationError(f"Sun data file not found: {self.city.data_file}")
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Error parsing sun data JSON file: {str(e)}")
        except TypeError as e:
            raise ConfigurationError(f"Invalid sun data format: {str(e)}")

    @staticmethod
    def create_smooth_data(data_points: List[float], num_points: int = 365) -> np.ndarray:
        """Create smooth periodic data using Fourier series."""
        data_array = np.array(data_points)
        fft_coeffs = np.fft.rfft(data_array)
        
        # Keep only lower frequencies for smoothing
        fft_coeffs[int(len(fft_coeffs) * 0.1):] = 0
        
        return np.fft.irfft(fft_coeffs, num_points)

    def setup_plot(self) -> Tuple[plt.Figure, plt.Axes]:
        """Initialize and configure the plot."""
        fig, ax = plt.subplots(figsize=(24, 24), subplot_kw=dict(polar=True), dpi=300)
        fig.patch.set_facecolor('#faf0e6')
        
        # Configure polar plot
        ax.set_theta_direction(-1)
        ax.set_theta_offset(np.pi / 2)
        ax.set_ylim(self.start_time, self.end_time)
        
        return fig, ax

    def plot_layers(self, ax: plt.Axes, data: SunData) -> None:
        """Plot the various twilight and daylight layers."""
        theta = np.linspace(0, 2*np.pi, self.num_interpolated_points)
        
        # Create smooth data for all layers
        smooth_data = {
            'sunrise': self.create_smooth_data(data.sunrise) / 24,
            'sunset': self.create_smooth_data(data.sunset) / 24,
            'civil_dawn': self.create_smooth_data([d[0] for d in data.civil]) / 24,
            'civil_dusk': self.create_smooth_data([d[1] for d in data.civil]) / 24,
            'nautical_dawn': self.create_smooth_data([d[0] for d in data.nautical]) / 24,
            'nautical_dusk': self.create_smooth_data([d[1] for d in data.nautical]) / 24,
            'astro_dawn': self.create_smooth_data([d[0] for d in data.astro]) / 24,
            'astro_dusk': self.create_smooth_data([d[1] for d in data.astro]) / 24
        }
        
        # Plot layers
        ax.fill_between(theta, smooth_data['sunset'], 1, color='#011F26', zorder=2)
        ax.fill_between(theta, 0, smooth_data['sunrise'], color='#011F26', zorder=2)
        ax.fill_between(theta, smooth_data['sunrise'], self.end_time-0.005, color='#fbba43', zorder=2)
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
        month_ticks_rad = [tick / 365 * 2 * np.pi for tick in month_ticks]
        
        ax.set_xticks(month_ticks_rad)
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        
        # Add labels
        label_height = self.end_time + 0.006
        for angle, label in zip(month_ticks_rad, self.month_labels):
            ax.text(angle, label_height, label, horizontalalignment='center', 
                   fontsize=22, color="#2F4F4F", fontweight='bold')
        
        # Add dividing lines
        for i in range(12):
            angle = cumulative_days[i] / 365 * 2 * np.pi if i < 11 else 2 * np.pi
            ax.plot([angle, angle], [self.start_time, self.end_time], 
                   color='#02735E', linewidth=0.5, zorder=10)

    def add_sunday_labels(self, ax: plt.Axes, days_in_month: List[int]) -> None:
        """Add Sunday date labels."""
        first_sunday = 4  # 0-based indexing
        sundays = [(first_sunday + i * 7) for i in range(52)]
        fixed_label_radius = self.end_time - 0.008
        cumulative_days = np.cumsum(days_in_month)
        
        for day_index in sundays:
            if day_index >= 365:
                continue
                
            angle = day_index / 365 * 2 * np.pi
            month_index = next((i for i, total in enumerate(cumulative_days) 
                              if day_index < total), 11)
            days_before_month = cumulative_days[month_index - 1] if month_index > 0 else 0
            month_day = day_index - days_before_month + 1
            
            rotation = (-np.degrees(angle) + 180) % 360 - 180
            
            ax.text(angle, fixed_label_radius, str(month_day),
                   ha='center', va='center', fontsize=14, color='#696969',
                   rotation=rotation, zorder=5, fontweight='bold')

    def add_hour_labels(self, ax: plt.Axes) -> None:
        """Add hour labels and tick marks."""
        theta = np.linspace(0, 2*np.pi, self.num_interpolated_points)
        
        # Add labels
        for i, label in enumerate(self.hour_labels):
            radius = self.hour_ticks[i]
            ax.text(np.pi / 2, radius, label,
                   ha='left', va='center', fontsize=9,
                   color='#e7fdeb', zorder=10)
        
        # Add tick marks
        for tick in self.hour_ticks:
            ax.fill_between(theta, tick - 0.0001, tick + 0.0001,
                          color='gray', alpha=0.4, zorder=3, linewidth=0)

    def add_title(self, ax: plt.Axes) -> None:
        """Add title and coordinates with custom font."""
        try:
            font_bold = FontProperties(fname='Arvo-Bold.ttf', weight='bold', size=64)
            font_regular = FontProperties(fname='Arvo-Regular.ttf', size=20)
            font_year = FontProperties(fname='Arvo-Regular.ttf', size=48)
        except:
            font_bold = FontProperties(weight='bold', size=64)
            font_regular = FontProperties(size=20)
            font_year = FontProperties(size=48)
        
        ax.text(0.5, 1.18, self.city.name, ha='center', va='center',
               fontproperties=font_bold, transform=ax.transAxes)
        ax.text(0.5, 1.14, self.city.coordinates, ha='center', va='center',
               fontproperties=font_regular, transform=ax.transAxes)
        ax.text(0.5, 1.23, str(self.city.year), ha='center', va='center',
               fontproperties=font_year, transform=ax.transAxes)

    def create_plot(self) -> None:
        """Create and save the complete dawn calendar plot."""
        data = self.load_sun_data()
        fig, ax = self.setup_plot()
        
        self.plot_layers(ax, data)
        self.add_month_labels(ax, data.days_in_month)
        self.add_sunday_labels(ax, data.days_in_month)
        self.add_hour_labels(ax)
        self.add_title(ax)
        
        plt.subplots_adjust(top=0.9)
        plt.savefig(f'{self.city.name}_dawn.pdf', bbox_inches='tight', pad_inches=1)
        plt.savefig(f'{self.city.name}_dawn.png', bbox_inches='tight', pad_inches=1)

        plt.close()

def main():
    try:
        # Load configuration and create plotter
        city_data = DawnCalendarPlotter.load_config()
        plotter = DawnCalendarPlotter(city_data)
        plotter.create_plot()
    except ConfigurationError as e:
        print(f"Configuration error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()