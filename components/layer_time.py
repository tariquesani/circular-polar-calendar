from components.layer import Layer
import numpy as np
import matplotlib.pyplot as plt

class TimeLayer(Layer):
    def __init__(self, config):
        self.config = config
        self.hour_labels = None
        self.hour_ticks = None
        # Default to showing labels at 0 degrees only if not specified
        self.label_angles = getattr(self.config, 'time_label_angles', [0])
        # Convert degrees to radians
        self.label_angles_rad = [angle * np.pi / 180 for angle in self.label_angles]

    @property
    def start_time(self):
        return None
    
    @property
    def end_time(self):
        return None

    @staticmethod
    def generate_hour_ticks(start, end, interval=0.25):
        """Generate tick positions for hour markers."""
        def frange(start, stop, step):
            """Generate a range of floating-point numbers."""
            while start < stop:
                yield round(start, 10)  # Avoid floating-point imprecision
                start += step
                
        return [h / 24 for h in frange(start, end, interval)]

    @staticmethod
    def generate_hour_labels(start, end, interval=0.25):
        """Generate labels for hour markers."""
        labels = [' ']  # Start with a blank space
        time = start + interval  # Start from the first quarter past the start time
        while time < end - interval:  # Stop before the end time
            hours = int(time)
            minutes = int((time % 1) * 60)
            am_pm = "AM" if hours < 12 else "PM"
            labels.append(f"{(hours - 1) % 12 + 1}:{minutes:02}{am_pm}")
            time += interval  # Increment by the specified interval in minutes
        return labels

    def plot(self, ax: plt.Axes, base):
        """Add hour labels and tick marks."""
        # Generate labels and ticks if not already generated
        if self.hour_labels is None:
            self.hour_labels = self.generate_hour_labels(
                base.start_time, base.end_time, self.config.interval)
            self.hour_ticks = self.generate_hour_ticks(
                base.start_time, base.end_time, self.config.interval)

        theta = np.linspace(
            0, 2 * np.pi, base.num_points)  # Circular positions

        # Add tick marks around the circle (only once)
        for radius in self.hour_ticks:
            ax.fill_between(theta, radius - 0.0001, radius + 0.0001,
                          color='gray', alpha=0.4, zorder=3, linewidth=0)

        # Add labels at each specified angle
        for angle_rad in self.label_angles_rad:
            for i, label in enumerate(self.hour_labels):
                label = " "+label  # Dirty hack to add some space between axes and labels
                radius = self.hour_ticks[i]  # Distance from the center

                # Convert radians to degrees for label rotation
                angle_deg = np.degrees(angle_rad)

                # Calculate text rotation based on angle position
                # This ensures text is always readable from the outside
                if angle_deg == 90:
                    text_angle = 0  # No rotation
                    ha = 'left'
                    label = " " + label.strip()
                elif angle_deg == 270:
                    text_angle = 0  # No rotation
                    ha = 'right'
                    label = label.strip() + " "
                elif 90 < angle_deg < 270:
                    text_angle = angle_deg + 180
                    ha = 'right'
                    label = label.strip() + " "  # Move spacing to right side
                else:
                    text_angle = angle_deg
                    ha = 'left'
                    label = " " + label.strip()  # Move spacing to left side

                # Add hour label with rotation to align along the radial direction
                ax.text(angle_rad, radius, label,
                       ha=ha, va='center', fontsize=9,
                       color=self.config.colors['time_label'], zorder=10,
                       rotation=text_angle)

    def footer(self, fig: plt.Figure, dims, base):
        pass 