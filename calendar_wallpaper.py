"""Wallpaper Calendar Plotter - Generates a 4K wallpaper with circular calendar visualization."""

import sys
import traceback
from dataclasses import dataclass
from typing import Dict
from components.config import ConfigurationError, load_config
from components.data_handler import DataHandler
from components.wallpaper_calendar_plotter import WallpaperCalendarPlotter
from components.layer_dawn import DawnLayer
from components.layer_temperature import TemperatureLayer
from components.layer_strava import StravaLayer

@dataclass
class WallpaperConfig:
    width: int = 3840
    height: int = 2160
    calendar_position: Dict[str, float] = None
    arc_degrees: int = 90

    def __post_init__(self):
        if self.calendar_position is None:
            self.calendar_position = {
                "left": -0.2,
                "bottom": -0.3,
                "width": 1.2,
                "height": 1.2
            }


def main():
    try:
        # Setup configuration
        config = load_config()
        config.city_name = sys.argv[1] if len(sys.argv) > 1 else config.city_name
        config.file_name = f"{config.city_name}_Wallpaper"
        config.wallpaper_mode = True
        config.running_target = 1000 # Yearly target for running in km

        # Load data and initialize layers
        data_handler = DataHandler(config)
        (config.dawn_data, config.weather_data,
         config.city_data, config.sun_data) = data_handler.load_data()
        
        # Set wallpaper specific config
        wallpaper_config = WallpaperConfig()
        wallpaper_config.width = 1920  # For Full HD
        wallpaper_config.height = 1080
        # Or for 4K:
        # wallpaper_config.width = 3840
        # wallpaper_config.height = 2160
        
        # Set the calendar position that worked well
        wallpaper_config.calendar_position = {
            "left": -0.3,
            "bottom": -1.2,
            "width": 1.02,
            "height": 2.3
        }
        
        config.wallpaper = wallpaper_config

        # Create and combine layers
        plotter = WallpaperCalendarPlotter(config)
        plotter.create_plot(layers=[
            DawnLayer(config),
            TemperatureLayer(config),
            StravaLayer(config)
        ])

    except ConfigurationError as e:
        print(f"Configuration error: {str(e)}")
        exit(1)
    except Exception as e:
        print(f"Error: {type(e).__name__} - {str(e)}\n\n{''.join(traceback.format_tb(e.__traceback__))}")
        exit(1)


if __name__ == "__main__":
    main() 