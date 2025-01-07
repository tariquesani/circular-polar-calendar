import json
from typing import List, Tuple
from components.data_types import DawnData, WeatherData, CityData, SunData


class DataHandler:
    """Initial data handling class with minimal changes from original implementation."""

    def __init__(self, config):
        """Initialize with config object from original implementation."""
        self.city_name = config.city_name
        self.data_file = f"data/{self.city_name}_data.json"

    def load_data(self) -> Tuple[DawnData, WeatherData, CityData]:
        """
        Load data from JSON file, now separated into dawn and weather components.
        Keeps close to original implementation while providing better structure.
        """
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            dawn_data = DawnData(
                sunrise=data['sunrise'],
                civil_dawn=[d[0] for d in data['civil']],
                nautical_dawn=[d[0] for d in data['nautical']],
                astro_dawn=[d[0] for d in data['astro']],
            )

            weather_data = WeatherData(
                temperature=data['temperature'],
                precipitation=data['precipitation'],
                weather_data_year=data['weather_data_year']
            )

            city_data = CityData(
                coordinates=data['coordinates'],
                days_in_month=data['days_in_month'],
                year=data['year']
            )

            sun_data = SunData(
                sunrise=data['sunrise'],
                sunset=data['sunset'],
                civil_dawn=[d[0] for d in data['civil']],
                nautical_dawn=[d[0] for d in data['nautical']],
                astro_dawn=[d[0] for d in data['astro']],
                civil_dusk=[d[1] for d in data['civil']],
                nautical_dusk=[d[1] for d in data['nautical']],
                astro_dusk=[d[1] for d in data['astro']]
            )

            return dawn_data, weather_data, city_data, sun_data

        except FileNotFoundError:
            raise FileNotFoundError(
                f"Sun data file not found: {self.data_file}")
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            raise ValueError(f"Error processing sun data: {str(e)}")

    def smooth_data(self, data: List[float], num_points: int, smoothen: bool = False) -> List[float]:
        """
        Moved smoothing functionality to data handler as it's data processing.
        Keeps original implementation but adds smoothen parameter.
        """
        import numpy as np

        if not smoothen:
            return np.array(data)

        """Create smooth periodic data using Fourier series."""
        fft_coeffs = np.fft.rfft(data)
        # Keep only lower frequencies
        fft_coeffs[int(len(fft_coeffs) * 0.1):] = 0
        return np.fft.irfft(fft_coeffs, num_points)
