# Historic Weather Data Collection System

This system collects and stores daily historic weather data from the past 10 years for all favorite weather locations.

## Database Schema

### Tables Created
- `historic_weather_data`: Stores daily weather records
- `historic_weather_collection_log`: Tracks collection progress
- `historic_weather_with_location`: View joining weather data with location details

### Data Fields
- Temperature (min, max, average)
- Humidity average
- Pressure average
- Wind speed (average, maximum)
- Wind direction
- Precipitation total
- Cloud cover average
- Weather symbol/condition
- Data source (open-meteo)

## Scripts

### 1. Main Collection Script
```bash
# Collect 10 years of data for all locations
docker compose exec api python3 collect_historic_weather.py

# Collect specific number of years
docker compose exec api python3 collect_historic_weather.py --years 5

# Process only a specific location
docker compose exec api python3 collect_historic_weather.py --location-id 1

# Dry run to see what would be collected
docker compose exec api python3 collect_historic_weather.py --dry-run
```

### 2. Status Script
```bash
# Check current collection status
docker compose exec api python3 historic_weather_status.py
```

### 3. Test Script (30 days only)
```bash
# Test with just 30 days of recent data
docker compose exec api python3 test_historic_weather.py
```

## Data Source

- **API**: Open-Meteo Historical Weather API (https://open-meteo.com/en/docs/historical-weather-api)
- **Coverage**: Global historic weather data from 1940 onwards
- **Update Frequency**: Daily (API data is available with 2-3 day delay)
- **Rate Limits**: Reasonable limits for academic/personal use

## Features

### Data Integrity
- Duplicate prevention (unique constraint on location+date)
- Incremental collection (only fetches missing data)
- Error handling and logging
- Progress tracking

### Efficient Collection
- Yearly chunks to avoid API limits
- Automatic retry on API failures
- Skips existing data automatically
- Detailed logging for monitoring

### Database Optimization
- Indexed for fast queries by location and date
- Proper foreign key relationships
- Efficient storage with appropriate data types

## Query Examples

```sql
-- Get average temperature by month for a location
SELECT 
    EXTRACT(YEAR FROM date) as year,
    EXTRACT(MONTH FROM date) as month,
    AVG(temperature_avg) as avg_temp
FROM historic_weather_data 
WHERE weather_location_id = 1
GROUP BY year, month
ORDER BY year, month;

-- Find the hottest days ever recorded for each location
SELECT 
    wl.city_name,
    wl.country,
    hwd.date,
    hwd.temperature_max
FROM historic_weather_with_location hwd
JOIN weather_locations wl ON hwd.weather_location_id = wl.id
WHERE hwd.temperature_max = (
    SELECT MAX(temperature_max) 
    FROM historic_weather_data h2 
    WHERE h2.weather_location_id = hwd.weather_location_id
);

-- Monthly precipitation totals
SELECT 
    city_name,
    EXTRACT(YEAR FROM date) as year,
    EXTRACT(MONTH FROM date) as month,
    SUM(precipitation_total) as total_precipitation
FROM historic_weather_with_location
GROUP BY city_name, year, month
ORDER BY city_name, year, month;
```

## Monitoring

The system includes comprehensive logging and status tracking:

- **Collection logs**: Track start/completion times and record counts
- **Error handling**: Detailed error messages and recovery
- **Progress monitoring**: Real-time status of data collection
- **Data validation**: Ensures data quality and completeness

## Usage Notes

1. **Initial Collection**: First run will take considerable time (several hours for 10 years per location)
2. **Incremental Updates**: Subsequent runs are fast, only fetching new data
3. **Safe Re-runs**: Can be run multiple times safely - will not duplicate data
4. **API Limits**: Respects Open-Meteo API rate limits with automatic delays
5. **Storage**: Approximately 3650 records per location per 10 years

## Next Steps

The historic weather data is now ready for:
- Weather trend analysis dashboards
- Climate pattern visualization
- Historical comparisons
- Weather prediction models
- Statistical analysis and reporting