#!/usr/bin/env python3
"""
Historic Weather Data Fetcher

This script fetches daily historic weather data for the past 10 years
for all favorite weather locations in the database.

Uses Open-Meteo Historical Weather API:
https://open-meteo.com/en/docs/historical-weather-api
"""

import requests
import psycopg
import psycopg.extras
import time
import sys
import os
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/historic_weather.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HistoricWeatherFetcher:
    """Fetches and stores historic weather data for favorite locations."""
    
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'database'),
            'dbname': os.getenv('DB_NAME', 'webapp_db'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', '530NWC0Gm3pt4O'),
            'port': os.getenv('DB_PORT', '5432')
        }
        self.api_base_url = "https://archive-api.open-meteo.com/v1/archive"
        self.years_back = 10
        self.daily_variables = [
            "temperature_2m_max",
            "temperature_2m_min", 
            "temperature_2m_mean",
            "relative_humidity_2m_mean",
            "precipitation_sum",
            "wind_speed_10m_max",
            "wind_speed_10m_mean",
            "wind_direction_10m_dominant",
            "weather_code"
        ]
        
    def get_db_connection(self):
        """Get database connection."""
        try:
            return psycopg.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None
    
    def get_favorite_locations(self) -> List[Dict]:
        """Get all favorite weather locations from database using shared location system."""
        conn = self.get_db_connection()
        if not conn:
            return []
        
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT DISTINCT swl.id, swl.city_name, swl.country, swl.latitude, swl.longitude
                    FROM shared_weather_locations swl
                    JOIN user_favorite_weather_locations ufwl ON swl.id = ufwl.weather_location_id
                    ORDER BY swl.id
                """)
                locations = cur.fetchall()
                logger.info(f"Found {len(locations)} shared weather locations with user favorites")
                return [dict(loc) for loc in locations]
        except Exception as e:
            logger.error(f"Failed to fetch locations: {e}")
            return []
        finally:
            conn.close()
    
    def get_date_range_for_collection(self) -> Tuple[date, date]:
        """Get the date range for historic data collection."""
        end_date = date.today()  # Include today - Open-Meteo often has current day data
        start_date = end_date - timedelta(days=365 * self.years_back)
        return start_date, end_date
    
    def check_existing_data(self, location_id: int, start_date: date, end_date: date) -> List[date]:
        """Check what dates already have data for a location."""
        conn = self.get_db_connection()
        if not conn:
            return []
        
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT date FROM historic_weather_data 
                    WHERE shared_weather_location_id = %s 
                    AND date >= %s AND date <= %s
                    ORDER BY date
                """, (location_id, start_date, end_date))
                existing_dates = [row[0] for row in cur.fetchall()]
                return existing_dates
        except Exception as e:
            logger.error(f"Failed to check existing data: {e}")
            return []
        finally:
            conn.close()
    
    def fetch_weather_data_for_location(self, location: Dict, start_date: date, end_date: date) -> Optional[Dict]:
        """Fetch historic weather data from Open-Meteo API."""
        try:
            params = {
                'latitude': float(location['latitude']),
                'longitude': float(location['longitude']),
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'daily': ','.join(self.daily_variables),
                'timezone': 'auto',
                'format': 'json'
            }
            
            logger.info(f"Fetching data for {location['city_name']}, {location['country']} "
                       f"from {start_date} to {end_date}")
            
            response = requests.get(self.api_base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'daily' not in data:
                logger.warning(f"No daily data in response for {location['city_name']}")
                return None
                
            return data
            
        except requests.RequestException as e:
            logger.error(f"API request failed for {location['city_name']}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to fetch data for {location['city_name']}: {e}")
            return None
    
    def weather_code_to_symbol(self, weather_code: int) -> str:
        """Convert Open-Meteo weather code to weather symbol."""
        weather_code_map = {
            0: 'clearsky_day',
            1: 'fair_day',
            2: 'partlycloudy_day', 
            3: 'cloudy',
            45: 'fog',
            48: 'fog',
            51: 'lightrain',
            53: 'rain',
            55: 'heavyrain',
            56: 'lightsleet',
            57: 'sleet',
            61: 'lightrain',
            63: 'rain',
            65: 'heavyrain',
            66: 'lightsleet',
            67: 'sleet',
            71: 'lightsnow',
            73: 'snow',
            75: 'heavysnow',
            77: 'snow',
            80: 'lightrain',
            81: 'rain',
            82: 'heavyrain',
            85: 'lightsnow',
            86: 'snow',
            95: 'thunder',
            96: 'thunder',
            99: 'thunder'
        }
        return weather_code_map.get(weather_code, 'unknown')
    
    def parse_time_from_iso(self, iso_string: str) -> Optional[str]:
        """Parse time from ISO datetime string."""
        try:
            if iso_string:
                dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
                return dt.strftime('%H:%M:%S')
        except Exception:
            pass
        return None
    
    def store_weather_data(self, location: Dict, weather_data: Dict) -> int:
        """Store weather data in database."""
        conn = self.get_db_connection()
        if not conn:
            return 0
        
        stored_count = 0
        daily = weather_data['daily']
        dates = daily['time']
        
        try:
            with conn.cursor() as cur:
                for i, date_str in enumerate(dates):
                    try:
                        # Parse date
                        record_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                        
                        # Extract weather data for this day
                        temp_max = daily['temperature_2m_max'][i] if daily['temperature_2m_max'][i] is not None else None
                        temp_min = daily['temperature_2m_min'][i] if daily['temperature_2m_min'][i] is not None else None
                        temp_avg = daily['temperature_2m_mean'][i] if daily['temperature_2m_mean'][i] is not None else None
                        humidity = daily['relative_humidity_2m_mean'][i] if daily['relative_humidity_2m_mean'][i] is not None else None
                        precipitation = daily['precipitation_sum'][i] if daily['precipitation_sum'][i] is not None else None
                        wind_speed_max = daily['wind_speed_10m_max'][i] if daily['wind_speed_10m_max'][i] is not None else None
                        wind_speed_avg = daily['wind_speed_10m_mean'][i] if daily['wind_speed_10m_mean'][i] is not None else None
                        wind_direction = daily['wind_direction_10m_dominant'][i] if daily['wind_direction_10m_dominant'][i] is not None else None
                        weather_code = daily['weather_code'][i] if daily['weather_code'][i] is not None else None
                        
                        weather_symbol = self.weather_code_to_symbol(weather_code) if weather_code is not None else 'unknown'
                        
                        # Parse sunrise/sunset times (not available in historic API)
                        sunrise_time = None
                        sunset_time = None
                        
                        # Insert or update record (prevent duplicates)
                        cur.execute("""
                            INSERT INTO historic_weather_data (
                                shared_weather_location_id, date, temperature_min, temperature_max, 
                                temperature_avg, humidity_avg, precipitation_total,
                                wind_speed_avg, wind_speed_max, wind_direction_avg,
                                weather_symbol, sunrise_time, sunset_time, data_source
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                            )
                            ON CONFLICT (shared_weather_location_id, date) 
                            DO UPDATE SET
                                temperature_min = EXCLUDED.temperature_min,
                                temperature_max = EXCLUDED.temperature_max,
                                temperature_avg = EXCLUDED.temperature_avg,
                                humidity_avg = EXCLUDED.humidity_avg,
                                precipitation_total = EXCLUDED.precipitation_total,
                                wind_speed_avg = EXCLUDED.wind_speed_avg,
                                wind_speed_max = EXCLUDED.wind_speed_max,
                                wind_direction_avg = EXCLUDED.wind_direction_avg,
                                weather_symbol = EXCLUDED.weather_symbol,
                                data_source = EXCLUDED.data_source,
                                updated_at = CURRENT_TIMESTAMP
                        """, (
                            location['id'], record_date, temp_min, temp_max, temp_avg,
                            humidity, precipitation, wind_speed_avg, wind_speed_max,
                            wind_direction, weather_symbol, sunrise_time, sunset_time,
                            'open-meteo'
                        ))
                        stored_count += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to store record for {record_date}: {e}")
                        # Rollback the transaction to allow continuing
                        conn.rollback()
                        continue
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to store weather data: {e}")
            conn.rollback()
        finally:
            conn.close()
        
        return stored_count
    
    def log_collection_progress(self, location: Dict, start_date: date, end_date: date, 
                              status: str, records_collected: int = 0, error_message: str = None):
        """Log collection progress to database."""
        conn = self.get_db_connection()
        if not conn:
            return
        
        try:
            with conn.cursor() as cur:
                if status == 'in_progress':
                    cur.execute("""
                        INSERT INTO historic_weather_collection_log 
                        (weather_location_id, start_date, end_date, status, data_source, started_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (location['id'], start_date, end_date, status, 'open-meteo', datetime.now()))
                    log_id = cur.fetchone()[0]
                else:
                    # Update existing log entry
                    cur.execute("""
                        UPDATE historic_weather_collection_log 
                        SET status = %s, records_collected = %s, error_message = %s, completed_at = %s
                        WHERE weather_location_id = %s AND start_date = %s AND end_date = %s
                        AND status = 'in_progress'
                    """, (status, records_collected, error_message, datetime.now(), 
                         location['id'], start_date, end_date))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to log collection progress: {e}")
        finally:
            conn.close()
    
    def process_location(self, location: Dict) -> bool:
        """Process historic weather data for a single location."""
        start_date, end_date = self.get_date_range_for_collection()
        
        logger.info(f"Processing {location['city_name']}, {location['country']}")
        
        # Check existing data
        existing_dates = self.check_existing_data(location['id'], start_date, end_date)
        if existing_dates:
            logger.info(f"Found {len(existing_dates)} existing records for {location['city_name']}")
        
        # Log start of collection
        self.log_collection_progress(location, start_date, end_date, 'in_progress')
        
        try:
            # Fetch data in yearly chunks to avoid API limits
            total_stored = 0
            current_start = start_date
            
            while current_start <= end_date:
                chunk_end = min(current_start + timedelta(days=365), end_date)
                
                # Check what specific dates are missing in this chunk
                all_dates_in_chunk = []
                current_date = current_start
                while current_date <= chunk_end:
                    all_dates_in_chunk.append(current_date)
                    current_date += timedelta(days=1)
                
                chunk_existing = [d for d in existing_dates if current_start <= d <= chunk_end]
                missing_dates = [d for d in all_dates_in_chunk if d not in chunk_existing]
                
                if not missing_dates:
                    logger.info(f"Skipping {current_start} to {chunk_end} - data already exists")
                    current_start = chunk_end + timedelta(days=1)
                    continue
                
                logger.info(f"Found {len(missing_dates)} missing dates from {current_start} to {chunk_end}")
                
                # Fetch data for this chunk
                weather_data = self.fetch_weather_data_for_location(location, current_start, chunk_end)
                
                if weather_data:
                    stored_count = self.store_weather_data(location, weather_data)
                    total_stored += stored_count
                    logger.info(f"Stored {stored_count} records for {location['city_name']} "
                              f"({current_start} to {chunk_end})")
                else:
                    logger.warning(f"No data received for {location['city_name']} "
                                 f"({current_start} to {chunk_end})")
                
                current_start = chunk_end + timedelta(days=1)
                
                # Add delay to respect API rate limits
                time.sleep(1)
            
            # Log successful completion
            self.log_collection_progress(location, start_date, end_date, 'completed', total_stored)
            logger.info(f"Completed {location['city_name']}: {total_stored} total records")
            return True
            
        except Exception as e:
            error_msg = f"Failed to process {location['city_name']}: {e}"
            logger.error(error_msg)
            self.log_collection_progress(location, start_date, end_date, 'failed', 0, str(e))
            return False
    
    def run(self):
        """Run the historic weather data collection."""
        logger.info("Starting historic weather data collection")
        
        locations = self.get_favorite_locations()
        if not locations:
            logger.error("No favorite locations found")
            return
        
        successful = 0
        failed = 0
        
        for location in locations:
            try:
                if self.process_location(location):
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Unexpected error processing {location['city_name']}: {e}")
                failed += 1
            
            # Add delay between locations
            time.sleep(2)
        
        logger.info(f"Historic weather data collection completed: "
                   f"{successful} successful, {failed} failed")

def main():
    """Main entry point."""
    fetcher = HistoricWeatherFetcher()
    fetcher.run()

if __name__ == "__main__":
    main()