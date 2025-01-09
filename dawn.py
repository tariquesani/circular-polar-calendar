"""Dawn Calendar Plotter - Generates a circular calendar visualization combining dawn twilight times and weather data."""

import sys
from components.config import ConfigurationError, load_config
from components.data_handler import DataHandler
from components.base_calendar_plotter import BaseCalendarPlotter
from components.layer_dawn import DawnLayer
from components.layer_temperature import TemperatureLayer

def main():
    try:
        # Setup configuration
        config = load_config()
        config.city_name = sys.argv[1] if len(sys.argv) > 1 else config.city_name
        config.file_name = f"{config.city_name}_Dawn"

        # Load data and initialize layers
        data_handler = DataHandler(config)
        (config.dawn_data, config.weather_data, 
         config.city_data, config.sun_data) = data_handler.load_data()

        # Create and combine layers
        plotter = BaseCalendarPlotter(config)
        plotter.create_plot(layers=[
            DawnLayer(config),
            TemperatureLayer(config)
        ])

    except ConfigurationError as e:
        print(f"Configuration error: {str(e)}")
        exit(1)
    except Exception as e:
        print(f"Error: {type(e).__name__} - {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()