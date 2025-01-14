"""
Day Calendar Plotter
Generates a circular calendar visualization combining dawn/dusk twilight times,
temperature, and precipitation data based on configuration settings.
"""

import sys
import traceback

from components.config import ConfigurationError, load_config
from components.data_handler import DataHandler
from components.base_calendar_plotter import BaseCalendarPlotter
from components.layer_temperature import TemperatureLayer
from components.layer_precipitation import PrecipitationLayer
from components.layer_day import DayLayer


def main():
    """
    Orchestrates calendar plot generation:
    1. Loads config and data
    2. Sets up visualization layers
    3. Generates final plot
    """
    try:
        city_name = sys.argv[1] if len(sys.argv) > 1 else None
        config = load_config()
        if city_name:
            config.city_name = city_name

        # Load data and set configuration
        data_handler = DataHandler(config)
        config.dawn_data, config.weather_data, config.city_data, config.sun_data = data_handler.load_data()
        config.file_name = f"{city_name}_Day"

        # Ring position configuration
        # Example settings shown in comments
        config.temp_offset = 0.062  # Higher means more inside the circle
        config.temp_footer_offset = 0.01
        config.precip_offset = 0.042
        config.precip_footer_offset = 0.04
        # config.use_sunday_layer = False  # Uncomment to disable Sunday layer

        # Create and combine visualization layers
        plotter = BaseCalendarPlotter(config)
        plotter.create_plot(layers=[
            DayLayer(config),
            TemperatureLayer(config),
            PrecipitationLayer(config)
        ])

    except ConfigurationError as e:
        print(f"Configuration error: {str(e)}")
        exit(1)
    except Exception as e:
        print(f"Error: {type(e).__name__} - {str(e)}\n\n{''.join(traceback.format_tb(e.__traceback__))}")
        exit(1)


if __name__ == "__main__":
    main()
