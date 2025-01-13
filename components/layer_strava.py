import json
import numpy as np
from datetime import datetime, date
from components.layer import Layer

class StravaLayer(Layer):
    def __init__(self, config):
        """
        :param config: Configuration object.
        """
        self.config = config
        self.run_data = []
    @property
    def start_time(self):
        return None
    
    @property
    def end_time(self):
        return None
    
    def load_data(self):
        """Load and filter run and walk data from ../data/strava_activities.json."""
        with open("data/strava_activities.json", "r") as f:
            activities = json.load(f)

        print(f"Loaded {len(activities)} activities from Strava.")

        # Filter activities of type 'Run' or 'Walk' and project dates to base.year
        self.run_data = []
        for activity in activities:
            if activity["type"] in {"Run", "Walk"}:
                activity_date = datetime.fromisoformat(activity["start_date"]).date()
                try:
                    # Safely project the date to the target year
                    projected_date = activity_date.replace(year=self.config.year)
                except ValueError:
                    # Skip February 29 for non-leap years
                    print(f"Skipping invalid date: {activity_date}")
                    continue
                # projected_date = activity_date.replace(year=self.config.year)  # Align to base.year
                day_of_year = (projected_date - date(self.config.year, 1, 1)).days + 1

                self.run_data.append({
                    "date": activity_date.isoformat(),  # Original date
                    "day_of_year": day_of_year,
                    "start_time": datetime.fromisoformat(activity["start_date"]).hour +
                                  datetime.fromisoformat(activity["start_date"]).minute / 60,
                    "distance": activity["distance"] / 1000,  # Convert to kilometers
                    "type": activity["type"],
                    "elapsed_time": activity["elapsed_time"],
                    "year": activity_date.year,  # Include year for grouping
                    "alpha": 0.25 if activity_date.year < self.config.year else 1.0
                })

    def plot(self, ax, base):
        """Plot the run and walk data from Strava layer."""
        self.load_data()

        days_in_year = base.num_points

        if not self.run_data:
            print("No data to plot in StravaLayer.")
            return

        # Sort activities by day of year
        self.run_data.sort(key=lambda x: x["day_of_year"])
        # Calculate scale: 1% of the difference between start_time and end_time equals 1km
        time_range = base.end_time - base.start_time
        scale = (time_range / 100)/24  # 1% of the time range is 1km

        # Plot individual runs or walks        
        for activity in self.run_data:
            theta = activity["day_of_year"] / base.num_points * 2 * np.pi
            r_start = activity["start_time"] / 24
            # r_end = (activity["start_time"] + (activity["elapsed_time"]/3600)) / 24
            r_end = r_start + activity["distance"] * scale  # Scale distance for radial length

            ax.plot(
                [theta, theta],
                [r_start, r_end],
                color="red" if activity["type"] == "Run" else "blue",
                # lw=1,
                # label="Run/Walk" if "Run/Walk" not in ax.get_legend_handles_labels()[1] else None,
                alpha=activity["alpha"],
                zorder=20           
            )

        # Compute scale to map distances into start_time and end_time range
        radial_range = (base.end_time - base.start_time) / 24  # Total radial range
        km_to_radial = (radial_range*0.9) / 1000  # Scale factor to convert km to radial range


        # Plot cumulative distance for each year
        years = sorted(set(activity["year"] for activity in self.run_data))
        for year in years:
            cumulative_distance = 0
            theta_spiral = []
            r_spiral = []

            for activity in filter(lambda x: x["year"] == year, self.run_data):
                theta = activity["day_of_year"] / base.num_points * 2 * np.pi
                cumulative_distance += activity["distance"]
                theta_spiral.append(theta)
                r_spiral.append(base.start_time / 24 + cumulative_distance * km_to_radial)

            ax.plot(
                theta_spiral, r_spiral,
                color="blue", lw=.5,
                alpha=0.25 if year < self.config.year else 1.0,
                # label=f"Cumulative Distance {year}" if year == self.config.year else None,
                zorder=15
            )


        # Plot target spiral for 1000km goal        
        daily_increment = 1000 / days_in_year  # Daily distance to meet 1000km goal
        target_distance = 0
        target_theta = []
        target_r = []

        for day in range(1, days_in_year + 1):
            theta = day / days_in_year * 2 * np.pi
            target_distance += daily_increment
            target_theta.append(theta)
            target_r.append(base.start_time / 24 + target_distance * km_to_radial)

        ax.plot(target_theta, target_r, color="gray", lw=1, linestyle="--", alpha=0.25, zorder=10)

        

    def footer(self, fig, footer_dimensions, base):
        pass