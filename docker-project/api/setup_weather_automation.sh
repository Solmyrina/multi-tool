#!/bin/bash
# Setup script for automated weather data collection

# Create cron job for hourly current weather collection
# This script sets up automated collection in the API container

echo "Setting up automated weather data collection..."

# Create log files if they don't exist
touch /app/current_weather.log
touch /app/historic_weather.log

# Add cron job to collect current weather every hour at 5 minutes past the hour
echo "5 * * * * cd /app && python3 collect_current_weather.py >> /app/current_weather.log 2>&1" > /tmp/weather_cron

# Add cron job to run historic weather collection every 6 hours (if needed)
echo "0 */6 * * * cd /app && python3 fetch_historic_weather.py >> /app/historic_weather.log 2>&1" >> /tmp/weather_cron

# Install cron job
crontab /tmp/weather_cron

# Clean up temporary file
rm /tmp/weather_cron

# Enable and start cron service (if not running)
service cron start

echo "Automated weather data collection configured:"
echo "- Current weather: Every hour at 5 minutes past"
echo "- Historic weather: Every 6 hours to fill gaps"
echo "- Logs: /app/current_weather.log and /app/historic_weather.log"

# Run initial historic data collection for all locations that need it
echo "Running initial historic data collection..."
python3 fetch_historic_weather.py >> /app/historic_weather.log 2>&1 &

# Show current cron jobs
echo ""
echo "Current cron jobs:"
crontab -l

echo "Weather automation setup completed!"