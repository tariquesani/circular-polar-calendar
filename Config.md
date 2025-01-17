
# Configuration Options

This document outlines all configurable options in the Calendar Visualization system.

## Core Configuration

### General Settings
- `city_name`: Name of the city to be displayed in the title
- `file_name`: Output file name (defaults to `city_name`)
- `year`: Calendar year (default: 2025)
- `interval`: Time interval for hour labels (default: 0.25 hours = 15 minutes)
- `smoothen`: Enable data smoothing (default: false)
  - Note: Keep false for places with Daylight Saving Time

### Layer Control
Toggle visibility of specific layers:
- `use_sunday_layer`: Show Sunday date labels (default: true)
- `use_months_layer`: Show month labels (default: true)
- `use_time_layer`: Show time labels (default: true)

## Visual Configuration

### Colors
Configure colors in the `colors` dictionary:

```yaml
colors:
  night: "#011F26"
  daylight: "#fbba43"
  astro: "#092A38"
  nautical: "#0A3F4D"
  civil: "#1C5C7C"
  background: "#faf0e6"
  divider: "#02735E"
  dial: "#FFFFFF"
  time_label: "#e7fdeb"
  month_label: "#2F4F4F"
  sunday_label: "#696969"
  title_text: "#000000"
  temperature: "YlOrRd"  # Matplotlib colormap
  precipitation: "Blues"  # Matplotlib colormap
```

### Layer-Specific Settings

#### MonthsLayer
- `months_offset`: Distance of month labels from outer edge (default: 0.03 or 3%)

#### TimeLayer
- `time_label_angles`: List of angles where time labels appear
  ```python
  # Examples:
  time_label_angles = [0]               # Default, labels at top only
  time_label_angles = [0, 180]          # Labels on top and bottom
  time_label_angles = [0, 90, 180, 270] # Labels at all cardinal points
  ```

#### TemperatureLayer
- `temp_offset`: Position of temperature band (default: 0.062)
  - Higher values move the band more inside the circle
- `temp_footer_offset`: Vertical position of temperature footer (default: 0.01)

#### StravaLayer (Fitness Calendar)
- `running_target`: Yearly running goal in kilometers (default: 1000)
- `strava_footer_height`: Height of Strava legend (default: 0.05)
- `strava_footer_offset`: Vertical position of Strava footer (default: -0.015)
  - Positive values move footer up

## Font Configuration

Uses Arvo font (when available) with following sizes:
- City name: Arvo-Bold, 64pt
- Coordinates: Arvo-Regular, 20pt
- Year: Arvo-Regular, 48pt

Falls back to system fonts if Arvo is unavailable.

## Example Configuration

```yaml
# config.yaml
city_name: "Nagpur"
smoothen: true
interval: 0.25

colors:
  night: "#011F26"
  daylight: "#fbba43"
  # ... other colors ...

# Layer-specific settings
months_offset: 0.03
time_label_angles: [0, 180]
temp_offset: 0.062
running_target: 1000
```

## Notes

- Some settings may have interdependencies
- Color values must be valid hex codes or matplotlib colormap names
- Offset values are relative to the plot's dimensions
- Font availability depends on system configuration
```
