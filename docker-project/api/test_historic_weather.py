#!/usr/bin/env python3
"""Test script for historic weather data - fetches just 30 days"""

import sys
import os
sys.path.append('/app')

from fetch_historic_weather import HistoricWeatherFetcher
from datetime import date, timedelta

class TestHistoricWeatherFetcher(HistoricWeatherFetcher):
    def __init__(self):
        super().__init__()
        self.years_back = 0  # Override to test with recent data only
    
    def get_date_range_for_collection(self):
        """Get a short date range for testing."""
        end_date = date.today() - timedelta(days=1)  
        start_date = end_date - timedelta(days=30)  # Just 30 days
        return start_date, end_date

def main():
    print("Testing historic weather data collection with 30 days of recent data...")
    fetcher = TestHistoricWeatherFetcher()
    
    # Get first location only for testing
    locations = fetcher.get_favorite_locations()
    if not locations:
        print("No locations found")
        return
    
    test_location = locations[0]
    print(f"Testing with: {test_location['city_name']}, {test_location['country']}")
    
    success = fetcher.process_location(test_location)
    print(f"Test result: {'SUCCESS' if success else 'FAILED'}")

if __name__ == "__main__":
    main()