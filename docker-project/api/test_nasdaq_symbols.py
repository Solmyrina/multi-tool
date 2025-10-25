#!/usr/bin/env python3
"""
Test script to check which NASDAQ symbols work with yfinance
"""
import yfinance as yf
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_nasdaq_symbols():
    """Test various NASDAQ-related symbols"""
    
    # Try different NASDAQ symbols
    symbols_to_test = [
        ("^IXIC", "NASDAQ Composite"),
        ("NDAQ", "Nasdaq Inc."),
        ("QQQ", "NASDAQ-100 ETF"),
        ("ONEQ", "NASDAQ Composite ETF"),
        ("^NDX", "NASDAQ-100"),
        ("TQQQ", "NASDAQ-100 3x ETF"),
        ("AAPL", "Apple (fallback)"),
        ("MSFT", "Microsoft (fallback)")
    ]
    
    working_symbols = []
    
    for symbol, name in symbols_to_test:
        try:
            logger.info(f"Testing {symbol} ({name})...")
            ticker = yf.Ticker(symbol)
            
            # Try to get recent data
            data = ticker.history(period="5d", interval="1d")
            
            if not data.empty:
                latest_price = data['Close'].iloc[-1]
                logger.info(f"✅ {symbol} works! Latest price: ${latest_price:.2f}")
                working_symbols.append((symbol, name, latest_price))
            else:
                logger.warning(f"❌ {symbol} returned empty data")
                
        except Exception as e:
            logger.error(f"❌ {symbol} failed: {e}")
    
    return working_symbols

if __name__ == "__main__":
    working = test_nasdaq_symbols()
    
    print("\n" + "="*50)
    print("WORKING SYMBOLS:")
    print("="*50)
    
    for symbol, name, price in working:
        print(f"{symbol:10} | {name:25} | ${price:8.2f}")
        
    if working:
        best_symbol = working[0][0]
        print(f"\nRecommended symbol: {best_symbol}")
    else:
        print("\nNo working symbols found!")