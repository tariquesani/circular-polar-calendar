import sys

from components.config import ConfigurationError, load_config
from components.base_calendar_plotter import BaseCalendarPlotter


def main():
    import traceback
    try:
        city_name = sys.argv[1] if len(sys.argv) > 1 else None
        config = load_config()

        if city_name:
            config.city_name = city_name

        plotter = BaseCalendarPlotter(config)
        plotter.create_plot()
    except ConfigurationError as e:
        print(f"Configuration error: {str(e)}")
        exit(1)
    except Exception as e:
        print(f"Error: {type(e).__name__} - {str(e)
                                             }\n{''.join(traceback.format_tb(e.__traceback__))}")
        exit(1)


if __name__ == "__main__":
    main()
