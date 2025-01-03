from typing import Dict
import yaml
from components.data_types import Config

class ConfigurationError(Exception):
    """Custom exception for configuration errors."""
    pass


def load_config(config_path: str = "config.yaml") -> Config:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        # Validate required fields
        required_fields = ['city_name', 'colors']
        missing_fields = [field for field in required_fields if field not in config_data]
        if missing_fields:
            raise ConfigurationError(f"Missing required fields: {', '.join(missing_fields)}")

        return Config(**config_data)

    except FileNotFoundError:
        raise ConfigurationError(f"Configuration file not found: {config_path}")
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Error parsing YAML configuration: {str(e)}")
    except Exception as e:
        raise ConfigurationError(f"Error creating configuration: {str(e)}")