# Weather Data Collection System

**Complete guide to historic and current weather data collection**

> **Consolidated from**: WEATHER_SYSTEM_README.md, HISTORIC_WEATHER_README.md

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Historic Weather Collection](#historic-weather-collection)
4. [Current Weather Collection](#current-weather-collection)
5. [Database Schema](#database-schema)
6. [API Integration](#api-integration)
7. [Automation Setup](#automation-setup)
8. [Troubleshooting](#troubleshooting)

---

## System Overview

### Purpose

Collect and store comprehensive weather data for analysis:
- **Historic Weather**: Years of past weather data for trends
- **Current Weather**: Real-time conditions updated every 30 minutes
- **Multiple Locations**: 44+ cities across Finland

### Data Sources

- **Historic Data**: Open-Meteo Historical Weather API
- **Current Data**: Open-Meteo Current Weather API
- **Location Data**: Shared locations table

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Weather Collection System                │
└─────────────────────────────────────────────────────────────┘
                              │
                 ┌────────────┴───────────┐
                 │                        │
         ┌───────▼────────┐      ┌───────▼────────┐
         │    Historic    │      │    Current     │
         │    Weather     │      │    Weather     │
         └───────┬────────┘      └───────┬────────┘
                 │                        │
         ┌───────▼────────┐      ┌───────▼────────┐
         │  fetch_historic│      │  collect_current│
         │  _weather.py   │      │  _weather.py    │
         └───────┬────────┘      └───────┬────────┘
                 │                        │
                 └────────────┬───────────┘
                              │
                       ┌──────▼──────┐
                       │ Open-Meteo  │
                       │     API     │
                       └──────┬──────┘
                              │
                       ┌──────▼──────┐
                       │ PostgreSQL  │
                       │  Database   │
                       └─────────────┘
```

### Data Flow

```
1. Cron job triggers collection script
           ↓
2. Load locations from shared table
           ↓
3. For each location:
   a. Build API request
   b. Fetch weather data
   c. Parse JSON response
   d. Insert into database
           ↓
4. Log results and errors
```

---

## Historic Weather Collection

### Overview

Collects years of historical weather data for all locations in a single batch process.

### Script: fetch_historic_weather.py

```python
#!/usr/bin/env python3
"""
Historic Weather Data Collection
Fetches years of historical weather data from Open-Meteo API
"""

import requests
import psycopg2
from datetime import datetime, timedelta
import time
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('historic_weather.log'),
        logging.StreamHandler()
    ]
)

# Database configuration
DB_CONFIG = {
    'host': 'database',
    'port': 5432,
    'database': 'webapp_db',
    'user': 'root',
    'password': 'root'
}

# API configuration
API_BASE_URL = 'https://archive-api.open-meteo.com/v1/archive'

# Date range for historic data
START_DATE = '2020-01-01'
END_DATE = '2024-12-31'

# Weather variables to collect
WEATHER_VARIABLES = [
    'temperature_2m',
    'relative_humidity_2m',
    'precipitation',
    'wind_speed_10m',
    'wind_direction_10m',
    'pressure_msl',
    'cloud_cover'
]

def get_locations():
    """Fetch all locations from shared locations table"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, name, latitude, longitude
            FROM shared_locations
            WHERE is_active = true
            ORDER BY name
        """)
        
        locations = cur.fetchall()
        cur.close()
        conn.close()
        
        logging.info(f"Loaded {len(locations)} locations from database")
        return locations
        
    except Exception as e:
        logging.error(f"Error loading locations: {e}")
        return []

def fetch_historic_weather(location_id, name, latitude, longitude):
    """Fetch historic weather data for a location"""
    logging.info(f"Fetching historic weather for {name}...")
    
    try:
        # Build API request
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'start_date': START_DATE,
            'end_date': END_DATE,
            'hourly': ','.join(WEATHER_VARIABLES),
            'timezone': 'Europe/Helsinki'
        }
        
        # Make API request
        response = requests.get(API_BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Extract hourly data
        hourly = data.get('hourly', {})
        times = hourly.get('time', [])
        
        if not times:
            logging.warning(f"No data returned for {name}")
            return 0
        
        # Insert into database
        records_inserted = insert_weather_data(location_id, hourly)
        
        logging.info(f"✓ {name}: {records_inserted} records inserted")
        return records_inserted
        
    except requests.exceptions.Timeout:
        logging.error(f"Timeout fetching data for {name}")
        return 0
    except requests.exceptions.RequestException as e:
        logging.error(f"API error for {name}: {e}")
        return 0
    except Exception as e:
        logging.error(f"Error processing {name}: {e}")
        return 0

def insert_weather_data(location_id, hourly_data):
    """Insert weather data into database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        times = hourly_data.get('time', [])
        temperatures = hourly_data.get('temperature_2m', [])
        humidity = hourly_data.get('relative_humidity_2m', [])
        precipitation = hourly_data.get('precipitation', [])
        wind_speed = hourly_data.get('wind_speed_10m', [])
        wind_direction = hourly_data.get('wind_direction_10m', [])
        pressure = hourly_data.get('pressure_msl', [])
        cloud_cover = hourly_data.get('cloud_cover', [])
        
        records_inserted = 0
        
        for i in range(len(times)):
            try:
                cur.execute("""
                    INSERT INTO historic_weather (
                        location_id, datetime,
                        temperature, humidity, precipitation,
                        wind_speed, wind_direction,
                        pressure, cloud_cover
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (location_id, datetime) DO NOTHING
                """, (
                    location_id,
                    times[i],
                    temperatures[i] if i < len(temperatures) else None,
                    humidity[i] if i < len(humidity) else None,
                    precipitation[i] if i < len(precipitation) else None,
                    wind_speed[i] if i < len(wind_speed) else None,
                    wind_direction[i] if i < len(wind_direction) else None,
                    pressure[i] if i < len(pressure) else None,
                    cloud_cover[i] if i < len(cloud_cover) else None
                ))
                
                if cur.rowcount > 0:
                    records_inserted += 1
                    
            except Exception as e:
                logging.error(f"Error inserting record {i}: {e}")
                continue
        
        conn.commit()
        cur.close()
        conn.close()
        
        return records_inserted
        
    except Exception as e:
        logging.error(f"Database error: {e}")
        return 0

def main():
    """Main collection process"""
    start_time = time.time()
    logging.info("=" * 60)
    logging.info("Starting historic weather data collection")
    logging.info(f"Date range: {START_DATE} to {END_DATE}")
    logging.info("=" * 60)
    
    # Get locations
    locations = get_locations()
    
    if not locations:
        logging.error("No locations found. Exiting.")
        return
    
    # Collect data for each location
    total_records = 0
    successful = 0
    
    for location_id, name, latitude, longitude in locations:
        records = fetch_historic_weather(location_id, name, latitude, longitude)
        total_records += records
        
        if records > 0:
            successful += 1
        
        # Rate limiting
        time.sleep(1)
    
    # Summary
    elapsed_time = time.time() - start_time
    logging.info("=" * 60)
    logging.info("Historic weather collection complete!")
    logging.info(f"Locations processed: {len(locations)}")
    logging.info(f"Successful: {successful}")
    logging.info(f"Total records: {total_records:,}")
    logging.info(f"Elapsed time: {elapsed_time:.1f} seconds")
    logging.info("=" * 60)

if __name__ == '__main__':
    main()
```

### Running Historic Collection

```bash
# Manual run
docker exec docker-project-api python fetch_historic_weather.py

# Run with shell script
docker exec docker-project-api bash run_historic_weather_collection.sh

# Check logs
docker exec docker-project-api tail -f historic_weather.log
```

### Expected Output

```
2024-10-08 10:00:00 - INFO - ============================================================
2024-10-08 10:00:00 - INFO - Starting historic weather data collection
2024-10-08 10:00:00 - INFO - Date range: 2020-01-01 to 2024-12-31
2024-10-08 10:00:00 - INFO - ============================================================
2024-10-08 10:00:01 - INFO - Loaded 44 locations from database
2024-10-08 10:00:01 - INFO - Fetching historic weather for Helsinki...
2024-10-08 10:00:15 - INFO - ✓ Helsinki: 43,824 records inserted
2024-10-08 10:00:16 - INFO - Fetching historic weather for Espoo...
2024-10-08 10:00:28 - INFO - ✓ Espoo: 43,824 records inserted
...
2024-10-08 10:15:30 - INFO - ============================================================
2024-10-08 10:15:30 - INFO - Historic weather collection complete!
2024-10-08 10:15:30 - INFO - Locations processed: 44
2024-10-08 10:15:30 - INFO - Successful: 44
2024-10-08 10:15:30 - INFO - Total records: 1,928,256
2024-10-08 10:15:30 - INFO - Elapsed time: 930.2 seconds
2024-10-08 10:15:30 - INFO - ============================================================
```

---

## Current Weather Collection

### Overview

Collects real-time weather conditions every 30 minutes via cron automation.

### Script: collect_current_weather.py

```python
#!/usr/bin/env python3
"""
Current Weather Data Collection
Fetches current weather conditions from Open-Meteo API
Runs every 30 minutes via cron
"""

import requests
import psycopg2
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('current_weather.log'),
        logging.StreamHandler()
    ]
)

# Database configuration
DB_CONFIG = {
    'host': 'database',
    'port': 5432,
    'database': 'webapp_db',
    'user': 'root',
    'password': 'root'
}

# API configuration
API_URL = 'https://api.open-meteo.com/v1/forecast'

# Current weather variables
CURRENT_VARIABLES = [
    'temperature_2m',
    'relative_humidity_2m',
    'apparent_temperature',
    'precipitation',
    'rain',
    'snowfall',
    'weather_code',
    'cloud_cover',
    'pressure_msl',
    'wind_speed_10m',
    'wind_direction_10m',
    'wind_gusts_10m'
]

def get_locations():
    """Fetch active locations"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, name, latitude, longitude
            FROM shared_locations
            WHERE is_active = true
            ORDER BY name
        """)
        
        locations = cur.fetchall()
        cur.close()
        conn.close()
        
        return locations
        
    except Exception as e:
        logging.error(f"Error loading locations: {e}")
        return []

def fetch_current_weather(location_id, name, latitude, longitude):
    """Fetch current weather for a location"""
    try:
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'current': ','.join(CURRENT_VARIABLES),
            'timezone': 'Europe/Helsinki'
        }
        
        response = requests.get(API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        current = data.get('current', {})
        
        if not current:
            logging.warning(f"No current data for {name}")
            return False
        
        # Insert into database
        insert_current_weather(location_id, current)
        
        logging.info(f"✓ {name}: Updated current weather")
        return True
        
    except Exception as e:
        logging.error(f"Error fetching weather for {name}: {e}")
        return False

def insert_current_weather(location_id, current_data):
    """Insert current weather into database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO current_weather (
                location_id, datetime,
                temperature, feels_like, humidity,
                precipitation, rain, snowfall,
                weather_code, cloud_cover, pressure,
                wind_speed, wind_direction, wind_gusts
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (location_id) 
            DO UPDATE SET
                datetime = EXCLUDED.datetime,
                temperature = EXCLUDED.temperature,
                feels_like = EXCLUDED.feels_like,
                humidity = EXCLUDED.humidity,
                precipitation = EXCLUDED.precipitation,
                rain = EXCLUDED.rain,
                snowfall = EXCLUDED.snowfall,
                weather_code = EXCLUDED.weather_code,
                cloud_cover = EXCLUDED.cloud_cover,
                pressure = EXCLUDED.pressure,
                wind_speed = EXCLUDED.wind_speed,
                wind_direction = EXCLUDED.wind_direction,
                wind_gusts = EXCLUDED.wind_gusts,
                updated_at = CURRENT_TIMESTAMP
        """, (
            location_id,
            current_data.get('time'),
            current_data.get('temperature_2m'),
            current_data.get('apparent_temperature'),
            current_data.get('relative_humidity_2m'),
            current_data.get('precipitation'),
            current_data.get('rain'),
            current_data.get('snowfall'),
            current_data.get('weather_code'),
            current_data.get('cloud_cover'),
            current_data.get('pressure_msl'),
            current_data.get('wind_speed_10m'),
            current_data.get('wind_direction_10m'),
            current_data.get('wind_gusts_10m')
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        
    except Exception as e:
        logging.error(f"Database error: {e}")

def main():
    """Main collection process"""
    logging.info("Starting current weather collection")
    
    locations = get_locations()
    
    if not locations:
        logging.error("No locations found")
        return
    
    successful = 0
    
    for location_id, name, latitude, longitude in locations:
        if fetch_current_weather(location_id, name, latitude, longitude):
            successful += 1
    
    logging.info(f"Current weather updated: {successful}/{len(locations)} locations")

if __name__ == '__main__':
    main()
```

### Automation Setup

```bash
# Setup script: setup_weather_automation.sh
#!/bin/bash

echo "Setting up weather data collection automation..."

# Add cron job for current weather (every 30 minutes)
(crontab -l 2>/dev/null; echo "*/30 * * * * cd /app && python3 collect_current_weather.py >> /app/current_weather.log 2>&1") | crontab -

echo "✓ Cron job added: Current weather every 30 minutes"

# Initial run
python3 collect_current_weather.py

echo "✓ Automation setup complete!"
```

```bash
# Run setup
docker exec docker-project-api bash setup_weather_automation.sh

# Verify cron job
docker exec docker-project-api crontab -l
```

---

## Database Schema

### Shared Locations Table

```sql
CREATE TABLE shared_locations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    latitude NUMERIC(10, 6) NOT NULL,
    longitude NUMERIC(10, 6) NOT NULL,
    country VARCHAR(50) DEFAULT 'Finland',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, latitude, longitude)
);

CREATE INDEX idx_shared_locations_active ON shared_locations(is_active);
CREATE INDEX idx_shared_locations_coords ON shared_locations(latitude, longitude);
```

### Historic Weather Table

```sql
CREATE TABLE historic_weather (
    id SERIAL PRIMARY KEY,
    location_id INTEGER REFERENCES shared_locations(id),
    datetime TIMESTAMP NOT NULL,
    temperature NUMERIC(5, 2),
    humidity NUMERIC(5, 2),
    precipitation NUMERIC(6, 2),
    wind_speed NUMERIC(5, 2),
    wind_direction NUMERIC(5, 2),
    pressure NUMERIC(7, 2),
    cloud_cover NUMERIC(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(location_id, datetime)
);

CREATE INDEX idx_historic_weather_location_datetime 
    ON historic_weather(location_id, datetime DESC);
CREATE INDEX idx_historic_weather_datetime 
    ON historic_weather(datetime DESC);
```

### Current Weather Table

```sql
CREATE TABLE current_weather (
    id SERIAL PRIMARY KEY,
    location_id INTEGER REFERENCES shared_locations(id) UNIQUE,
    datetime TIMESTAMP NOT NULL,
    temperature NUMERIC(5, 2),
    feels_like NUMERIC(5, 2),
    humidity NUMERIC(5, 2),
    precipitation NUMERIC(6, 2),
    rain NUMERIC(6, 2),
    snowfall NUMERIC(6, 2),
    weather_code INTEGER,
    cloud_cover NUMERIC(5, 2),
    pressure NUMERIC(7, 2),
    wind_speed NUMERIC(5, 2),
    wind_direction NUMERIC(5, 2),
    wind_gusts NUMERIC(5, 2),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_current_weather_location ON current_weather(location_id);
CREATE INDEX idx_current_weather_datetime ON current_weather(datetime DESC);
```

---

## API Integration

### Open-Meteo API

**Free, open-source weather API** with no API key required.

#### Endpoints

- **Historic**: `https://archive-api.open-meteo.com/v1/archive`
- **Current**: `https://api.open-meteo.com/v1/forecast`

#### Rate Limits

- 10,000 requests per day (free tier)
- ~1 second between requests recommended

#### Example Request

```bash
# Historic weather
curl "https://archive-api.open-meteo.com/v1/archive?latitude=60.1695&longitude=24.9354&start_date=2024-01-01&end_date=2024-12-31&hourly=temperature_2m,precipitation&timezone=Europe/Helsinki"

# Current weather
curl "https://api.open-meteo.com/v1/forecast?latitude=60.1695&longitude=24.9354&current=temperature_2m,wind_speed_10m&timezone=Europe/Helsinki"
```

---

## Troubleshooting

### Common Issues

#### 1. No Data Collected

**Check:**
```bash
# Verify locations exist
docker exec docker-project-database psql -U root webapp_db -c "SELECT COUNT(*) FROM shared_locations WHERE is_active = true;"

# Check API connectivity
docker exec docker-project-api curl -s "https://api.open-meteo.com/v1/forecast?latitude=60.1695&longitude=24.9354&current=temperature_2m"
```

#### 2. Cron Not Running

**Check:**
```bash
# Verify cron is installed
docker exec docker-project-api which cron

# Check cron logs
docker exec docker-project-api tail -f /var/log/cron.log

# Restart cron
docker exec docker-project-api service cron restart
```

#### 3. Database Connection Errors

**Check:**
```bash
# Test database connection
docker exec docker-project-api python3 -c "import psycopg2; conn = psycopg2.connect(host='database', user='root', password='root', database='webapp_db'); print('✓ Connected')"
```

---

## Conclusion

The weather collection system provides:

- ✅ **Comprehensive historic data** (5 years × 44 locations)
- ✅ **Real-time current weather** (updated every 30 minutes)
- ✅ **Automated collection** via cron
- ✅ **Robust error handling** and logging
- ✅ **Scalable architecture** (easily add new locations)

**Result**: A reliable weather data pipeline for analysis and visualization!

---

**Last Updated**: October 8, 2025  
**Consolidated From**: 2 weather system documents
