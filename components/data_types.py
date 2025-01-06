from dataclasses import dataclass
from typing import List


@dataclass
class Config:
    city_name: str
    colors: dict
    year: int = 2025
    smoothen: bool = False
    interval: float = 0.25

    @property
    def days_in_year(self) -> int:
        """Calculate number of days in the year accounting for leap years."""
        return 366 if self.year % 4 == 0 and (self.year % 100 != 0 or self.year % 400 == 0) else 365


@dataclass
class DawnData:
    sunrise: List[float]
    civil_dawn: List[float]
    nautical_dawn: List[float]
    astro_dawn: List[float]


@dataclass
class WeatherData:
    temperature: List[float]
    precipitation: List[float]
    weather_data_year: int

@dataclass
class CityData:
    coordinates: dict
    days_in_month: List[int]
    year: int