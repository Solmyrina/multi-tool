#!/usr/bin/env python3
"""
Test script for checking when financial APIs are available again
Run this periodically to check if Yahoo Finance rate limits have reset
"""

import sys
import os
import time
sys.path.append('/app')

from stock_service import StockDataService

def test_yahoo_finance():
    """Test if Yahoo Finance is working"""
    print("🔍 Testing Yahoo Finance API...")
    
    try:
        import yfinance as yf
        ticker = yf.Ticker('AAPL')
        
        # Quick test - just get basic info
        info = ticker.info
        if info and 'shortName' in info:
            print("✅ Yahoo Finance API is working!")
            return True
        else:
            print("❌ Yahoo Finance returning empty data")
            return False
            
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "Too Many Requests" in error_msg:
            print("⏳ Yahoo Finance still rate limited")
        else:
            print(f"❌ Yahoo Finance error: {e}")
        return False

def test_alternative_apis():
    """Test alternative APIs if configured"""
    print("\n🔍 Testing alternative financial APIs...")
    
    # Test if we have API keys configured
    alpha_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
    finnhub_key = os.environ.get('FINNHUB_API_KEY') 
    iex_key = os.environ.get('IEX_CLOUD_API_KEY')
    
    available_apis = []
    
    if alpha_key and alpha_key.strip():
        available_apis.append("Alpha Vantage")
        
    if finnhub_key and finnhub_key.strip():
        available_apis.append("Finnhub")
        
    if iex_key and iex_key.strip():
        available_apis.append("IEX Cloud")
    
    if available_apis:
        print(f"📋 Configured APIs: {', '.join(available_apis)}")
        return True
    else:
        print("⚠️  No alternative API keys configured")
        print("   Add API keys to .env file to enable backup data sources")
        return False

def main():
    print("🚀 Financial API Status Checker")
    print("=" * 40)
    
    # Test Yahoo Finance
    yahoo_working = test_yahoo_finance()
    
    # Test alternatives
    alternatives_ready = test_alternative_apis()
    
    print("\n📊 Summary:")
    print(f"   Yahoo Finance: {'✅ Working' if yahoo_working else '❌ Rate Limited'}")
    print(f"   Alternative APIs: {'✅ Configured' if alternatives_ready else '⚠️  Not Set Up'}")
    
    if yahoo_working:
        print("\n🎉 Ready to fetch fresh stock data!")
        return True
    elif alternatives_ready:
        print("\n🔄 Yahoo Finance down, but alternatives available")
        return True
    else:
        print("\n⏳ Waiting for APIs to become available...")
        print("   💡 Tip: Set up alternative API keys in .env file")
        return False

if __name__ == "__main__":
    main()