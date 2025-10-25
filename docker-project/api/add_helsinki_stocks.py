#!/usr/bin/env python3
"""
Script to add major Helsinki Stock Exchange (OMX Helsinki) stocks to the database
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

# Major Helsinki Stock Exchange companies
# Using .HE suffix for Yahoo Finance API
HELSINKI_STOCKS = [
    # Blue chip companies from OMX Helsinki 25
    ("NOKIA.HE", "Nokia Corporation"),
    ("NESTE.HE", "Neste Corporation"),
    ("UPM.HE", "UPM-Kymmene Corporation"),
    ("STORA.HE", "Stora Enso Oyj"),
    ("FORTUM.HE", "Fortum Corporation"),
    ("SAMPO.HE", "Sampo Plc"),
    ("NORDEA.HE", "Nordea Bank Abp"),
    ("ELISA.HE", "Elisa Corporation"),
    ("TLS1V.HE", "Telia Company AB"),
    ("KESBV.HE", "Kesko Corporation"),
    ("KNEBV.HE", "KONE Corporation"),
    ("METSO.HE", "Metso Corporation"),
    ("ORNBV.HE", "Orion Corporation"),
    ("WRT1V.HE", "Wartsila Corporation"),
    ("TYRES.HE", "Nokian Tyres plc"),
    ("YIT.HE", "YIT Corporation"),
    ("CGCBV.HE", "Cargotec Corporation"),
    ("KESKOA.HE", "Kesko Corporation A"),
    ("OKDBV.HE", "Olvi plc"),
    ("RTRKS.HE", "Rettig Group"),
    ("ATRAV.HE", "Atra Zeneca"),
    ("VALMT.HE", "Valmet Corporation"),
    ("STERV.HE", "Steris Corporation"),
    ("OUTBV.HE", "Outokumpu Oyj"),
    ("KONECRANES.HE", "Konecranes Plc"),
    
    # Additional major companies
    ("HUHTAMAKI.HE", "Huhtamaki Oyj"),
    ("CITYCON.HE", "Citycon Oyj"),
    ("SPONDA.HE", "Sponda Oyj"),
    ("RAISIO.HE", "Raisio plc"),
    ("RAPALA.HE", "Rapala VMC Corporation"),
]

def main():
    """Main function to add Helsinki stocks to the database"""
    try:
        logger.info("Starting Helsinki Stock Exchange data addition...")
        
        # Initialize stock service
        stock_service = StockDataService(DB_CONFIG)
        
        total_success = 0
        total_failed = 0
        
        for symbol, name in HELSINKI_STOCKS:
            try:
                logger.info(f"Processing {symbol} - {name}...")
                
                # Fetch and store stock data
                result = stock_service.fetch_and_store_stock_data(
                    symbol=symbol,
                    name=name,
                    exchange="HELSINKI"
                )
                
                if result['success']:
                    logger.info(f"✅ Successfully added {symbol}")
                    logger.info(f"   Daily records: {result.get('daily_records', 0)}")
                    logger.info(f"   Hourly records: {result.get('hourly_records', 0)}")
                    logger.info(f"   Total records: {result['records']}")
                    total_success += 1
                else:
                    logger.error(f"❌ Failed to add {symbol}: {result.get('error', 'Unknown error')}")
                    total_failed += 1
                    
            except Exception as e:
                logger.error(f"❌ Error processing {symbol}: {e}")
                total_failed += 1
                continue
        
        logger.info(f"\n🎉 Helsinki stocks addition completed!")
        logger.info(f"   Successfully added: {total_success}")
        logger.info(f"   Failed: {total_failed}")
        logger.info(f"   Total processed: {len(HELSINKI_STOCKS)}")
        
        if total_success > 0:
            # Verify some data was stored
            latest_prices = stock_service.get_latest_stock_prices()
            helsinki_stocks = [p for p in latest_prices if p['symbol'].endswith('.HE')]
            
            if helsinki_stocks:
                logger.info(f"\n📊 Sample Helsinki stock prices:")
                for stock in helsinki_stocks[:5]:  # Show first 5
                    logger.info(f"   {stock['symbol']}: €{stock['current_price']:.2f}")
            
        return 0 if total_failed == 0 else 1
            
    except Exception as e:
        logger.error(f"❌ Error in main process: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)