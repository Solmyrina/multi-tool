#!/usr/bin/env python3
"""
Test script for new stock data APIs
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stock_service import MultiSourceDataFetcher
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_new_apis():
    """Test the new stock data APIs"""
    fetcher = MultiSourceDataFetcher()
    
    # Test symbols
    test_symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "^IXIC"]
    
    print("🚀 Testing New Stock Data APIs")
    print("=" * 50)
    
    for symbol in test_symbols:
        print(f"\n📊 Testing symbol: {symbol}")
        print("-" * 30)
        
        # Test Twelve Data
        print("🔍 Testing Twelve Data API...")
        twelve_data = fetcher.fetch_from_twelve_data(symbol, "1d")
        if twelve_data is not None and not twelve_data.empty:
            print(f"✅ Twelve Data: {len(twelve_data)} records")
            print(f"   Latest price: ${twelve_data.iloc[-1]['Close']:.2f}")
            print(f"   Date range: {twelve_data.index[0]} to {twelve_data.index[-1]}")
        else:
            print("❌ Twelve Data: No data")
        
        # Test Public APIs (includes EOD, Yahoo query1, etc.)
        print("🔍 Testing Public APIs...")
        public_data = fetcher.fetch_from_public_apis(symbol, "1d")
        if public_data is not None and not public_data.empty:
            print(f"✅ Public APIs: {len(public_data)} records")
            print(f"   Latest price: ${public_data.iloc[-1]['Close']:.2f}")
            print(f"   Date range: {public_data.index[0]} to {public_data.index[-1]}")
        else:
            print("❌ Public APIs: No data")
        
        # Test Alpha Vantage (if configured)
        print("🔍 Testing Alpha Vantage...")
        av_data = fetcher.fetch_from_alpha_vantage(symbol, "1d")
        if av_data is not None and not av_data.empty:
            print(f"✅ Alpha Vantage: {len(av_data)} records")
            print(f"   Latest price: ${av_data.iloc[-1]['Close']:.2f}")
        else:
            print("❌ Alpha Vantage: No data (check API key)")
        
        # Test Finnhub (if configured)
        print("🔍 Testing Finnhub...")
        fh_data = fetcher.fetch_from_finnhub(symbol, "1d")
        if fh_data is not None and not fh_data.empty:
            print(f"✅ Finnhub: {len(fh_data)} records")
            print(f"   Latest price: ${fh_data.iloc[-1]['Close']:.2f}")
        else:
            print("❌ Finnhub: No data (check API key)")
        
        print()

if __name__ == "__main__":
    test_new_apis()