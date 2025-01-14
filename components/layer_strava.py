import json
import numpy as np
from datetime import datetime, date
from components.layer import Layer

class StravaLayer(Layer):
    def __init__(self, config):
        self.config = config
        self.run_data = []
    
    @property
    def start_time(self): return None
    
    @property
    def end_time(self): return None
    
    def load_data(self):
        """Load and process run/walk activities from Strava data file"""
        with open("data/strava_activities.json", "r") as f:
            activities = json.load(f)

        print(f"Loaded {len(activities)} activities from Strava.")
        
        for activity in activities:
            if activity["type"] not in {"Run", "Walk"}:
                continue
                
            activity_date = datetime.fromisoformat(activity["start_date"]).date()
            
            try:
                projected_date = activity_date.replace(year=self.config.year)
            except ValueError:
                print(f"Skipping invalid date in Strava data: {activity_date}")
                continue
                
            day_of_year = (projected_date - date(self.config.year, 1, 1)).days + 1
            start_datetime = datetime.fromisoformat(activity["start_date"])
            
            self.run_data.append({
                "date": activity_date.isoformat(),
                "day_of_year": day_of_year,
                "start_time": start_datetime.hour + start_datetime.minute / 60,
                "distance": activity["distance"] / 1000,  # Convert to km
                "type": activity["type"],
                "elapsed_time": activity["elapsed_time"],
                "year": activity_date.year,
                "alpha": 0.25 if activity_date.year < self.config.year else 1.0
            })

    def plot(self, ax, base):
        """Plot activities and progress visualization"""
        self.load_data()
        if not self.run_data:
            print("No data to plot in StravaLayer.")
            return

        # Calculate scale factors
        time_range = base.end_time - base.start_time
        activity_scale = (time_range / 100) / 24  # 1km = 1% of time range
        radial_range = (base.end_time - base.start_time) / 24
        km_to_radial = (radial_range * 0.9) / 1000 # Cover 90% of radial range

        # Plot individual activities
        self.run_data.sort(key=lambda x: x["day_of_year"])
        for activity in self.run_data:
            theta = activity["day_of_year"] / base.num_points * 2 * np.pi
            r_start = activity["start_time"] / 24
            r_end = r_start + activity["distance"] * activity_scale
            
            ax.plot([theta, theta], [r_start, r_end],
                   color="red" if activity["type"] == "Run" else "blue",
                   alpha=activity["alpha"], zorder=20)

        # Plot yearly cumulative distances
        for year in sorted(set(a["year"] for a in self.run_data)):
            cumulative = 0
            theta_points, r_points = [], []
            
            for activity in filter(lambda x: x["year"] == year, self.run_data):
                cumulative += activity["distance"]
                theta_points.append(activity["day_of_year"] / base.num_points * 2 * np.pi)
                r_points.append(base.start_time / 24 + cumulative * km_to_radial)
            
            ax.plot(theta_points, r_points, color="green", lw=.5,
                   alpha=0.25 if year < self.config.year else 1.0, zorder=15)

        # Plot target line for 1000km goal
        daily_target = self.config.running_target / base.num_points
        target_points = [(day / base.num_points * 2 * np.pi,
                         base.start_time / 24 + (day * daily_target) * km_to_radial)
                        for day in range(1, base.num_points + 1)]
        
        ax.plot(*zip(*target_points), color="gray", lw=1,
               linestyle="--", alpha=0.25, zorder=10)

    def footer(self, fig, dims, base):
        """Create footer with activity legends and stats."""
        ax = fig.add_axes([
            dims['left'],
            dims['bottom'] + getattr(self.config, 'strava_footer_offset', 0),
            dims['width'],
            getattr(self.config, 'strava_footer_height', 0.1)
        ])
        
        ax.set_aspect('equal', adjustable='box')
        ax.axis('off')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 0.2)

        legend_items = [
            ('Run', 'red', 'Individual runs'),
            ('Walk', 'blue', 'Individual walks'),
            ('Progress', 'green', 'Cumulative distance'),
            ('Target', 'gray', f'{self.config.running_target}km yearly goal')
        ]

        for x, (label, color, desc) in zip(np.linspace(0.1, 0.9, len(legend_items)), legend_items):
            ax.plot([x - 0.02, x + 0.02], [0.15, 0.15], 
                    color=color, 
                    linestyle='--' if label == 'Target' else '-',
                    alpha=0.25 if label == 'Target' else 1.0,
                    linewidth=1)
            
            ax.text(x, 0.125, label, ha='center', va='center',
                color=self.config.colors['title_text'],
                fontsize=8, alpha=0.7, fontweight='normal')
            
            ax.text(x, 0.1, desc, ha='center', va='center',
                color=self.config.colors['title_text'],
                fontsize=6, alpha=0.5)