"""
Temperature Layer Component

This module implements a visualization layer for temperature data in a circular calendar plot.
It creates a colored band representing temperature variations throughout the year, with
a corresponding colorbar in the footer for reference.
"""

from components.base_calendar_plotter import BaseCalendarPlotter
from components.layer import Layer
import numpy as np
import matplotlib.pyplot as plt


class TemperatureLayer(Layer):
    """
    A layer class that visualizes temperature data as a colored circular band.
    
    The temperature is represented using a color gradient, with the band's position
    and width being configurable through offset parameters.
    """

    def __init__(self, config):
        """
        Initialize the temperature layer with weather data and configuration.

        Args:
            weather_data: Dataset containing temperature readings
            config: Configuration object with plotting parameters
        """
        self.config = config
        self.weather_data = config.weather_data

        # Set default positioning parameters if not specified in config
        self.config.temp_offset = getattr(self.config, 'temp_offset', 0.042)  # Default 4.2% offset from outer edge
        self.config.temp_footer_offset = getattr(self.config, 'temp_footer_offset', 0.04)  # Default 4% footer offset

        # Control the smoothness of the temperature band
        self.n_r = 20  # Number of radial points for interpolation
        

    @property
    def start_time(self):
        """Temperature layer doesn't affect the time range, so return None."""
        return None

    @property
    def end_time(self):
        """Temperature layer doesn't affect the time range, so return None."""
        return None

    def plot(self, ax: plt.Axes, base: BaseCalendarPlotter):
        """
        Plot temperature data as a circular color band.

        Args:
            ax: Matplotlib axes object to plot on
            base: BaseCalendarPlotter instance providing common plotting utilities

        The band's color represents temperature values, with the color scale
        defined in the configuration. The band's position is determined by
        offset parameters relative to the plot's outer edge.
        """
        # Skip if no temperature data is available
        if not hasattr(self.weather_data, 'temperature') or not self.weather_data.temperature:
            print("No temperature data available")
            return

        # Create angular coordinates for the circular plot
        theta = np.linspace(0, 2*np.pi, base.num_points)

        # Calculate radial positions based on time range
        r_min = base.start_time/24
        r_max = base.end_time/24

        # Calculate band positioning
        time_range = base.end_time - base.start_time
        temp_offset = time_range/24 * self.config.temp_offset  # Convert percentage to absolute offset
        band_width = time_range/24 * 0.02   # Set band width to 2% of time range
        r_mid = r_max - temp_offset  # Position band relative to outer edge

        # Create radial grid for the temperature band
        r_temp_grid = np.linspace(
            r_mid - band_width/2,  # Inner radius
            r_mid + band_width/2,  # Outer radius
            self.n_r
        )

        # Handle data length mismatches (e.g., leap years)
        temp_data = np.array(self.weather_data.temperature)
        if len(temp_data) != base.num_points:
            print(f"Warning: Temperature data length ({len(temp_data)}) differs from expected length ({base.num_points})")
            if len(temp_data) > base.num_points:
                temp_data = temp_data[:base.num_points]  # Truncate extra data
            else:
                padding = base.num_points - len(temp_data)
                temp_data = np.pad(temp_data, (0, padding), mode='edge')  # Pad with last value

        # Store temperature range for colorbar
        base.temp_min = np.min(temp_data)
        base.temp_max = np.max(temp_data)

        # Create 2D temperature array for coloring
        temp_colors = np.tile(temp_data, (self.n_r, 1))

        # Create coordinate meshgrid for plotting
        THETA, R_TEMP = np.meshgrid(theta, r_temp_grid)

        # Plot the temperature band
        norm = plt.Normalize(base.temp_min, base.temp_max)
        self.temp_plot = ax.pcolormesh(
            THETA,
            R_TEMP,
            temp_colors,
            cmap=base.colors['temperature'],  # Color scheme from config
            norm=norm,  # Normalize colors to temperature range
            shading='gouraud',  # Smooth color transitions
            zorder=9  # Layer ordering
        )

    def footer(self, fig, footer_dimensions, base: BaseCalendarPlotter):
        """
        Add a footer with a temperature scale colorbar.

        Args:
            fig: Matplotlib figure object
            footer_dimensions: Dictionary with footer positioning parameters
            base: BaseCalendarPlotter instance providing common plotting utilities
        
        Creates a horizontal colorbar showing the temperature scale with
        custom formatting and positioning.
        """
        # Set up colorbar dimensions
        colorbar_height = 0.005  # Thin colorbar
        colorbar_bottom = footer_dimensions['bottom'] + self.config.temp_footer_offset
        
        # Create colorbar axes
        colorbar_ax = fig.add_axes([
            footer_dimensions['left'] + 0.2,  # Start 20% from left
            colorbar_bottom,
            footer_dimensions['width'] - 0.4,  # 40% total horizontal margins
            colorbar_height
        ])

        # Create and customize colorbar
        colorbar = plt.colorbar(self.temp_plot, cax=colorbar_ax,
                              orientation='horizontal', spacing='proportional')
        
        # Remove unnecessary visual elements
        colorbar.outline.set_visible(False)
        colorbar.ax.tick_params(size=0)

        # Add title above colorbar
        colorbar_ax.text(0.5, 1.5, 'Average temperature (°C)',
                        ha='center', va='bottom',
                        transform=colorbar_ax.transAxes,
                        color=self.config.colors['title_text'],
                        fontsize=8)

        # Configure temperature scale ticks
        ticks = np.linspace(base.temp_min, base.temp_max, 5)  # 5 evenly spaced ticks
        colorbar.set_ticks(ticks)
        colorbar.set_ticklabels([f'{t:.1f}°C' for t in ticks])

        # Style tick labels
        colorbar.ax.tick_params(labelsize=6)  # Small font size
        for label in colorbar.ax.get_xticklabels():
            label.set_alpha(0.5)  # Semi-transparent
            label.set_color(self.config.colors['title_text'])  # Match text color scheme