#!/usr/bin/env python3
"""
Automatic stock data updater - runs periodically to check for API availability
and fetch fresh stock data when possible. Implements 24h timeout when all APIs fail.
"""

import sys
import os
import time
import logging
import json
from datetime import datetime, timedelta
sys.path.append('/app')

from stock_service import StockDataService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/stock_update.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Timeout configuration
TIMEOUT_FILE = '/app/api_timeout.json'
TIMEOUT_HOURS = 24

def get_priority_stocks():
    """Get list of priority stocks to update"""
    return [
        'AAPL',   # Apple
        'MSFT',   # Microsoft  
        'GOOG',   # Google
        'AMZN',   # Amazon
        'TSLA',   # Tesla
        'NVDA',   # NVIDIA
        'META',   # Meta
        'NFLX',   # Netflix
        'GOOGL',  # Alphabet Class A
        'ADBE'    # Adobe
    ]

def is_api_timeout_active():
    """Check if we're in a 24h timeout period after all APIs failed"""
    try:
        if os.path.exists(TIMEOUT_FILE):
            with open(TIMEOUT_FILE, 'r') as f:
                timeout_data = json.load(f)
            
            timeout_time = datetime.fromisoformat(timeout_data['timeout_until'])
            current_time = datetime.now()
            
            if current_time < timeout_time:
                remaining = timeout_time - current_time
                hours_remaining = remaining.total_seconds() / 3600
                logger.info(f"⏰ API timeout active - {hours_remaining:.1f} hours remaining until {timeout_time.strftime('%Y-%m-%d %H:%M:%S')}")
                return True
            else:
                # Timeout expired, remove the file
                os.remove(TIMEOUT_FILE)
                logger.info("✅ API timeout expired - resuming normal operations")
                return False
    except Exception as e:
        logger.warning(f"Error checking timeout file: {e}")
        # If there's an error reading the timeout file, assume no timeout
        if os.path.exists(TIMEOUT_FILE):
            os.remove(TIMEOUT_FILE)
        return False
    
    return False

def set_api_timeout():
    """Set 24h timeout when all APIs fail"""
    timeout_until = datetime.now() + timedelta(hours=TIMEOUT_HOURS)
    timeout_data = {
        'timeout_until': timeout_until.isoformat(),
        'reason': 'All APIs failed',
        'timeout_hours': TIMEOUT_HOURS,
        'created_at': datetime.now().isoformat()
    }
    
    try:
        with open(TIMEOUT_FILE, 'w') as f:
            json.dump(timeout_data, f, indent=2)
        
        logger.info(f"🚫 API timeout set - no attempts for {TIMEOUT_HOURS} hours until {timeout_until.strftime('%Y-%m-%d %H:%M:%S')}")
        return True
    except Exception as e:
        logger.error(f"Error setting timeout file: {e}")
        return False

def clear_api_timeout():
    """Clear API timeout when at least one API succeeds"""
    try:
        if os.path.exists(TIMEOUT_FILE):
            os.remove(TIMEOUT_FILE)
            logger.info("✅ API timeout cleared - at least one API is working")
    except Exception as e:
        logger.warning(f"Error clearing timeout file: {e}")

def check_and_update_stocks():
    """Check API availability and update stocks if possible - SINGLE ATTEMPT PER STOCK with 24h timeout"""
    
    # Check if we're in timeout period
    if is_api_timeout_active():
        return False
    
    logger.info("🔍 Checking financial API availability...")
    
    # Database configuration
    DB_CONFIG = {
        'host': os.environ.get('DB_HOST', 'database'),
        'dbname': os.environ.get('DB_NAME', 'webapp_db'),
        'user': os.environ.get('DB_USER', 'root'),
        'password': os.environ.get('DB_PASSWORD', '530NWC0Gm3pt4O'),
        'port': os.environ.get('DB_PORT', '5432')
    }
    
    try:
        service = StockDataService(DB_CONFIG)
        priority_stocks = get_priority_stocks()
        
        successful_updates = 0
        failed_updates = 0
        
        for symbol in priority_stocks:
            try:
                logger.info(f"📈 Attempting to update {symbol}...")
                
                # Single attempt to fetch recent data
                data = service.fetch_historical_data(symbol, period='5d', interval='1d')
                
                if data is not None and not data.empty:
                    # Store the data
                    stock_id = service.get_or_create_stock(symbol)
                    if stock_id:
                        stored_count = service.store_stock_data(stock_id, data)
                        if stored_count > 0:
                            logger.info(f"✅ Updated {symbol}: {stored_count} new records")
                            successful_updates += 1
                        else:
                            logger.info(f"ℹ️  {symbol}: No new data to store")
                            successful_updates += 1
                    else:
                        logger.error(f"❌ Could not get/create stock ID for {symbol}")
                        failed_updates += 1
                else:
                    logger.info(f"⚠️  {symbol}: All APIs failed - no data available")
                    failed_updates += 1
                    
                # Brief pause between requests
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Error updating {symbol}: {e}")
                failed_updates += 1
        
        # Summary
        total_stocks = len(priority_stocks)
        logger.info(f"📊 Update Summary:")
        logger.info(f"   Total stocks: {total_stocks}")
        logger.info(f"   Successful: {successful_updates}")
        logger.info(f"   Failed: {failed_updates}")
        
        if successful_updates > 0:
            # At least one API is working - clear any existing timeout
            clear_api_timeout()
            logger.info("🎉 Successfully updated some stocks with fresh data!")
            return True
        else:
            # All APIs failed - set 24h timeout
            set_api_timeout()
            logger.info("🚫 All APIs failed - setting 24-hour timeout before next attempt")
            return False
            
    except Exception as e:
        logger.error(f"💥 Critical error in stock updater: {e}")
        return False

def main():
    """Main function for the stock updater with 24h timeout support"""
    logger.info("🚀 Starting automatic stock data updater")
    logger.info(f"⏰ Current time: {datetime.now()}")
    
    # Check if we're in timeout period first
    if is_api_timeout_active():
        logger.info("⏸️  Skipping update - in 24h timeout period")
        return
    
    success = check_and_update_stocks()
    
    if success:
        logger.info("✅ Stock update completed successfully")
    else:
        logger.info("🚫 All APIs failed - 24h timeout activated")
    
    logger.info("🏁 Stock updater finished")

if __name__ == "__main__":
    main()