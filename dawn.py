import sys
import traceback

from components.config import ConfigurationError, load_config
from components.data_handler import DataHandler
from components.base_calendar_plotter import BaseCalendarPlotter

from components.layer_dawn import DawnLayer
from components.layer_temperature import TemperatureLayer
from components.layer_precipitation import PrecipitationLayer


def main():

    try:
        city_name = sys.argv[1] if len(sys.argv) > 1 else None
        config = load_config()

        if city_name:
            config.city_name = city_name

        data_handler = DataHandler(config)

        dawn_data, weather_data, city_data = data_handler.load_data()
        config.city_data = city_data

        # config.temp_offset = 0.062 # 6.2% offset for temperature ring, higher means more inside the circle
        # config.temp_footer_offset = 0.01 # 1% offset for temperature footer

        # config.precip_offset = 0.042 # 4.2% offset for precipitation ring
        # config.precip_footer_offset = 0.04 # 4% offset for precipitation footer

        dawn_layer = DawnLayer(dawn_data, config)
        temperature_layer = TemperatureLayer(weather_data, config)
        precipitation_layer = PrecipitationLayer(weather_data, config)

        plotter = BaseCalendarPlotter(config)
        plotter.create_plot(layers=[dawn_layer, temperature_layer])

    except ConfigurationError as e:
        print(f"Configuration error: {str(e)}")
        exit(1)
    except Exception as e:
        print(f"Error: {type(e).__name__} - {str(e)
                                             }\n\n{''.join(traceback.format_tb(e.__traceback__))}")
        exit(1)


if __name__ == "__main__":
    main()
