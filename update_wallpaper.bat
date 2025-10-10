@echo off
cd generators
py generator_strava.py
cd ..
py calendar_wallpaper.py Nagpur
start "" "C:\Users\ADMIN\Projects\circular-polar-calendar\png\Nagpur_Wallpaper.png"
py lastruns.py
py next_holiday.py
pause
