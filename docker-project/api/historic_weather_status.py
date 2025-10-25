#!/usr/bin/env python3
"""
Historic Weather Data Status

Shows the current status of historic weather data collection.
"""

import sys
import os
sys.path.append('/app')

from fetch_historic_weather import HistoricWeatherFetcher

def main():
    fetcher = HistoricWeatherFetcher()
    conn = fetcher.get_db_connection()
    
    if not conn:
        print("Failed to connect to database")
        return
    
    try:
        with conn.cursor() as cur:
            # Get summary of data collection
            cur.execute("""
                SELECT 
                    wl.city_name,
                    wl.country,
                    COUNT(hwd.id) as records_count,
                    MIN(hwd.date) as earliest_date,
                    MAX(hwd.date) as latest_date,
                    CASE 
                        WHEN COUNT(hwd.id) > 0 THEN 
                            ROUND((COUNT(hwd.id)::numeric / 3650) * 100, 1)
                        ELSE 0 
                    END as completion_percentage
                FROM weather_locations wl
                LEFT JOIN historic_weather_data hwd ON wl.id = hwd.weather_location_id
                GROUP BY wl.id, wl.city_name, wl.country
                ORDER BY wl.city_name
            """)
            
            results = cur.fetchall()
            
            print("Historic Weather Data Collection Status")
            print("=" * 60)
            print(f"{'Location':<25} {'Records':<8} {'Earliest':<12} {'Latest':<12} {'Complete':<8}")
            print("-" * 60)
            
            total_records = 0
            for row in results:
                city_name, country, records_count, earliest_date, latest_date, completion_pct = row
                total_records += records_count or 0
                
                location_name = f"{city_name}"
                if len(location_name) > 24:
                    location_name = location_name[:21] + "..."
                
                earliest_str = str(earliest_date) if earliest_date else "-"
                latest_str = str(latest_date) if latest_date else "-"
                completion_str = f"{completion_pct}%" if completion_pct else "0%"
                
                print(f"{location_name:<25} {records_count or 0:<8} {earliest_str:<12} {latest_str:<12} {completion_str:<8}")
            
            print("-" * 60)
            print(f"Total records: {total_records}")
            
            # Get collection log status
            cur.execute("""
                SELECT 
                    status,
                    COUNT(*) as count
                FROM historic_weather_collection_log
                GROUP BY status
                ORDER BY status
            """)
            
            log_results = cur.fetchall()
            if log_results:
                print("\nCollection Log Summary:")
                for status, count in log_results:
                    print(f"  {status}: {count}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()