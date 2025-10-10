"""Layer Registry - Maps layer names to layer classes and validates layer compatibility."""

import os
import json
from typing import Dict, List, Optional


class LayerRegistry:
    """Registry for managing available calendar layers and their requirements."""
    
    def __init__(self):
        """Initialize the layer registry with layer definitions."""
        self.layers = {
            'dawn': {
                'class_name': 'DawnLayer',
                'module': 'components.layer_dawn',
                'name': 'Dawn/Twilight',
                'description': 'Shows sunrise and twilight phases (civil, nautical, astronomical)',
                'requires': ['sun_data'],
                'data_keys': ['sunrise', 'civil', 'nautical', 'astro']
            },
            'day': {
                'class_name': 'DayLayer',
                'module': 'components.layer_day',
                'name': 'Day/Night',
                'description': 'Shows daylight and nighttime periods',
                'requires': ['sun_data'],
                'data_keys': ['sunrise', 'sunset']
            },
            'temperature': {
                'class_name': 'TemperatureLayer',
                'module': 'components.layer_temperature',
                'name': 'Temperature',
                'description': 'Displays temperature variations as a colored band',
                'requires': ['weather_data'],
                'data_keys': ['temperature']
            },
            'precipitation': {
                'class_name': 'PrecipitationLayer',
                'module': 'components.layer_precipitation',
                'name': 'Precipitation',
                'description': 'Shows rainfall and precipitation data',
                'requires': ['weather_data'],
                'data_keys': ['precipitation']
            },
            'holidays': {
                'class_name': 'HolidaysLayer',
                'module': 'components.layer_holidays',
                'name': 'Holidays',
                'description': 'Marks holidays and special dates',
                'requires': ['holidays_data'],
                'data_keys': []
            },
            'months': {
                'class_name': 'MonthsLayer',
                'module': 'components.layer_months',
                'name': 'Month Labels',
                'description': 'Displays month names around the calendar',
                'requires': [],
                'data_keys': []
            },
            'time': {
                'class_name': 'TimeLayer',
                'module': 'components.layer_time',
                'name': 'Time Labels',
                'description': 'Shows hour markers and time labels',
                'requires': [],
                'data_keys': []
            },
            'sunday': {
                'class_name': 'SundayLayer',
                'module': 'components.layer_sunday',
                'name': 'Sunday Markers',
                'description': 'Highlights Sundays on the calendar',
                'requires': [],
                'data_keys': []
            },
            'strava': {
                'class_name': 'StravaLayer',
                'module': 'components.layer_strava',
                'name': 'Strava Activities',
                'description': 'Visualizes Strava fitness activities',
                'requires': ['strava_data'],
                'data_keys': []
            },
            'all_dates': {
                'class_name': 'AllDatesLayer',
                'module': 'components.layer_all_dates',
                'name': 'All Dates',
                'description': 'Shows all dates in the year',
                'requires': [],
                'data_keys': []
            }
        }
    
    def get_layer_class(self, layer_id: str):
        """
        Dynamically import and return the layer class.
        
        Args:
            layer_id: The layer identifier (e.g., 'dawn', 'temperature')
            
        Returns:
            The layer class
            
        Raises:
            ValueError: If layer_id is not found
            ImportError: If layer module cannot be imported
        """
        if layer_id not in self.layers:
            raise ValueError(f"Unknown layer: {layer_id}. Available layers: {', '.join(self.layers.keys())}")
        
        layer_info = self.layers[layer_id]
        module_name = layer_info['module']
        class_name = layer_info['class_name']
        
        try:
            module = __import__(module_name, fromlist=[class_name])
            return getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            raise ImportError(f"Could not import {class_name} from {module_name}: {str(e)}")
    
    def get_layer_info(self, layer_id: str) -> Optional[Dict]:
        """Get metadata about a specific layer."""
        return self.layers.get(layer_id)
    
    def list_layers(self) -> List[Dict]:
        """
        List all available layers with their metadata.
        
        Returns:
            List of layer dictionaries with id, name, description, and requirements
        """
        return [
            {
                'id': layer_id,
                'name': info['name'],
                'description': info['description'],
                'requires': info['requires']
            }
            for layer_id, info in self.layers.items()
        ]
    
    def validate_layer_compatibility(self, layer_id: str, city_name: str) -> Dict:
        """
        Check if a layer can be used with the given city's data.
        
        Args:
            layer_id: The layer to validate
            city_name: The city name to check data availability
            
        Returns:
            Dict with 'valid' boolean and 'errors' list
        """
        if layer_id not in self.layers:
            return {
                'valid': False,
                'errors': [f"Unknown layer: {layer_id}"]
            }
        
        layer_info = self.layers[layer_id]
        errors = []
        
        # Check city data file exists (use absolute path)
        data_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', f"{city_name}_data.json")
        data_file = os.path.abspath(data_file)
        if not os.path.exists(data_file) and layer_info['requires']:
            errors.append(f"Data file not found for {city_name}")
            return {'valid': False, 'errors': errors}
        
        # Check specific data keys if data file is required
        if layer_info['data_keys']:
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for key in layer_info['data_keys']:
                    if key not in data:
                        errors.append(f"Missing required data: {key}")
            except (FileNotFoundError, json.JSONDecodeError) as e:
                errors.append(f"Error reading data file: {str(e)}")
        
        # Check for special data requirements
        if 'strava_data' in layer_info['requires']:
            strava_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'strava_activities.json')
            strava_file = os.path.abspath(strava_file)
            if not os.path.exists(strava_file):
                errors.append("Strava activities data not available")
        
        if 'holidays_data' in layer_info['requires']:
            holidays_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'holidays.json')
            holidays_file = os.path.abspath(holidays_file)
            if not os.path.exists(holidays_file):
                errors.append("Holidays data not available")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def get_available_layers_for_city(self, city_name: str) -> List[Dict]:
        """
        Get list of layers that can be used with a specific city.
        
        Args:
            city_name: The city to check
            
        Returns:
            List of available layers with validation status
        """
        available = []
        for layer_id in self.layers:
            validation = self.validate_layer_compatibility(layer_id, city_name)
            layer_info = self.get_layer_info(layer_id)
            
            available.append({
                'id': layer_id,
                'name': layer_info['name'],
                'description': layer_info['description'],
                'available': validation['valid'],
                'errors': validation['errors'] if not validation['valid'] else []
            })
        
        return available

