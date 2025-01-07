from components.base_calendar_plotter import BaseCalendarPlotter
from components.layer import Layer
import numpy as np
import matplotlib.pyplot as plt


class PrecipitationLayer(Layer):
    def __init__(self, weather_data, config):
        self.weather_data = weather_data
        self.config = config

        # Set a default value for precip_offset and precip_footer_offset
        self.config.precip_offset = getattr(self.config, 'precip_offset', 0.042)
        self.config.precip_footer_offset = getattr(self.config, 'precip_footer_offset', 0.04)
        
        # Add precipitation plotting parameters
        self.n_r = 20  # Number of radial points for smoothness

    @property
    def start_time(self):
        """Precipitation layer doesn't affect the time range, so return None."""
        return None

    @property
    def end_time(self):
        """Precipitation layer doesn't affect the time range, so return None."""
        return None

    def plot(self, ax: plt.Axes, base: BaseCalendarPlotter):
        """Plot precipitation data as a circular band."""
        if not hasattr(self.weather_data, 'precipitation') or not self.weather_data.precipitation:
            print("No precipitation data available")
            return  # Skip if no precipitation data available

        # Create coordinate system for precipitation band
        theta = np.linspace(0, 2*np.pi, base.num_points)

        # Scale the precipitation band to fit within the plot's y-limits
        r_min = base.start_time/24
        r_max = base.end_time/24

        # Calculate relative offsets based on time range
        time_range = base.end_time - base.start_time
        precip_offset = time_range/24 * self.config.precip_offset  # Adjust percentage as needed
        band_width = time_range/24 * 0.02   # Adjust percentage as needed
        r_mid = r_max - precip_offset  # Dynamic midpoint based on time range

        r_precip_grid = np.linspace(
            r_mid - band_width/2,  # Start band below middle
            r_mid + band_width/2,  # End band above middle
            self.n_r
        )

        # Handle mismatched data lengths (leap year case)
        precip_data = np.array(self.weather_data.precipitation)
        if len(precip_data) != base.num_points:
            print(f"Warning: precipitation data length ({
                  len(precip_data)}) differs from expected length ({base.num_points})")
            if len(precip_data) > base.num_points:
                # Truncate extra data
                precip_data = precip_data[:base.num_points]
            else:
                # Pad with nearest neighbor
                padding = base.num_points - len(precip_data)
                precip_data = np.pad(precip_data, (0, padding), mode='edge')

        # Store original precipitation data for colorbar
        base.precip_min = np.min(precip_data)
        base.precip_max = np.max(precip_data)

        # Create 2D arrays for coloring
        precip_colors = np.tile(precip_data, (self.n_r, 1))

        # Create meshgrid for plotting
        THETA, R_TEMP = np.meshgrid(theta, r_precip_grid)

        # Plot precipitation band
        norm = plt.Normalize(base.precip_min, base.precip_max)
        self.precip_plot = ax.pcolormesh(
            THETA,
            R_TEMP,
            precip_colors,
            cmap=base.colors['precipitation'],  # See config.yaml for colors
            norm=norm,  # Use the same normalization for consistent coloring
            shading='gouraud',  # Smooth color interpolation
            # alpha=0.9,  # Slight transparency
            zorder=9  # Place in front of other elements
        )

    def footer(self, fig, footer_dimensions, base: BaseCalendarPlotter):
        """Add a footer with legend explaining different precipitation scales."""
        colorbar_height = 0.005  # Reduced height for the colorbar
        # Move colorbar up
        colorbar_bottom = footer_dimensions['bottom'] + self.config.precip_footer_offset
        colorbar_ax = fig.add_axes([footer_dimensions['left'] + 0.2, colorbar_bottom,
                                    footer_dimensions['width'] - 0.4, colorbar_height])
        colorbar = plt.colorbar(self.precip_plot, cax=colorbar_ax,
                                orientation='horizontal')

        # Remove outline and ticks
        colorbar.outline.set_visible(False)
        colorbar.ax.tick_params(size=0)

        # Add precipitation label above the colorbar
        colorbar_ax.text(0.5, 1.5, 'Average precipitation (mm)',
                         ha='center', va='bottom',
                         transform=colorbar_ax.transAxes,
                         color=self.config.colors['title_text'],
                         fontsize=8)

        # Set custom ticks to show min, middle, and max temperatures
        ticks = np.linspace(base.precip_min, base.precip_max, 5)
        colorbar.set_ticks(ticks)
        colorbar.set_ticklabels([f'{t:.1f}mm' for t in ticks])

        colorbar.ax.tick_params(labelsize=6)  # Adjust tick label size
        for label in colorbar.ax.get_xticklabels():
            label.set_alpha(0.5)  # Add transparency
            # Match color with other text
            label.set_color(self.config.colors['title_text'])
