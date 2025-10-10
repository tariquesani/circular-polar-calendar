"""Calendar Builder Service - Bridges web configurations to calendar generation."""

import os
import sys
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add parent directory to path to import components
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from components.config import load_config, ConfigurationError
from components.data_handler import DataHandler
from components.base_calendar_plotter import BaseCalendarPlotter
from components.wallpaper_calendar_plotter import WallpaperCalendarPlotter
from components.data_types import Config
from .layer_registry import LayerRegistry


class CalendarBuilderError(Exception):
    """Custom exception for calendar builder errors."""
    pass


class CalendarBuilder:
    """Main service for building calendars from web configurations."""
    
    def __init__(self, output_dir: str = "web/generated"):
        """
        Initialize the calendar builder.
        
        Args:
            output_dir: Directory to store generated calendar files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.layer_registry = LayerRegistry()
        
        # Default colors from config.yaml
        self.default_colors = {
            "night": "#011F26",
            "daylight": "#fbba43", 
            "astro": "#092A38",
            "nautical": "#0A3F4D",
            "civil": "#1C5C7C",
            "background": "#faf0e6",
            "divider": "#02735E",
            "dial": "#FFFFFF",
            "time_label": "#e7fdeb",
            "month_label": "#2F4F4F",
            "sunday_label": "#696969",
            "title_text": "#000000",
            "temperature": "YlOrRd",
            "precipitation": "Blues"
        }
    
    def parse_web_config(self, web_config: Dict[str, Any]) -> Config:
        """
        Convert web configuration to internal Config object.
        
        Args:
            web_config: Configuration from web frontend
            
        Returns:
            Config object for calendar generation
            
        Raises:
            CalendarBuilderError: If configuration is invalid
        """
        try:
            # Validate required fields
            required_fields = ['city_name']
            missing_fields = [field for field in required_fields if field not in web_config]
            if missing_fields:
                raise CalendarBuilderError(f"Missing required fields: {', '.join(missing_fields)}")
            
            # Build colors dict
            colors = self.default_colors.copy()
            if 'colors' in web_config:
                colors.update(web_config['colors'])
            
            # Create config object
            config = Config(
                city_name=web_config['city_name'],
                year=web_config.get('year', 2025),
                colors=colors,
                smoothen=web_config.get('smoothen', False),
                interval=web_config.get('interval', 0.25)
            )
            
            # Add any additional attributes
            for key, value in web_config.items():
                if key not in ['city_name', 'year', 'colors', 'smoothen', 'interval']:
                    setattr(config, key, value)
            
            return config
            
        except Exception as e:
            raise CalendarBuilderError(f"Failed to parse configuration: {str(e)}")
    
    def validate_config(self, web_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate web configuration before generation.
        
        Args:
            web_config: Configuration to validate
            
        Returns:
            Validation result with 'valid' boolean and 'errors' list
        """
        errors = []
        warnings = []
        
        try:
            # Check required fields
            if 'city_name' not in web_config:
                errors.append("City name is required")
            
            if 'layers' not in web_config or not web_config['layers']:
                errors.append("At least one layer must be selected")
            
            city_name = web_config.get('city_name')
            if city_name:
                # Check if data file exists (use absolute path)
                data_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', f"{city_name}_data.json")
                data_file = os.path.abspath(data_file)
                if not os.path.exists(data_file):
                    errors.append(f"Data file not found for {city_name}")
                else:
                    # Validate layers
                    layers = web_config.get('layers', [])
                    for layer in layers:
                        if isinstance(layer, dict):
                            layer_id = layer.get('type', layer.get('id', layer))
                        else:
                            layer_id = layer
                        
                        validation = self.layer_registry.validate_layer_compatibility(layer_id, city_name)
                        if not validation['valid']:
                            errors.extend(validation['errors'])
            
            # Validate year
            year = web_config.get('year', 2025)
            if not isinstance(year, int) or year < 1900 or year > 2100:
                errors.append("Year must be between 1900 and 2100")
            
            # Validate colors
            if 'colors' in web_config:
                colors = web_config['colors']
                if not isinstance(colors, dict):
                    errors.append("Colors must be a dictionary")
                else:
                    for color_name, color_value in colors.items():
                        if not self._is_valid_color(color_value):
                            errors.append(f"Invalid color '{color_value}' for {color_name}")
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings
            }
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"Validation error: {str(e)}"],
                'warnings': []
            }
    
    def _is_valid_color(self, color: str) -> bool:
        """Check if color string is valid hex color."""
        if not isinstance(color, str):
            return False
        
        # Check for matplotlib colormap names
        valid_colormaps = [
            'YlOrRd', 'Blues', 'Greens', 'Reds', 'Purples', 'Oranges',
            'coolwarm', 'viridis', 'plasma', 'inferno', 'magma', 'Greys'
        ]
        if color in valid_colormaps:
            return True
        
        # Check hex color format
        if color.startswith('#') and len(color) == 7:
            try:
                int(color[1:], 16)
                return True
            except ValueError:
                return False
        
        return False
    
    def build_calendar(self, web_config: Dict[str, Any], preview_mode: bool = False) -> Dict[str, Any]:
        """
        Build calendar from web configuration.
        
        Args:
            web_config: Configuration from web frontend
            preview_mode: If True, generate smaller preview version
            
        Returns:
            Dict with success status, file paths, and any errors
        """
        try:
            # Validate configuration first
            validation = self.validate_config(web_config)
            if not validation['valid']:
                return {
                    'success': False,
                    'error': 'Configuration validation failed',
                    'errors': validation['errors']
                }
            
            # Parse configuration
            config = self.parse_web_config(web_config)
            
            # Change to project root directory for the entire generation process
            original_cwd = os.getcwd()
            project_root = os.path.join(os.path.dirname(__file__), '..', '..')
            project_root = os.path.abspath(project_root)
            
            try:
                os.chdir(project_root)
                
                # Load data
                data_handler = DataHandler(config)
                config.dawn_data, config.weather_data, config.city_data, config.sun_data = data_handler.load_data()
                
                # Create layers
                layers = []
                layer_configs = web_config.get('layers', [])
                
                for layer_config in layer_configs:
                    if isinstance(layer_config, dict):
                        layer_id = layer_config.get('type', layer_config.get('id'))
                        layer_settings = layer_config
                    else:
                        layer_id = layer_config
                        layer_settings = {}
                    
                    # Get layer class
                    layer_class = self.layer_registry.get_layer_class(layer_id)
                    
                    # Create layer instance
                    layer = layer_class(config)
                    
                    # Apply layer-specific settings
                    for key, value in layer_settings.items():
                        if key not in ['type', 'id']:
                            setattr(layer, key, value)
                    
                    layers.append(layer)
                
                # Generate unique filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_name = f"{config.city_name}_{timestamp}"
                
                # Determine plotter class
                format_type = web_config.get('format_type', 'calendar')
                if format_type == 'wallpaper':
                    plotter_class = WallpaperCalendarPlotter
                    # Add wallpaper-specific config
                    config.wallpaper = self._create_wallpaper_config(web_config.get('wallpaper', {}))
                else:
                    plotter_class = BaseCalendarPlotter
                
                # Create plotter
                plotter = plotter_class(config, layers)
                
                # Store the figure before create_plot closes it
                fig, ax = plotter.setup_plot()
                plotter.fig = fig
                plotter.ax = ax
                
                # Generate files
                if preview_mode:
                    return self._generate_preview(plotter, base_name, layers)
                else:
                    return self._generate_full_calendar(plotter, base_name, layers)
                    
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Calendar generation failed: {str(e)}'
                }
            finally:
                # Always restore original working directory
                os.chdir(original_cwd)
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Calendar generation failed: {str(e)}'
            }
    
    def _create_wallpaper_config(self, wallpaper_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Create wallpaper configuration from settings."""
        resolution = wallpaper_settings.get('resolution', 'hd')
        
        # Resolution presets
        resolutions = {
            'hd': {'width': 1920, 'height': 1080},
            '4k': {'width': 3840, 'height': 2160},
            'custom': wallpaper_settings.get('custom_resolution', {'width': 1920, 'height': 1080})
        }
        
        dimensions = resolutions.get(resolution, resolutions['hd'])
        
        # Calendar position (default: centered)
        position = wallpaper_settings.get('position', {
            'left': 0.1,
            'bottom': 0.1,
            'width': 0.8,
            'height': 0.8
        })
        
        return {
            'width': dimensions['width'],
            'height': dimensions['height'],
            'calendar_position': position,
            'dark_mode': wallpaper_settings.get('dark_mode', False)
        }
    
    def _create_calendar_plot(self, plotter: BaseCalendarPlotter, layers: List):
        """Create the calendar plot manually without saving to files."""
        # Get layers
        plotter.layers = layers

        if getattr(plotter.config, "use_sunday_layer", True):
            from components.layer_sunday import SundayLayer
            plotter.layers.append(SundayLayer(plotter.config))

        if getattr(plotter.config, "use_months_layer", True):
            from components.layer_months import MonthsLayer
            plotter.layers.append(MonthsLayer(plotter.config))

        if getattr(plotter.config, "use_time_layer", True):
            from components.layer_time import TimeLayer
            plotter.layers.append(TimeLayer(plotter.config))

        # Plot layers
        for layer in plotter.layers:
            layer.plot(plotter.ax, plotter)

        # Add title
        plotter.add_title(plotter.ax)

        # Add footer
        plotter.add_footer(plotter.fig)

        # Adjust layout
        import matplotlib.pyplot as plt
        plt.subplots_adjust(top=0.95, bottom=0.3)
    
    def _generate_preview(self, plotter: BaseCalendarPlotter, base_name: str, layers: List) -> Dict[str, Any]:
        """Generate preview version of calendar."""
        try:
            # Create smaller preview
            preview_name = f"{base_name}_preview"
            png_path = self.output_dir / f"{preview_name}.png"
            
            # Generate the plot manually
            self._create_calendar_plot(plotter, layers)
            
            # Save preview
            plotter.fig.savefig(png_path, dpi=72, bbox_inches='tight', facecolor=plotter.config.colors['background'])
            import matplotlib.pyplot as plt
            plt.close(plotter.fig)
            
            return {
                'success': True,
                'preview_url': f"/api/calendar/files/{preview_name}.png",
                'preview_path': str(png_path)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Preview generation failed: {str(e)}'
            }
    
    def _generate_full_calendar(self, plotter: BaseCalendarPlotter, base_name: str, layers: List) -> Dict[str, Any]:
        """Generate full resolution calendar files."""
        try:
            png_path = self.output_dir / f"{base_name}.png"
            pdf_path = self.output_dir / f"{base_name}.pdf"
            
            # Generate the plot manually
            self._create_calendar_plot(plotter, layers)
            
            # Save PNG
            plotter.fig.savefig(png_path, dpi=300, bbox_inches='tight', facecolor=plotter.config.colors['background'])
            
            # Save PDF
            plotter.fig.savefig(pdf_path, bbox_inches='tight', facecolor=plotter.config.colors['background'])
            
            import matplotlib.pyplot as plt
            plt.close(plotter.fig)
            
            return {
                'success': True,
                'png_url': f"/api/calendar/files/{base_name}.png",
                'pdf_url': f"/api/calendar/files/{base_name}.pdf",
                'png_path': str(png_path),
                'pdf_path': str(pdf_path),
                'filename': base_name
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Calendar generation failed: {str(e)}'
            }
    
    def get_available_layers(self) -> List[Dict[str, Any]]:
        """Get list of all available layers."""
        return self.layer_registry.list_layers()
    
    def get_available_cities(self) -> List[Dict[str, Any]]:
        """Get list of cities with available data."""
        cities = []
        data_dir = Path(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))
        
        if data_dir.exists():
            for file_path in data_dir.glob("*_data.json"):
                city_name = file_path.stem.replace("_data", "")
                
                # Check what data is available
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    cities.append({
                        'name': city_name,
                        'has_weather': 'temperature' in data and 'precipitation' in data,
                        'has_sun': 'sunrise' in data and 'sunset' in data,
                        'has_civil': 'civil' in data,
                        'has_nautical': 'nautical' in data,
                        'has_astro': 'astro' in data,
                        'year': data.get('year', 2025)
                    })
                except Exception:
                    # Skip corrupted files
                    continue
        
        return sorted(cities, key=lambda x: x['name'])
    
    def cleanup_old_files(self, max_age_days: int = 7):
        """Clean up old generated files."""
        try:
            cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)
            
            for file_path in self.output_dir.glob("*"):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    
        except Exception as e:
            print(f"Warning: Failed to cleanup old files: {str(e)}")


# Initialize global instance
calendar_builder = CalendarBuilder()
