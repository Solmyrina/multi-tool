#!/usr/bin/env python3
"""
Debug script to test Yahoo Finance API issues
"""

import yfinance as yf
import logging
import json
import requests
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_yfinance_basic():
    """Test basic yfinance functionality"""
    print("=== Testing basic yfinance ===")
    try:
        ticker = yf.Ticker("AAPL")
        print(f"Ticker object created: {ticker}")
        
        # Test info
        try:
            info = ticker.info
            print(f"Info keys: {list(info.keys())[:10] if info else 'No info'}")
        except Exception as e:
            print(f"Info failed: {e}")
        
        # Test history with different parameters
        print("\n--- Testing history with 5d period ---")
        data = ticker.history(period="5d", interval="1d")
        print(f"5d data shape: {data.shape if not data.empty else 'Empty'}")
        if not data.empty:
            print(f"Latest date: {data.index[-1]}")
            print(f"Latest price: {data['Close'].iloc[-1]}")
        
        print("\n--- Testing history with 1mo period ---")
        data = ticker.history(period="1mo", interval="1d")
        print(f"1mo data shape: {data.shape if not data.empty else 'Empty'}")
        
        print("\n--- Testing history with 1y period ---")
        data = ticker.history(period="1y", interval="1d")
        print(f"1y data shape: {data.shape if not data.empty else 'Empty'}")
        
    except Exception as e:
        print(f"Basic test failed: {e}")

def test_direct_yahoo_api():
    """Test direct Yahoo Finance API calls"""
    print("\n=== Testing direct Yahoo API ===")
    
    # Yahoo Finance chart API
    symbol = "AAPL"
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    
    params = {
        'period1': int((datetime.now() - timedelta(days=7)).timestamp()),
        'period2': int(datetime.now().timestamp()),
        'interval': '1d',
        'includePrePost': 'true',
        'events': 'div,splits'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        print(f"Status code: {response.status_code}")
        print(f"Response length: {len(response.text)}")
        print(f"Response content type: {response.headers.get('content-type')}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"JSON structure: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                if 'chart' in data and 'result' in data['chart']:
                    result = data['chart']['result']
                    if result:
                        timestamps = result[0].get('timestamp', [])
                        print(f"Number of timestamps: {len(timestamps)}")
                        if timestamps:
                            print(f"Date range: {datetime.fromtimestamp(timestamps[0])} to {datetime.fromtimestamp(timestamps[-1])}")
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                print(f"Raw response (first 500 chars): {response.text[:500]}")
        else:
            print(f"Error response: {response.text[:500]}")
            
    except Exception as e:
        print(f"Direct API test failed: {e}")

def test_different_symbols():
    """Test different stock symbols"""
    print("\n=== Testing different symbols ===")
    symbols = ["AAPL", "MSFT", "GOOGL", "SPY", "QQQ"]
    
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="5d", interval="1d")
            print(f"{symbol}: {'OK' if not data.empty else 'EMPTY'} ({len(data)} records)")
        except Exception as e:
            print(f"{symbol}: ERROR - {e}")

if __name__ == "__main__":
    test_yfinance_basic()
    test_direct_yahoo_api()
    test_different_symbols()