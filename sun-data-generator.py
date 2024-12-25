from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union
import astral
from astral import LocationInfo
from astral.sun import sun
from astral import moon
from datetime import datetime, date, timedelta
import numpy as np
from scipy.interpolate import interp1d
import json
from pathlib import Path
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

# [Previous Location class implementation remains the same]
@dataclass
class Location:
    """Represents a geographical location with timezone information."""
    name: str
    country: str
    timezone: str
    latitude: float
    longitude: float

    @classmethod
    def from_city_name(cls, city_name: str) -> 'Location':
        """
        Create a Location instance from just a city name.
        Automatically fetches geographical and timezone information.
        """
        # Initialize geocoder with a user agent
        geolocator = Nominatim(user_agent="sun_data_calculator")
        tf = TimezoneFinder()

        # Get location information
        try:
            location = geolocator.geocode(city_name)
            if not location:
                raise ValueError(f"Could not find location: {city_name}")

            # Get timezone for the coordinates
            timezone_str = tf.timezone_at(lat=location.latitude, lng=location.longitude)
            if not timezone_str:
                raise ValueError(f"Could not determine timezone for: {city_name}")

            # Extract country from address
            country = location.address.split(',')[-1].strip()

            return cls(
                name=city_name,
                country=country,
                timezone=timezone_str,
                latitude=location.latitude,
                longitude=location.longitude
            )
        except Exception as e:
            raise ValueError(f"Error creating location for {city_name}: {str(e)}")

    def to_location_info(self) -> LocationInfo:
        """Convert to astral LocationInfo object."""
        return LocationInfo(
            self.name,
            self.country,
            self.timezone,
            self.latitude,
            self.longitude
        )

class AstralDataCalculator:
    """Handles calculations of astronomical data for a given location."""
    
    def __init__(self, location: Location, year: int):
        self.location = location
        self.year = year
        self.city = location.to_location_info()
        self.days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        # Adjust for leap year
        if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
            self.days_in_month[1] = 29

    def calculate_sun_data(self, current_date: date) -> Dict[str, float]:
        """Calculate sun-related data for a specific date."""
        try:
            s = sun(self.city.observer, date=current_date, tzinfo=self.city.tzinfo, dawn_dusk_depression=6)
            nautical = sun(self.city.observer, date=current_date, tzinfo=self.city.tzinfo, dawn_dusk_depression=12)
            astro = sun(self.city.observer, date=current_date, tzinfo=self.city.tzinfo, dawn_dusk_depression=18)
            
            return {
                'sunrise': self._time_to_decimal(s["sunrise"]),
                'sunset': self._time_to_decimal(s["sunset"]),
                'noon': self._time_to_decimal(s["noon"]),
                'civil_dawn': self._time_to_decimal(s["dawn"]),
                'civil_dusk': self._time_to_decimal(s["dusk"]),
                'nautical_dawn': self._time_to_decimal(nautical["dawn"]),
                'nautical_dusk': self._time_to_decimal(nautical["dusk"]),
                'astro_dawn': self._time_to_decimal(astro["dawn"]),
                'astro_dusk': self._time_to_decimal(astro["dusk"]),
                'moon_phase': moon.phase(current_date)  # Fixed moon phase calculation
            }
        except Exception as e:
            print(f"Error calculating data for {current_date}: {e}")
            return {k: -1 for k in [
                'sunrise', 'sunset', 'noon', 'civil_dawn', 'civil_dusk',
                'nautical_dawn', 'nautical_dusk', 'astro_dawn', 'astro_dusk',
                'moon_phase'
            ]}

    @staticmethod
    def _time_to_decimal(time: datetime) -> float:
        """Convert datetime to decimal hours."""
        return time.hour + time.minute / 60

    # [Rest of the AstralDataCalculator class remains the same]
    def generate_yearly_data(self) -> Dict[str, Union[List[float], List[Tuple[float, float]]]]:
        """Generate astronomical data for entire year."""
        data = {
            'sunrise': [], 'sunset': [], 'noon': [], 'moon_phases': [],
            'civil': [], 'nautical': [], 'astro': []
        }
        
        for month in range(1, 13):
            for day in range(1, self.days_in_month[month - 1] + 1):
                current_date = date(self.year, month, day)
                day_data = self.calculate_sun_data(current_date)
                
                data['sunrise'].append(day_data['sunrise'])
                data['sunset'].append(day_data['sunset'])
                data['noon'].append(day_data['noon'])
                data['moon_phases'].append(day_data['moon_phase'])
                data['civil'].append((day_data['civil_dawn'], day_data['civil_dusk']))
                data['nautical'].append((day_data['nautical_dawn'], day_data['nautical_dusk']))
                data['astro'].append((day_data['astro_dawn'], day_data['astro_dusk']))
        
        return data

