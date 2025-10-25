#!/usr/bin/env python3
"""
Weather Data Collection Status Monitor

Shows comprehensive status of both historic and current weather data collection.
"""

import os
import sys
import psycopg
from psycopg.rows import dict_row
from datetime import datetime, timezone, timedelta

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
        print(f"Database connection failed: {e}")
        return None

def print_header(title):
    """Print a formatted header"""
    print(f"\n{title}")
    print("=" * len(title))

def print_weather_status():
    """Print comprehensive weather data status"""
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database")
        return
    
    try:
        cur = conn.cursor(row_factory=dict_row)
        
        # 1. Historic Weather Data Status
        print_header("Historic Weather Data Status")
        cur.execute("""
            SELECT 
                wl.city_name,
                COUNT(hwd.id) as records,
                MIN(hwd.date) as earliest_date,
                MAX(hwd.date) as latest_date,
                ROUND(COUNT(hwd.id) * 100.0 / 3652, 1) as completion_percent
            FROM weather_locations wl
            LEFT JOIN historic_weather_data hwd ON wl.id = hwd.weather_location_id
            GROUP BY wl.id, wl.city_name
            ORDER BY wl.city_name
        """)
        
        historic_data = cur.fetchall()
        if historic_data:
            print(f"{'Location':<20} {'Records':<8} {'Earliest':<12} {'Latest':<12} {'Complete':<10}")
            print("-" * 70)
            
            total_records = 0
            for row in historic_data:
                total_records += row['records'] or 0
                print(f"{row['city_name']:<20} {row['records'] or 0:<8} "
                      f"{str(row['earliest_date']) if row['earliest_date'] else 'N/A':<12} "
                      f"{str(row['latest_date']) if row['latest_date'] else 'N/A':<12} "
                      f"{row['completion_percent'] or 0:<9.1f}%")
            
            print("-" * 70)
            print(f"Total historic records: {total_records}")
        
        # 2. Current Weather Data Status
        print_header("Current Weather Data Status (Last 7 Days)")
        cur.execute("""
            SELECT 
                wl.city_name,
                COUNT(cwd.id) as records,
                MIN(cwd.recorded_at) as earliest_time,
                MAX(cwd.recorded_at) as latest_time,
                MAX(cwd.temperature) as max_temp,
                MIN(cwd.temperature) as min_temp,
                cwd_latest.weather_description as current_condition
            FROM weather_locations wl
            LEFT JOIN current_weather_data cwd ON wl.id = cwd.weather_location_id 
                AND cwd.recorded_at > CURRENT_TIMESTAMP - INTERVAL '7 days'
            LEFT JOIN LATERAL (
                SELECT weather_description, recorded_at
                FROM current_weather_data cwd2
                WHERE cwd2.weather_location_id = wl.id
                ORDER BY recorded_at DESC
                LIMIT 1
            ) cwd_latest ON true
            GROUP BY wl.id, wl.city_name, cwd_latest.weather_description
            ORDER BY wl.city_name
        """)
        
        current_data = cur.fetchall()
        if current_data:
            print(f"{'Location':<20} {'Records':<8} {'Latest Update':<20} {'Min/Max °C':<12} {'Condition':<20}")
            print("-" * 88)
            
            total_current = 0
            for row in current_data:
                total_current += row['records'] or 0
                latest_str = str(row['latest_time'])[:19] if row['latest_time'] else 'N/A'
                temp_range = f"{row['min_temp']:.1f}/{row['max_temp']:.1f}" if row['min_temp'] else 'N/A'
                condition = row['current_condition'] or 'N/A'
                
                print(f"{row['city_name']:<20} {row['records'] or 0:<8} "
                      f"{latest_str:<20} {temp_range:<12} {condition:<20}")
            
            print("-" * 88)
            print(f"Total current weather records (7 days): {total_current}")
        
        # 3. Collection Log Summary
        print_header("Recent Collection Activity")
        
        # Historic collection logs
        cur.execute("""
            SELECT 
                'Historic' as collection_type,
                wl.city_name,
                COALESCE(hcl.completed_at, hcl.started_at, hcl.created_at) as collection_time,
                hcl.status,
                hcl.records_collected,
                hcl.error_message
            FROM historic_weather_collection_log hcl
            LEFT JOIN weather_locations wl ON hcl.weather_location_id = wl.id
            WHERE COALESCE(hcl.completed_at, hcl.started_at, hcl.created_at) > CURRENT_TIMESTAMP - INTERVAL '24 hours'
            
            UNION ALL
            
            SELECT 
                'Current' as collection_type,
                wl.city_name,
                cwcl.collection_time,
                cwcl.status,
                cwcl.records_collected,
                cwcl.error_message
            FROM current_weather_collection_log cwcl
            LEFT JOIN weather_locations wl ON cwcl.weather_location_id = wl.id
            WHERE cwcl.collection_time > CURRENT_TIMESTAMP - INTERVAL '24 hours'
            
            ORDER BY collection_time DESC
            LIMIT 20
        """)
        
        logs = cur.fetchall()
        if logs:
            print(f"{'Type':<8} {'Location':<20} {'Time':<20} {'Status':<8} {'Records':<8} {'Error':<30}")
            print("-" * 102)
            
            for log in logs:
                time_str = str(log['collection_time'])[:19] if log['collection_time'] else 'N/A'
                location = log['city_name'] or 'All locations'
                error = (log['error_message'] or '')[:30] if log['error_message'] else ''
                
                print(f"{log['collection_type']:<8} {location:<20} {time_str:<20} "
                      f"{log['status']:<8} {log['records_collected'] or 0:<8} {error:<30}")
        
        # 4. System Health Check
        print_header("System Health")
        
        # Check for locations missing recent current data
        cur.execute("""
            SELECT wl.city_name
            FROM weather_locations wl
            LEFT JOIN current_weather_data cwd ON wl.id = cwd.weather_location_id
                AND cwd.recorded_at > CURRENT_TIMESTAMP - INTERVAL '2 hours'
            WHERE cwd.id IS NULL
        """)
        
        missing_current = cur.fetchall()
        if missing_current:
            locations = [row['city_name'] for row in missing_current]
            print(f"⚠️  Locations missing recent current weather data: {', '.join(locations)}")
        else:
            print("✅ All locations have recent current weather data")
        
        # Check for incomplete historic data
        cur.execute("""
            SELECT wl.city_name
            FROM weather_locations wl
            LEFT JOIN (
                SELECT weather_location_id, COUNT(*) as count
                FROM historic_weather_data
                GROUP BY weather_location_id
                HAVING COUNT(*) < 3600
            ) hwd ON wl.id = hwd.weather_location_id
            WHERE hwd.weather_location_id IS NOT NULL OR NOT EXISTS (
                SELECT 1 FROM historic_weather_data hwd2 WHERE hwd2.weather_location_id = wl.id
            )
        """)
        
        incomplete_historic = cur.fetchall()
        if incomplete_historic:
            locations = [row['city_name'] for row in incomplete_historic]
            print(f"⚠️  Locations with incomplete historic data: {', '.join(locations)}")
        else:
            print("✅ All locations have complete historic weather data")
        
        # Check cron job status (if available)
        try:
            import subprocess
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            if result.returncode == 0 and 'collect_current_weather.py' in result.stdout:
                print("✅ Automated hourly collection is configured")
            else:
                print("⚠️  Automated hourly collection may not be configured")
        except:
            print("❓ Unable to check cron job status")
        
    except Exception as e:
        print(f"Error generating status report: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("Weather Data Collection Status Report")
    print("Generated at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print_weather_status()