"""
Day Calendar Plotter

This script generates a calendar visualization that combines dawn twilight times, temperature,
and precipitation data. It creates a circular calendar plot with multiple
data layers that can be customized through configuration.

The script can accept a city name as a command line argument, otherwise it uses
the default city from the configuration file.
"""

import sys
import traceback

from components.config import ConfigurationError, load_config
from components.data_handler import DataHandler
from components.base_calendar_plotter import BaseCalendarPlotter

from components.layer_dawn import DawnLayer
from components.layer_temperature import TemperatureLayer
from components.layer_precipitation import PrecipitationLayer
from components.layer_day import DayLayer


def main():
    """
    Main function that orchestrates the calendar plot generation process.

    The function:
    1. Loads configuration (either default or with specified city)
    2. Initializes data handler to load required datasets
    3. Creates visualization layers (dawn times, temperature, and optionally precipitation)
    4. Combines layers into final calendar plot

    Exits with status code 1 if any errors occur during execution.
    """
    try:
        # Get city name from command line args if provided
        city_name = sys.argv[1] if len(sys.argv) > 1 else None
        config = load_config()

        if city_name:
            config.city_name = city_name

        # Initialize data handler and load required datasets
        data_handler = DataHandler(config)
        config.dawn_data, config.weather_data, config.city_data, config.sun_data = data_handler.load_data()

        #File name for your plots
        config.file_name = f"{city_name}_Day"

        # Configuration options for adjusting visualization layout
        # Commented out values show example settings
        # config.temp_offset = 0.062 # 6.2% offset for temperature ring, higher means more inside the circle
        # config.temp_footer_offset = 0.01 # 1% offset for temperature footer

        # config.precip_offset = 0.042 # 4.2% offset for precipitation ring
        # config.precip_footer_offset = 0.04 # 4% offset for precipitation footer

        # Create individual data layers
        # dawn_layer = DawnLayer(config)
        day_layer = DayLayer(config)
        temperature_layer = TemperatureLayer(config)
        # Precipitation layer is currently commented out
        # precipitation_layer = PrecipitationLayer(config)

        # Initialize base plotter and combine layers
        plotter = BaseCalendarPlotter(config)
        plotter.create_plot(layers=[day_layer, temperature_layer])

    except ConfigurationError as e:
        # Handle configuration-specific errors
        print(f"Configuration error: {str(e)}")
        exit(1)
    except Exception as e:
        # Handle any other unexpected errors with full traceback
        print(f"Error: {type(e).__name__} - {str(e)
                                             }\n\n{''.join(traceback.format_tb(e.__traceback__))}")
        exit(1)


if __name__ == "__main__":
    main()
