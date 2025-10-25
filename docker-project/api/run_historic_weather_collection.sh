#!/bin/bash

# Historic Weather Data Collection Script
# This script runs the historic weather data fetcher

echo "Starting historic weather data collection..."
echo "This may take several minutes depending on the number of favorite locations."
echo ""

# Run the Python script
cd /app && python3 fetch_historic_weather.py

echo ""
echo "Historic weather data collection completed."
echo "Check the logs for detailed information: /app/historic_weather.log"