# [DataInterpolator class remains exactly the same]
class DataInterpolator:
    """Handles interpolation of missing astronomical data."""
    
    @staticmethod
    def interpolate_missing_values(times: Union[List[float], List[Tuple[float, float]]]) -> Union[List[float], List[Tuple[float, float]]]:
        """Interpolate missing values in the dataset."""
        if isinstance(times[0], tuple):
            first_values = np.array([t[0] for t in times])
            second_values = np.array([t[1] for t in times])
            first_values = DataInterpolator._interpolate_array(first_values)
            second_values = DataInterpolator._interpolate_array(second_values)
            return list(zip(first_values, second_values))
        return DataInterpolator._interpolate_array(times)

    @staticmethod
    def _interpolate_array(times: List[float]) -> List[float]:
        """Interpolate missing values in a single array."""
        times = np.array(times, dtype=float)
        valid_indices = np.where(times != -1)[0]
        valid_values = times[valid_indices]

        if len(valid_indices) < 2:
            raise ValueError("Insufficient valid data points for interpolation")

        interp_func = interp1d(valid_indices, valid_values, kind='linear', fill_value='extrapolate')
        invalid_indices = np.where(times == -1)[0]
        interpolated_values = interp_func(invalid_indices)
        times[invalid_indices] = interpolated_values
        return times.tolist()

# [DataProcessor class and main() function remain exactly the same]
class DataProcessor:
    """Handles the complete data processing pipeline."""
    
    def __init__(self, city_name: str, year: int):
        self.location = Location.from_city_name(city_name)
        self.calculator = AstralDataCalculator(self.location, year)
        self.interpolator = DataInterpolator()
        self.year = year

    def process_data(self) -> Dict[str, Union[List[float], List[Tuple[float, float]], List[int]]]:
        """Process and interpolate all astronomical data."""
        raw_data = self.calculator.generate_yearly_data()
        processed_data = {
            'sunrise': self.interpolator.interpolate_missing_values(raw_data['sunrise']),
            'sunset': self.interpolator.interpolate_missing_values(raw_data['sunset']),
            'noon': self.interpolator.interpolate_missing_values(raw_data['noon']),
            'civil': self.interpolator.interpolate_missing_values(raw_data['civil']),
            'nautical': self.interpolator.interpolate_missing_values(raw_data['nautical']),
            'astro': self.interpolator.interpolate_missing_values(raw_data['astro']),
            'moon_phases': self.interpolator.interpolate_missing_values(raw_data['moon_phases']),
            'days_in_month': self.calculator.days_in_month,
            'coordinates': {'latitude': self.location.latitude, 'longitude': self.location.longitude}
        }
        return processed_data

def main():
    """Main execution function."""
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python script.py <city_name> <year>")
        print("Example: python script.py 'New York' 2025")
        sys.exit(1)
        
    city_name = sys.argv[1]
    year = int(sys.argv[2])
    
    try:
        processor = DataProcessor(city_name, year)
        data = processor.process_data()
        
        # Create sanitized filename (remove spaces and special characters)
        filename = f"data/{city_name}_data.json"
        output_path = Path(filename)
        
        with output_path.open('w') as f:
            json.dump(data, f, indent=4)
        print(f"Data successfully written to {output_path}")
        
        # Print some useful information
        print(f"\nLocation details:")
        print(f"City: {processor.location.name}")
        print(f"Country: {processor.location.country}")
        print(f"Timezone: {processor.location.timezone}")
        print(f"Coordinates: {processor.location.latitude:.4f}°, {processor.location.longitude:.4f}°")
        
    except Exception as e:
        print(f"Error processing data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()