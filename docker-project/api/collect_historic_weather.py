#!/usr/bin/env python3
"""
Production Historic Weather Data Collection

This script collects historic weather data for all favorite locations.
It can be run multiple times safely and will only fetch missing data.
"""

import sys
import os
sys.path.append('/app')

from fetch_historic_weather import HistoricWeatherFetcher
import argparse

def main():
    parser = argparse.ArgumentParser(description='Collect historic weather data')
    parser.add_argument('--years', type=int, default=10, help='Number of years to collect (default: 10)')
    parser.add_argument('--location-id', type=int, help='Process only specific location ID')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without actually doing it')
    
    args = parser.parse_args()
    
    fetcher = HistoricWeatherFetcher()
    fetcher.years_back = args.years
    
    if args.dry_run:
        print(f"DRY RUN: Would collect {args.years} years of historic weather data")
        locations = fetcher.get_favorite_locations()
        for loc in locations:
            if args.location_id and loc['id'] != args.location_id:
                continue
            print(f"  - {loc['city_name']}, {loc['country']} (ID: {loc['id']})")
        return
    
    if args.location_id:
        # Process single location
        locations = fetcher.get_favorite_locations()
        target_location = next((loc for loc in locations if loc['id'] == args.location_id), None)
        if not target_location:
            print(f"Location ID {args.location_id} not found")
            return
        
        print(f"Processing single location: {target_location['city_name']}, {target_location['country']}")
        success = fetcher.process_location(target_location)
        print(f"Result: {'SUCCESS' if success else 'FAILED'}")
    else:
        # Process all locations
        print(f"Starting collection of {args.years} years of historic weather data for all locations...")
        fetcher.run()

if __name__ == "__main__":
    main()