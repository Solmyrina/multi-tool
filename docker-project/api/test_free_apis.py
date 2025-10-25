#!/usr/bin/env python3
"""
Test completely free stock APIs that don't require registration
"""
import requests
import json
import pandas as pd
from datetime import datetime

def test_yahoo_query1():
    """Test Yahoo Finance query1 API directly"""
    print("🔍 Testing Yahoo Finance query1 API...")
    
    symbol = "AAPL"
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {
        'interval': '1d',
        'range': '5d',
        'includePrePost': 'false'
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                result = data['chart']['result'][0]
                
                if 'timestamp' in result and 'indicators' in result:
                    timestamps = result['timestamp']
                    quotes = result['indicators']['quote'][0]
                    
                    print(f"✅ Yahoo Finance: Got {len(timestamps)} records")
                    
                    # Show sample data
                    if timestamps and quotes['close']:
                        latest_ts = timestamps[-1]
                        latest_close = quotes['close'][-1]
                        latest_date = datetime.fromtimestamp(latest_ts)
                        
                        print(f"   Latest: {latest_date} - ${latest_close:.2f}")
                        return True
                else:
                    print("❌ Yahoo Finance: No price data in response")
            else:
                print("❌ Yahoo Finance: No chart data in response")
        else:
            print(f"❌ Yahoo Finance: HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}...")
    
    except Exception as e:
        print(f"❌ Yahoo Finance: Error - {e}")
    
    return False

def test_eod_historical():
    """Test EOD Historical Data free endpoint"""
    print("\n🔍 Testing EOD Historical Data...")
    
    symbol = "AAPL"
    # Try the demo endpoint
    url = f"https://eodhistoricaldata.com/api/eod/{symbol}.US"
    params = {
        'fmt': 'json',
        'period': 'd',
        'order': 'd'
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list) and data:
                print(f"✅ EOD Historical: Got {len(data)} records")
                
                # Show latest data
                latest = data[-1]
                print(f"   Latest: {latest.get('date')} - ${latest.get('close', 'N/A')}")
                return True
            else:
                print(f"❌ EOD Historical: Unexpected response format")
                print(f"Response type: {type(data)}")
                print(f"Response: {str(data)[:200]}...")
        else:
            print(f"❌ EOD Historical: HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}...")
    
    except Exception as e:
        print(f"❌ EOD Historical: Error - {e}")
    
    return False

def test_financial_modeling_prep():
    """Test Financial Modeling Prep free endpoint"""
    print("\n🔍 Testing Financial Modeling Prep...")
    
    symbol = "AAPL"
    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}"
    params = {
        'timeseries': '5'
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'historical' in data and data['historical']:
                print(f"✅ Financial Modeling Prep: Got {len(data['historical'])} records")
                
                # Show latest data
                latest = data['historical'][0]  # They return newest first
                print(f"   Latest: {latest.get('date')} - ${latest.get('close', 'N/A')}")
                return True
            else:
                print(f"❌ Financial Modeling Prep: No historical data")
                print(f"Response keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                print(f"Response: {str(data)[:200]}...")
        else:
            print(f"❌ Financial Modeling Prep: HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}...")
    
    except Exception as e:
        print(f"❌ Financial Modeling Prep: Error - {e}")
    
    return False

def test_alpha_vantage_demo():
    """Test Alpha Vantage demo endpoint (no key required)"""
    print("\n🔍 Testing Alpha Vantage demo...")
    
    # Alpha Vantage has a demo endpoint
    url = "https://www.alphavantage.co/query"
    params = {
        'function': 'TIME_SERIES_DAILY',
        'symbol': 'IBM',  # Demo symbol
        'apikey': 'demo'
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'Time Series (Daily)' in data:
                ts_data = data['Time Series (Daily)']
                print(f"✅ Alpha Vantage Demo: Got {len(ts_data)} records")
                
                # Show latest data
                latest_date = max(ts_data.keys())
                latest_data = ts_data[latest_date]
                print(f"   Latest: {latest_date} - ${latest_data.get('4. close', 'N/A')}")
                return True
            else:
                print(f"❌ Alpha Vantage Demo: No time series data")
                print(f"Response keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")
        else:
            print(f"❌ Alpha Vantage Demo: HTTP {response.status_code}")
    
    except Exception as e:
        print(f"❌ Alpha Vantage Demo: Error - {e}")
    
    return False

def main():
    print("🚀 Testing Completely Free Stock APIs")
    print("=" * 50)
    
    results = []
    
    # Test each API
    results.append(("Yahoo Finance query1", test_yahoo_query1()))
    results.append(("EOD Historical Data", test_eod_historical()))
    results.append(("Financial Modeling Prep", test_financial_modeling_prep()))
    results.append(("Alpha Vantage Demo", test_alpha_vantage_demo()))
    
    print("\n📊 Results Summary:")
    print("-" * 30)
    for api_name, success in results:
        status = "✅ Working" if success else "❌ Failed"
        print(f"{api_name}: {status}")
    
    working_count = sum(1 for _, success in results if success)
    print(f"\n🎯 {working_count}/{len(results)} APIs are working")

if __name__ == "__main__":
    main()