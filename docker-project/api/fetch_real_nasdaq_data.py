#!/usr/bin/env python3
"""
Script to fetch real NASDAQ Composite Index data and replace demo data
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stock_service import StockDataService
import psycopg
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'database',
    'dbname': 'webapp_db', 
    'user': 'root',
    'password': '530NWC0Gm3pt4O',
    'port': '5432'
}

def clear_demo_data():
    """Clear existing demo data from the database"""
    try:
        conn = psycopg.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        logger.info("Clearing existing stock data...")
        
        # Clear in order due to foreign key constraints
        cur.execute("DELETE FROM stock_fetch_logs")
        cur.execute("DELETE FROM stock_prices")
        cur.execute("DELETE FROM stocks")
        
        conn.commit()
        logger.info("Successfully cleared all existing stock data")
        
    except Exception as e:
        logger.error(f"Error clearing demo data: {e}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Main function to replace demo data with real NASDAQ data"""
    try:
        logger.info("Starting NASDAQ data fetch process...")
        
        # Clear existing demo data
        clear_demo_data()
        
        # Initialize stock service
        stock_service = StockDataService(DB_CONFIG)
        
        # Fetch real NASDAQ data
        logger.info("Fetching real NASDAQ Composite Index data...")
        result = stock_service.fetch_and_store_nasdaq_data()
        
        if result['success']:
            logger.info(f"✅ Successfully fetched NASDAQ data!")
            logger.info(f"   Symbol: {result['symbol']}")
            logger.info(f"   Daily records: {result.get('daily_records', 0)}")
            logger.info(f"   Hourly records: {result.get('hourly_records', 0)}")
            logger.info(f"   Total records: {result['records']}")
            
            # Also verify data was stored
            latest_prices = stock_service.get_latest_stock_prices()
            if latest_prices:
                for price in latest_prices:
                    logger.info(f"   Latest price for {price['symbol']}: ${price['current_price']:.2f}")
            
        else:
            logger.error(f"❌ Failed to fetch NASDAQ data: {result.get('error', 'Unknown error')}")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Error in main process: {e}")
        return 1
    
    logger.info("🎉 NASDAQ data fetch completed successfully!")
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)