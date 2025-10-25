#!/usr/bin/env python3
"""
Script to add the most popular NASDAQ stocks in smaller batches
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stock_service import StockDataService
import logging
import time

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

# Top 50 most popular NASDAQ stocks (Mega and Large Cap)
TOP_50_NASDAQ_STOCKS = [
    # Mega Cap Tech Giants
    ("AAPL", "Apple Inc."),
    ("MSFT", "Microsoft Corporation"),
    ("GOOGL", "Alphabet Inc. Class A"),
    ("GOOG", "Alphabet Inc. Class C"),
    ("AMZN", "Amazon.com Inc."),
    ("NVDA", "NVIDIA Corporation"),
    ("TSLA", "Tesla Inc."),
    ("META", "Meta Platforms Inc."),
    
    # Large Cap Tech
    ("AVGO", "Broadcom Inc."),
    ("NFLX", "Netflix Inc."),
    ("ADBE", "Adobe Inc."),
    ("ORCL", "Oracle Corporation"),
    ("CRM", "Salesforce Inc."),
    ("CSCO", "Cisco Systems Inc."),
    ("INTC", "Intel Corporation"),
    ("AMD", "Advanced Micro Devices Inc."),
    ("QCOM", "QUALCOMM Incorporated"),
    ("TXN", "Texas Instruments Incorporated"),
    ("INTU", "Intuit Inc."),
    ("ISRG", "Intuitive Surgical Inc."),
    ("AMAT", "Applied Materials Inc."),
    ("ADI", "Analog Devices Inc."),
    ("MU", "Micron Technology Inc."),
    ("LRCX", "Lam Research Corporation"),
    ("KLAC", "KLA Corporation"),
    ("PYPL", "PayPal Holdings Inc."),
    ("SNPS", "Synopsys Inc."),
    ("CDNS", "Cadence Design Systems Inc."),
    ("MRVL", "Marvell Technology Inc."),
    ("FTNT", "Fortinet Inc."),
    ("ADSK", "Autodesk Inc."),
    ("NXPI", "NXP Semiconductors N.V."),
    ("WDAY", "Workday Inc."),
    ("TEAM", "Atlassian Corporation"),
    ("DDOG", "Datadog Inc."),
    ("CRWD", "CrowdStrike Holdings Inc."),
    ("ZS", "Zscaler Inc."),
    ("NET", "Cloudflare Inc."),
    ("SNOW", "Snowflake Inc."),
    
    # Popular Consumer & Other Sectors
    ("COST", "Costco Wholesale Corporation"),
    ("SBUX", "Starbucks Corporation"),
    ("MDLZ", "Mondelez International Inc."),
    ("MNST", "Monster Beverage Corporation"),
    ("REGN", "Regeneron Pharmaceuticals Inc."),
    ("GILD", "Gilead Sciences Inc."),
    ("BIIB", "Biogen Inc."),
    ("MRNA", "Moderna Inc."),
    ("DXCM", "DexCom Inc."),
    ("ILMN", "Illumina Inc.")
]

def add_popular_stocks():
    """Add the top 50 popular NASDAQ stocks"""
    try:
        logger.info("Initializing stock data service...")
        stock_service = StockDataService(DB_CONFIG)
        
        logger.info(f"Adding {len(TOP_50_NASDAQ_STOCKS)} popular NASDAQ stocks...")
        
        successful = 0
        failed = 0
        skipped = 0
        
        for i, (symbol, name) in enumerate(TOP_50_NASDAQ_STOCKS, 1):
            try:
                # Check if stock already exists with data
                existing_count = stock_service.get_stock_data_count(symbol)
                if existing_count > 0:
                    logger.info(f"[{i}/{len(TOP_50_NASDAQ_STOCKS)}] {symbol} already exists with {existing_count} records - skipping")
                    skipped += 1
                    continue
                
                logger.info(f"[{i}/{len(TOP_50_NASDAQ_STOCKS)}] Processing {symbol} ({name})...")
                
                # Fetch and store stock data
                result = stock_service.fetch_and_store_stock_data(
                    symbol=symbol,
                    name=name,
                    exchange="NASDAQ"
                )
                
                if result.get('success', False):
                    successful += 1
                    logger.info(f"✅ Successfully added {symbol} - {result.get('records', 0)} records")
                else:
                    failed += 1
                    logger.warning(f"⚠️ Failed to add {symbol}: {result.get('error', 'Unknown error')}")
                
                # Add delay to avoid rate limiting
                time.sleep(1.0)
                
            except Exception as e:
                failed += 1
                logger.error(f"❌ Error processing {symbol}: {e}")
                continue
        
        logger.info(f"")
        logger.info(f"{'='*60}")
        logger.info(f"SUMMARY:")
        logger.info(f"{'='*60}")
        logger.info(f"Total stocks processed: {len(TOP_50_NASDAQ_STOCKS)}")
        logger.info(f"Successfully added: {successful}")
        logger.info(f"Already existed: {skipped}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Success rate: {(successful/(len(TOP_50_NASDAQ_STOCKS)-skipped)*100):.1f}%" if len(TOP_50_NASDAQ_STOCKS)-skipped > 0 else "N/A")
        
        return successful, failed, skipped
        
    except Exception as e:
        logger.error(f"Error in main process: {e}")
        return 0, len(TOP_50_NASDAQ_STOCKS), 0

def main():
    """Main function"""
    try:
        logger.info("🚀 Starting Top 50 Popular NASDAQ stocks addition process...")
        logger.info("This will add the most popular and heavily traded NASDAQ stocks...")
        
        successful, failed, skipped = add_popular_stocks()
        
        if successful > 0 or skipped > 0:
            logger.info(f"🎉 Process completed! Added {successful} new stocks, {skipped} already existed.")
            return 0
        else:
            logger.error(f"❌ Process failed! No stocks were added successfully.")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)