"""Temperature Layer Component - Visualizes temperature data as a colored band in the circular calendar."""

from components.base_calendar_plotter import BaseCalendarPlotter
from components.layer import Layer
import numpy as np
import matplotlib.pyplot as plt


class TemperatureLayer(Layer):
    """Visualizes temperature data as a colored circular band."""

    def __init__(self, config):
        self.config = config
        self.weather_data = config.weather_data
        
        # Default offsets if not in config
        self.config.temp_offset = getattr(self.config, 'temp_offset', 0.042)
        self.config.temp_footer_offset = getattr(self.config, 'temp_footer_offset', 0.04)
        self.n_r = 20  # Radial points for interpolation

    @property
    def start_time(self): return None

    @property
    def end_time(self): return None

    def plot(self, ax: plt.Axes, base: BaseCalendarPlotter):
        """Plot temperature data as a circular color band."""
        if not hasattr(self.weather_data, 'temperature') or not self.weather_data.temperature:
            print("No temperature data available")
            return

        # Set up coordinates
        theta = np.linspace(0, 2*np.pi, base.num_points)
        time_range = base.end_time - base.start_time
        
        # Calculate band position
        temp_offset = time_range/24 * self.config.temp_offset
        band_width = time_range/24 * 0.02
        r_mid = base.end_time/24 - temp_offset
        r_temp_grid = np.linspace(r_mid - band_width/2, r_mid + band_width/2, self.n_r)

        # Prepare temperature data
        temp_data = np.array(self.weather_data.temperature)
        if len(temp_data) != base.num_points:
            temp_data = self._adjust_data_length(temp_data, base.num_points)

        # Store temperature range
        base.temp_min, base.temp_max = np.min(temp_data), np.max(temp_data)
        
        # Create and plot temperature band
        THETA, R_TEMP = np.meshgrid(theta, r_temp_grid)
        temp_colors = np.tile(temp_data, (self.n_r, 1))
        
        self.temp_plot = ax.pcolormesh(
            THETA, R_TEMP, temp_colors,
            cmap=base.colors['temperature'],
            norm=plt.Normalize(base.temp_min, base.temp_max),
            shading='gouraud',
            zorder=9
        )

    def _adjust_data_length(self, data, target_length):
        """Adjust data length to match target length."""
        if len(data) > target_length:
            return data[:target_length]
        return np.pad(data, (0, target_length - len(data)), mode='edge')

    def footer(self, fig, dims, base: BaseCalendarPlotter):
        """Add temperature scale colorbar to footer."""
        colorbar_ax = fig.add_axes([
            dims['left'] + 0.2,
            dims['bottom'] + self.config.temp_footer_offset,
            dims['width'] - 0.4,
            0.005
        ])

        colorbar = plt.colorbar(self.temp_plot, cax=colorbar_ax,
                              orientation='horizontal', spacing='proportional')
        
        # Style colorbar
        colorbar.outline.set_visible(False)
        colorbar.ax.tick_params(size=0)
        
        # Add title and ticks
        colorbar_ax.text(0.5, 1.5, 'Average temperature (°C)',
                        ha='center', va='bottom',
                        transform=colorbar_ax.transAxes,
                        color=base.colors['title_text'],
                        fontsize=8)

        ticks = np.linspace(base.temp_min, base.temp_max, 5)
        colorbar.set_ticks(ticks)
        colorbar.set_ticklabels([f'{t:.1f}°C' for t in ticks])
        
        # Style tick labels
        colorbar.ax.tick_params(labelsize=6)
        for label in colorbar.ax.get_xticklabels():
            label.set_alpha(0.5)
            label.set_color(base.colors['title_text'])