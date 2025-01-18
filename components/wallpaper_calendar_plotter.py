import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy as np
from datetime import datetime
from components.base_calendar_plotter import BaseCalendarPlotter


class WallpaperCalendarPlotter(BaseCalendarPlotter):
    def setup_plot(self):
        """Initialize and configure the plot for wallpaper format."""
        # Get dimensions from wallpaper config
        width = self.config.wallpaper.width
        height = self.config.wallpaper.height
        
        # Calculate figsize based on dpi
        dpi = 96
        figsize = (width/dpi, height/dpi)
        
        # Create figure with exact dimensions
        fig = plt.figure(figsize=figsize, dpi=dpi)
        
        # Set figure background
        fig.patch.set_facecolor(self.config.colors['background'])
        
        # Create axes with specific position and size using calendar_position from config
        pos = self.config.wallpaper.calendar_position
        ax = fig.add_axes([pos['left'], pos['bottom'], 
                          pos['width'], pos['height']], 
                         projection='polar')
        
        # Basic setup
        ax.set_facecolor('none')
        ax.set_theta_direction(-1)
        
        # Calculate rotation for current month
        rotation = self.calculate_rotation_for_current_month()
        ax.set_theta_offset(np.pi/2 - np.radians(rotation))
        
        ax.set_ylim(self.start_time/24, self.end_time/24)
        
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.set_xticks([])
        ax.set_yticks([])
        
        return fig, ax

    def calculate_rotation_for_current_month(self):
        """Calculate rotation needed to put current month at top."""
        current_month = datetime.now().month
        days_before_month = sum(self.days_in_month[:current_month-1])
        angle = (days_before_month / self.config.days_in_year) * 360
        return angle

    def add_title(self, ax: plt.Axes) -> None:
        """Add title to the wallpaper plot."""
        try:
            font_props = {k: FontProperties(fname=f'./fonts/Arvo-{v}.ttf', size=s)
                          for k, v, s in [('bold', 'Bold', 48),
                                        ('regular', 'Regular', 16),
                                        ('year', 'Regular', 36)]}
        except:
            font_props = {k: FontProperties(weight=w, size=s)
                          for k, (w, s) in {'bold': ('bold', 48),
                                          'regular': (None, 16),
                                          'year': (None, 36)}.items()}

        common_props = {
            'ha': 'right',
            'va': 'center',
            'transform': ax.figure.transFigure,
            'color': self.config.colors['title_text']
        }
        
        # Position title elements in top-right area
        ax.text(0.95, 0.9, str(self.year),
                fontproperties=font_props['year'], **common_props)
        ax.text(0.95, 0.85, self.config.city_name,
                fontproperties=font_props['bold'], **common_props)
        ax.text(0.95, 0.8, self.format_coordinates(self.coordinates),
                fontproperties=font_props['regular'], **common_props)

    def add_footer(self, fig: plt.Figure) -> None:
        """Add footers from the layers in vertical layout on right side."""
        # For wallpaper layout, stack footers vertically on the right side
        footer_dimensions = {
            "height": 0.15,      # Height for each footer element
            "width": 0.25,       # Width of the footer area
            "left": 0.7,         # Position from left
            "bottom": 0.2,       # Starting position from bottom
            "vertical_gap": 0.1, # Gap between footer elements
            "is_wallpaper": True # Flag to indicate wallpaper layout
        }

        # Calculate positions for each footer
        num_footers = sum(1 for layer in self.layers if hasattr(layer, "footer"))
        current_bottom = footer_dimensions["bottom"]

        # Ask each layer to render its footer
        for layer in self.layers:
            if hasattr(layer, "footer"):
                # Create dimensions for this specific footer
                this_footer_dims = footer_dimensions.copy()
                this_footer_dims["bottom"] = current_bottom
                
                # Render footer
                layer.footer(fig, this_footer_dims, self)
                
                # Move up for next footer
                current_bottom += footer_dimensions["height"] + footer_dimensions["vertical_gap"]

    def create_plot(self, layers) -> None:
        """Create and save the complete wallpaper plot."""
        self.layers = layers

        if getattr(self.config, "use_sunday_layer", True):
            from components.layer_sunday import SundayLayer
            self.layers.append(SundayLayer(self.config))

        if getattr(self.config, "use_months_layer", True):
            from components.layer_months import MonthsLayer
            self.layers.append(MonthsLayer(self.config))

        if getattr(self.config, "use_time_layer", True):
            from components.layer_time import TimeLayer
            self.layers.append(TimeLayer(self.config))

        fig, ax = self.setup_plot()

        for layer in self.layers:
            layer.plot(ax, self)

        self.add_title(ax)
        # self.add_footer(fig)  # Commented out for cleaner wallpaper layout
        
        # Save with exact dimensions
        plt.savefig(f'./png/{self.config.file_name}.png',
                    dpi=96,
                    bbox_inches=None,  # Don't adjust bounds
                    pad_inches=0,      # No padding
                    facecolor=fig.get_facecolor())
        plt.close() 