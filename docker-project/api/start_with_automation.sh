#!/bin/bash
# Startup script for API container with weather automation

echo "Starting API container with weather automation..."

# Start cron service
service cron start

# Set up automated weather data collection
chmod +x /app/setup_weather_automation.sh
/app/setup_weather_automation.sh

# Start API in background
python api.py &

# Keep container running and follow logs
tail -f /app/current_weather.log /app/historic_weather.log 2>/dev/null || tail -f /dev/null