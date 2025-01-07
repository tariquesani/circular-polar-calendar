from components.base_calendar_plotter import BaseCalendarPlotter
from components.layer import Layer
import numpy as np
import matplotlib.pyplot as plt


class TemperatureLayer(Layer):
    def __init__(self, weather_data, config):
        self.weather_data = weather_data
        self.config = config

        # Set a default value for temp_offset and temp_footer_offset
        self.config.temp_offset = getattr(self.config, 'temp_offset', 0.042)
        self.config.temp_footer_offset = getattr(self.config, 'temp_footer_offset', 0.04)

        # Add temperature plotting parameters
        self.n_r = 20  # Number of radial points for smoothness
        

    @property
    def start_time(self):
        """Temperature layer doesn't affect the time range, so return None."""
        return None

    @property
    def end_time(self):
        """Temperature layer doesn't affect the time range, so return None."""
        return None

    def plot(self, ax: plt.Axes, base: BaseCalendarPlotter):
        """Plot temperature data as a circular band."""
        if not hasattr(self.weather_data, 'temperature') or not self.weather_data.temperature:
            print("No temperature data available")
            return  # Skip if no temperature data available

        # Create coordinate system for temperature band
        theta = np.linspace(0, 2*np.pi, base.num_points)

        # Scale the temperature band to fit within the plot's y-limits
        r_min = base.start_time/24
        r_max = base.end_time/24

        # Calculate relative offsets based on time range
        time_range = base.end_time - base.start_time
        temp_offset = time_range/24 * self.config.temp_offset  # Adjust percentage as needed
        band_width = time_range/24 * 0.02   # Adjust percentage as needed
        r_mid = r_max - temp_offset  # Dynamic midpoint based on time range

        r_temp_grid = np.linspace(
            r_mid - band_width/2,  # Start band below middle
            r_mid + band_width/2,  # End band above middle
            self.n_r
        )

        # Handle mismatched data lengths (leap year case)
        temp_data = np.array(self.weather_data.temperature)
        if len(temp_data) != base.num_points:
            print(f"Warning: Temperature data length ({
                  len(temp_data)}) differs from expected length ({base.num_points})")
            if len(temp_data) > base.num_points:
                # Truncate extra data
                temp_data = temp_data[:base.num_points]
            else:
                # Pad with nearest neighbor
                padding = base.num_points - len(temp_data)
                temp_data = np.pad(temp_data, (0, padding), mode='edge')

        # Store original temperature data for colorbar
        base.temp_min = np.min(temp_data)
        base.temp_max = np.max(temp_data)

        # Create 2D arrays for coloring
        temp_colors = np.tile(temp_data, (self.n_r, 1))

        # Create meshgrid for plotting
        THETA, R_TEMP = np.meshgrid(theta, r_temp_grid)

        # Plot temperature band
        norm = plt.Normalize(base.temp_min, base.temp_max)
        self.temp_plot = ax.pcolormesh(
            THETA,
            R_TEMP,
            temp_colors,
            cmap=base.colors['temperature'],  # See config.yaml for colors
            norm=norm,  # Use the same normalization for consistent coloring
            shading='gouraud',  # Smooth color interpolation
            # alpha=0.9,  # Slight transparency
            zorder=9  # Place in front of other elements
        )

    def footer(self, fig, footer_dimensions, base: BaseCalendarPlotter):
        """Add a footer with legend explaining different temperature scales."""

        colorbar_height = 0.005  # Reduced height for the colorbar
        # Move colorbar up
        colorbar_bottom = footer_dimensions['bottom'] + self.config.temp_footer_offset
        colorbar_ax = fig.add_axes([footer_dimensions['left'] + 0.2, colorbar_bottom,
                                    footer_dimensions['width'] - 0.4, colorbar_height])
        colorbar = plt.colorbar(self.temp_plot, cax=colorbar_ax,
                                orientation='horizontal', spacing='proportional') 

        # Remove outline and ticks
        colorbar.outline.set_visible(False)
        colorbar.ax.tick_params(size=0)

        # Add temperature label above the colorbar
        colorbar_ax.text(0.5, 1.5, 'Average temperature (°C)',
                         ha='center', va='bottom',
                         transform=colorbar_ax.transAxes,
                         color=self.config.colors['title_text'],
                         fontsize=8)

        # Set custom ticks to show min, middle, and max temperatures
        ticks = np.linspace(base.temp_min, base.temp_max, 5)
        colorbar.set_ticks(ticks)
        colorbar.set_ticklabels([f'{t:.1f}°C' for t in ticks])

        colorbar.ax.tick_params(labelsize=6)  # Adjust tick label size
        for label in colorbar.ax.get_xticklabels():
            label.set_alpha(0.5)  # Add transparency
            # Match color with other text
            label.set_color(self.config.colors['title_text'])
