from components.layer import Layer
import numpy as np
import matplotlib.pyplot as plt
from typing import List

class MonthsLayer(Layer):
    def __init__(self, config):
        self.config = config
        self.month_labels = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                           'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
        self.config.months_offset = getattr(self.config, 'months_offset', 0.03)  # Default 3% offset from outer edge

    @property
    def start_time(self):
        return None
    
    @property
    def end_time(self):
        return None

    def plot(self, ax: plt.Axes, base):
        """Add month labels and dividing lines."""
        days_in_month = base.days_in_month
        cumulative_days = np.cumsum(days_in_month)
        month_ticks = [(cumulative_days[i - 1] if i > 0 else 0) + days_in_month[i] / 2
                      for i in range(12)]
        month_ticks_rad = [tick / base.num_points * 2 * np.pi for tick in month_ticks]

        # Add labels and lines
        time_range = base.end_time - base.start_time
        label_height = (base.end_time/24) + (time_range / 24 * self.config.months_offset)  # percentage of the time range
        
        for i, (angle, label) in enumerate(zip(month_ticks_rad, self.month_labels)):
            rotation = (-np.degrees(angle) + 180) % 360 + 90
            adjusted_rotation = rotation + np.degrees(base.theta_offset)
            ax.text(angle, label_height, label, 
                   ha='center', va='center', 
                   rotation=adjusted_rotation,
                   fontsize=22, 
                   color=self.config.colors['month_label'], 
                   fontweight='bold')

            # Add dividing line
            if i < 11:
                line_angle = cumulative_days[i] / base.num_points * 2 * np.pi
            else:
                line_angle = 2 * np.pi
                
            ax.plot([line_angle, line_angle], 
                    [base.start_time/24, base.end_time/24],
                    color=self.config.colors['divider'], 
                    linewidth=0.5, 
                    zorder=10)

    def footer(self, fig: plt.Figure, dims, base):
        pass 