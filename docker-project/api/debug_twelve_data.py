#!/usr/bin/env python3
"""
Debug Twelve Data API response
"""
import requests
import json

def debug_twelve_data():
    url = "https://api.twelvedata.com/time_series"
    params = {
        'symbol': 'AAPL',
        'interval': '1day',
        'outputsize': '5',
        'format': 'JSON'
    }
    
    print("🔍 Testing Twelve Data API directly...")
    print(f"URL: {url}")
    print(f"Params: {params}")
    
    response = requests.get(url, params=params, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:500]}...")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"JSON Keys: {list(data.keys())}")
            return data
        except Exception as e:
            print(f"JSON parse error: {e}")
    
    return None

if __name__ == "__main__":
    debug_twelve_data()