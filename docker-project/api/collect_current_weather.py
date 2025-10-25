#!/usr/bin/env python3
"""
Current Weather Data Collection Script

Collects current weather data from yr.no API for all favorite locations
and stores it in the database for hourly tracking.

Usage:
    python3 collect_current_weather.py
    python3 collect_current_weather.py --location-id 1
    python3 collect_current_weather.py --dry-run
"""

import os
import sys
import logging
import requests
import psycopg
from psycopg.rows import dict_row
from datetime import datetime, timezone
import argparse
import time
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/current_weather.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg.connect(
            host=os.environ.get('DATABASE_HOST', 'database'),
            database=os.environ.get('DATABASE_NAME', 'webapp_db'),
            user=os.environ.get('DATABASE_USER', 'root'),
            password=os.environ.get('DATABASE_PASSWORD', '530NWC0Gm3pt4O')
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def get_weather_symbol_code(symbol_name: str) -> str:
    """Convert yr.no symbol name to simplified code"""
    symbol_mapping = {
        'clearsky': 'clear',
        'fair': 'fair', 
        'partlycloudy': 'partly-cloudy',
        'cloudy': 'cloudy',
        'rainshowers': 'rain-showers',
        'rainshowersandthunder': 'rain-thunder',
        'sleetshowers': 'sleet-showers',
        'snowshowers': 'snow-showers',
        'rain': 'rain',
        'heavyrain': 'heavy-rain',
        'heavyrainandthunder': 'heavy-rain-thunder',
        'sleet': 'sleet',
        'snow': 'snow',
        'snowandthunder': 'snow-thunder',
        'fog': 'fog',
        'sleetshowersandthunder': 'sleet-thunder',
        'snowshowersandthunder': 'snow-thunder',
        'rainandthunder': 'rain-thunder',
        'sleetandthunder': 'sleet-thunder'
    }
    return symbol_mapping.get(symbol_name, symbol_name)

def fetch_current_weather(latitude: float, longitude: float, location_name: str) -> Optional[Dict[str, Any]]:
    """Fetch current weather data from yr.no API"""
    try:
        # yr.no API endpoint for current weather
        url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact"
        params = {
            'lat': latitude,
            'lon': longitude
        }
        
        headers = {
            'User-Agent': 'WeatherApp/1.0 (your-email@domain.com)'  # yr.no requires User-Agent
        }
        
        # Retry logic with exponential backoff for transient failures
        max_retries = 3
        retry_delay = 2  # seconds
        last_error = None
        
        for attempt in range(max_retries):
            try:
                start_time = time.time()
                response = requests.get(url, params=params, headers=headers, timeout=30)
                api_response_time = int((time.time() - start_time) * 1000)
                
                if response.status_code != 200:
                    logger.warning(f"API request failed for {location_name} (attempt {attempt+1}/{max_retries}): {response.status_code} {response.reason}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                        continue
                    else:
                        logger.error(f"All retries failed for {location_name}")
                        return None
                
                # Success - break retry loop
                break
                
            except (requests.exceptions.RequestException, OSError) as e:
                last_error = str(e)
                logger.warning(f"Network error for {location_name} (attempt {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))  # Exponential backoff: 2s, 4s, 6s
                else:
                    logger.error(f"Failed to fetch weather for {location_name} after {max_retries} attempts: {last_error}")
                    return None
        
        data = response.json()
        
        # Get current weather from first time period (should be current hour)
        if not data.get('properties', {}).get('timeseries'):
            logger.warning(f"No weather data in response for {location_name}")
            return None
        
        current_data = data['properties']['timeseries'][0]
        instant_data = current_data['data']['instant']['details']
        
        # Get weather symbol from next_1_hours if available, otherwise next_6_hours
        weather_symbol = None
        weather_description = None
        
        if 'next_1_hours' in current_data['data']:
            weather_symbol = current_data['data']['next_1_hours']['summary']['symbol_code']
        elif 'next_6_hours' in current_data['data']:
            weather_symbol = current_data['data']['next_6_hours']['summary']['symbol_code']
        
        if weather_symbol:
            # Remove day/night suffix for consistency
            weather_symbol = weather_symbol.replace('_day', '').replace('_night', '')
            weather_description = weather_symbol.replace('_', ' ').title()
        
        # Extract weather data
        weather_data = {
            'temperature': instant_data.get('air_temperature'),
            'humidity': instant_data.get('relative_humidity'),
            'pressure': instant_data.get('air_pressure_at_sea_level'),
            'wind_speed': instant_data.get('wind_speed'),
            'wind_direction': instant_data.get('wind_from_direction'),
            'wind_gust': instant_data.get('wind_speed_of_gust'),
            'precipitation': None,  # Current precipitation not available in instant data
            'cloud_cover': instant_data.get('cloud_area_fraction'),
            'visibility': None,  # Not available in yr.no API
            'weather_symbol': get_weather_symbol_code(weather_symbol) if weather_symbol else None,
            'weather_description': weather_description,
            'feels_like': None,  # Not available in yr.no API
            'uv_index': instant_data.get('ultraviolet_index_clear_sky'),
            'api_response_time': api_response_time,
            'recorded_at': datetime.now(timezone.utc)
        }
        
        logger.info(f"Successfully fetched weather data for {location_name}")
        return weather_data
        
    except requests.RequestException as e:
        logger.error(f"Request failed for {location_name}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error fetching weather data for {location_name}: {e}")
        return None

def store_weather_data(conn, location_id: int, weather_data: Dict[str, Any], location_name: str) -> bool:
    """Store weather data in database"""
    try:
        cur = conn.cursor()
        
        # Round recorded_at to the current hour to avoid duplicates
        recorded_at = weather_data['recorded_at'].replace(minute=0, second=0, microsecond=0)
        
        # Insert weather data with ON CONFLICT to handle duplicates
        cur.execute("""
            INSERT INTO current_weather_data (
                weather_location_id, recorded_at, temperature, humidity, pressure,
                wind_speed, wind_direction, wind_gust, precipitation, cloud_cover,
                visibility, weather_symbol, weather_description, feels_like, uv_index,
                data_source, api_response_time
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) ON CONFLICT (weather_location_id, recorded_at) 
            DO UPDATE SET
                temperature = EXCLUDED.temperature,
                humidity = EXCLUDED.humidity,
                pressure = EXCLUDED.pressure,
                wind_speed = EXCLUDED.wind_speed,
                wind_direction = EXCLUDED.wind_direction,
                wind_gust = EXCLUDED.wind_gust,
                precipitation = EXCLUDED.precipitation,
                cloud_cover = EXCLUDED.cloud_cover,
                weather_symbol = EXCLUDED.weather_symbol,
                weather_description = EXCLUDED.weather_description,
                uv_index = EXCLUDED.uv_index,
                api_response_time = EXCLUDED.api_response_time,
                created_at = CURRENT_TIMESTAMP
        """, (
            location_id, recorded_at, weather_data['temperature'], weather_data['humidity'],
            weather_data['pressure'], weather_data['wind_speed'], weather_data['wind_direction'],
            weather_data['wind_gust'], weather_data['precipitation'], weather_data['cloud_cover'],
            weather_data['visibility'], weather_data['weather_symbol'], weather_data['weather_description'],
            weather_data['feels_like'], weather_data['uv_index'], 'yr.no', weather_data['api_response_time']
        ))
        
        conn.commit()
        
        # Log success
        cur.execute("""
            INSERT INTO current_weather_collection_log (
                weather_location_id, status, records_collected, api_response_time, yr_no_api_status
            ) VALUES (%s, %s, %s, %s, %s)
        """, (location_id, 'success', 1, weather_data['api_response_time'], 200))
        
        conn.commit()
        logger.info(f"Stored weather data for {location_name}")
        return True
        
    except Exception as e:
        logger.error(f"Error storing weather data for {location_name}: {e}")
        conn.rollback()
        
        # Log failure
        try:
            cur.execute("""
                INSERT INTO current_weather_collection_log (
                    weather_location_id, status, records_collected, error_message
                ) VALUES (%s, %s, %s, %s)
            """, (location_id, 'failed', 0, str(e)))
            conn.commit()
        except:
            pass
        
        return False

def collect_weather_for_location(location: Dict[str, Any], dry_run: bool = False) -> bool:
    """Collect weather data for a single location"""
    location_id = location['id']
    location_name = f"{location['city_name']}, {location['country']}"
    
    logger.info(f"Collecting weather data for {location_name}")
    
    if dry_run:
        logger.info(f"DRY RUN: Would collect weather for {location_name}")
        return True
    
    # Fetch weather data
    weather_data = fetch_current_weather(
        location['latitude'], 
        location['longitude'], 
        location_name
    )
    
    if not weather_data:
        logger.warning(f"No weather data received for {location_name}")
        return False
    
    # Store in database
    conn = get_db_connection()
    if not conn:
        logger.error(f"Database connection failed for {location_name}")
        return False
    
    try:
        success = store_weather_data(conn, location_id, weather_data, location_name)
        return success
    finally:
        conn.close()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Collect current weather data from yr.no API')
    parser.add_argument('--location-id', type=int, help='Collect for specific location ID only')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without actually doing it')
    
    args = parser.parse_args()
    
    logger.info("Starting current weather data collection")
    
    # Get database connection
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        sys.exit(1)
    
    try:
        cur = conn.cursor(row_factory=dict_row)
        
        if args.location_id:
            # Collect for specific location
            cur.execute("""
                SELECT id, city_name, country, latitude, longitude 
                FROM weather_locations 
                WHERE id = %s
            """, (args.location_id,))
            locations = cur.fetchall()
            
            if not locations:
                logger.error(f"Location ID {args.location_id} not found")
                sys.exit(1)
                
            logger.info(f"Processing single location: {locations[0]['city_name']}, {locations[0]['country']}")
        else:
            # Collect for all locations
            cur.execute("""
                SELECT id, city_name, country, latitude, longitude 
                FROM weather_locations 
                ORDER BY city_name
            """)
            locations = cur.fetchall()
            
            logger.info(f"Found {len(locations)} favorite locations")
        
        successful = 0
        failed = 0
        
        for location in locations:
            try:
                if collect_weather_for_location(location, args.dry_run):
                    successful += 1
                else:
                    failed += 1
                
                # Small delay between requests to be respectful to API
                if not args.dry_run:
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Unexpected error processing {location['city_name']}: {e}")
                failed += 1
        
        logger.info(f"Current weather data collection completed: {successful} successful, {failed} failed")
        
        if failed > 0:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()