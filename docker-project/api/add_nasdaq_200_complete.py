#!/usr/bin/env python3
"""
Script to add the complete top 200 NASDAQ companies by market capitalization
Includes robust error handling, progress tracking, and resume functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stock_service import StockDataService
import logging
import time
import json
from datetime import datetime

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

# Complete top 200 NASDAQ companies by market cap (as of 2024)
TOP_200_NASDAQ_COMPANIES = [
    # Mega Cap (>$200B)
    ("AAPL", "Apple Inc."),
    ("MSFT", "Microsoft Corporation"),
    ("GOOGL", "Alphabet Inc. Class A"),
    ("GOOG", "Alphabet Inc. Class C"),
    ("AMZN", "Amazon.com Inc."),
    ("NVDA", "NVIDIA Corporation"),
    ("TSLA", "Tesla Inc."),
    ("META", "Meta Platforms Inc."),
    
    # Large Cap ($10B-$200B) - Tech
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
    ("PLTR", "Palantir Technologies Inc."),
    ("OKTA", "Okta Inc."),
    ("DOCU", "DocuSign Inc."),
    ("SPLK", "Splunk Inc."),
    ("NOW", "ServiceNow Inc."),
    ("PANW", "Palo Alto Networks Inc."),
    ("MDB", "MongoDB Inc."),
    ("VEEV", "Veeva Systems Inc."),
    ("ZM", "Zoom Video Communications Inc."),
    ("TWLO", "Twilio Inc."),
    ("TTD", "The Trade Desk Inc."),
    ("ESTC", "Elastic N.V."),
    ("FSLY", "Fastly Inc."),
    ("DOCN", "DigitalOcean Holdings Inc."),
    ("GTLB", "GitLab Inc."),
    ("S", "SentinelOne Inc."),
    ("PATH", "UiPath Inc."),
    ("AI", "C3.ai Inc."),
    ("SMCI", "Super Micro Computer Inc."),
    
    # Large Cap - Biotech/Healthcare
    ("REGN", "Regeneron Pharmaceuticals Inc."),
    ("GILD", "Gilead Sciences Inc."),
    ("BIIB", "Biogen Inc."),
    ("MRNA", "Moderna Inc."),
    ("DXCM", "DexCom Inc."),
    ("ILMN", "Illumina Inc."),
    ("VRTX", "Vertex Pharmaceuticals Inc."),
    ("BMRN", "BioMarin Pharmaceutical Inc."),
    ("TECH", "Bio-Techne Corporation"),
    ("EXAS", "Exact Sciences Corporation"),
    ("HOLX", "Hologic Inc."),
    ("SGEN", "Seagen Inc."),
    ("INCY", "Incyte Corporation"),
    ("ALXN", "Alexion Pharmaceuticals Inc."),
    ("CELG", "Celgene Corporation"),
    ("AMGN", "Amgen Inc."),
    ("ABBV", "AbbVie Inc."),
    ("LLY", "Eli Lilly and Company"),
    ("TMO", "Thermo Fisher Scientific Inc."),
    ("ABT", "Abbott Laboratories"),
    ("DHR", "Danaher Corporation"),
    ("BMY", "Bristol-Myers Squibb Company"),
    ("MRK", "Merck & Co. Inc."),
    ("PFE", "Pfizer Inc."),
    ("JNJ", "Johnson & Johnson"),
    ("UNH", "UnitedHealth Group Incorporated"),
    ("CVS", "CVS Health Corporation"),
    ("SYK", "Stryker Corporation"),
    ("BSX", "Boston Scientific Corporation"),
    
    # Large Cap - Consumer & Retail
    ("COST", "Costco Wholesale Corporation"),
    ("SBUX", "Starbucks Corporation"),
    ("MDLZ", "Mondelez International Inc."),
    ("KHC", "The Kraft Heinz Company"),
    ("GIS", "General Mills Inc."),
    ("K", "Kellogg Company"),
    ("CAG", "Conagra Brands Inc."),
    ("CPB", "Campbell Soup Company"),
    ("HSY", "The Hershey Company"),
    ("MKC", "McCormick & Company Incorporated"),
    ("SJM", "The J.M. Smucker Company"),
    ("HRL", "Hormel Foods Corporation"),
    ("TSN", "Tyson Foods Inc."),
    ("MNST", "Monster Beverage Corporation"),
    ("CELH", "Celsius Holdings Inc."),
    ("FIZZ", "National Beverage Corp."),
    ("KDP", "Keurig Dr Pepper Inc."),
    ("PEP", "PepsiCo Inc."),
    ("KO", "The Coca-Cola Company"),
    ("WMT", "Walmart Inc."),
    ("HD", "The Home Depot Inc."),
    ("MCD", "McDonald's Corporation"),
    ("YUM", "Yum! Brands Inc."),
    ("QSR", "Restaurant Brands International Inc."),
    ("CMG", "Chipotle Mexican Grill Inc."),
    ("ROST", "Ross Stores Inc."),
    ("DLTR", "Dollar Tree Inc."),
    ("WBA", "Walgreens Boots Alliance Inc."),
    ("ORLY", "O'Reilly Automotive Inc."),
    ("FAST", "Fastenal Company"),
    ("CPRT", "Copart Inc."),
    ("PAYX", "Paychex Inc."),
    ("ADP", "Automatic Data Processing Inc."),
    
    # Large Cap - Communications & Media
    ("CMCSA", "Comcast Corporation"),
    ("TMUS", "T-Mobile US Inc."),
    ("CHTR", "Charter Communications Inc."),
    ("SIRI", "Sirius XM Holdings Inc."),
    ("WBD", "Warner Bros. Discovery Inc."),
    ("EA", "Electronic Arts Inc."),
    ("MTCH", "Match Group Inc."),
    ("SNAP", "Snap Inc."),
    ("PINS", "Pinterest Inc."),
    ("ROKU", "Roku Inc."),
    ("RBLX", "Roblox Corporation"),
    ("U", "Unity Software Inc."),
    
    # Mid Cap ($2B-$10B) - Emerging Tech
    ("HOOD", "Robinhood Markets Inc."),
    ("COIN", "Coinbase Global Inc."),
    ("SQ", "Block Inc."),
    ("SHOP", "Shopify Inc."),
    ("UBER", "Uber Technologies Inc."),
    ("LYFT", "Lyft Inc."),
    ("DASH", "DoorDash Inc."),
    ("ABNB", "Airbnb Inc."),
    ("ZI", "ZoomInfo Technologies Inc."),
    ("LCID", "Lucid Group Inc."),
    ("RIVN", "Rivian Automotive Inc."),
    
    # Mid Cap - Industrial & Materials
    ("CSX", "CSX Corporation"),
    ("ODFL", "Old Dominion Freight Line Inc."),
    ("CTAS", "Cintas Corporation"),
    ("VRSK", "Verisk Analytics Inc."),
    ("BKR", "Baker Hughes Company"),
    ("FANG", "Diamondback Energy Inc."),
    ("ALGN", "Align Technology Inc."),
    ("IDXX", "IDEXX Laboratories Inc."),
    ("ANSS", "ANSYS Inc."),
    ("MAR", "Marriott International Inc."),
    ("BKNG", "Booking Holdings Inc."),
    ("EBAY", "eBay Inc."),
    ("MELI", "MercadoLibre Inc."),
    
    # Mid Cap - Energy & Utilities
    ("ENPH", "Enphase Energy Inc."),
    ("SEDG", "SolarEdge Technologies Inc."),
    ("PLUG", "Plug Power Inc."),
    ("FSLR", "First Solar Inc."),
    ("RUN", "Sunrun Inc."),
    ("EXC", "Exelon Corporation"),
    ("XEL", "Xcel Energy Inc."),
    
    # Mid Cap - Financial Services
    ("CTSH", "Cognizant Technology Solutions Corporation"),
    ("GEHC", "GE HealthCare Technologies Inc."),
    
    # Mid Cap - Consumer Services & Travel
    ("NCLH", "Norwegian Cruise Line Holdings Ltd."),
    ("CCL", "Carnival Corporation"),
    ("RCL", "Royal Caribbean Cruises Ltd."),
    ("WYNN", "Wynn Resorts Limited"),
    ("MGM", "MGM Resorts International"),
    
    # Mid Cap - International Tech
    ("BIDU", "Baidu Inc."),
    ("JD", "JD.com Inc."),
    ("NTES", "NetEase Inc."),
    ("BILI", "Bilibili Inc."),
    ("BABA", "Alibaba Group Holding Limited"),
    ("PDD", "PDD Holdings Inc."),
    
    # Small Cap - Specialty Tech & Services
    ("CROX", "Crocs Inc."),
    ("LULU", "Lululemon Athletica Inc."),
    ("ZG", "Zillow Group Inc."),
    ("ETSY", "Etsy Inc."),
    ("CHWY", "Chewy Inc."),
    ("CVNA", "Carvana Co."),
    ("PTON", "Peloton Interactive Inc."),
    ("BYND", "Beyond Meat Inc."),
    ("TDOC", "Teladoc Health Inc."),
    ("PENN", "PENN Entertainment Inc."),
    ("DKNG", "DraftKings Inc."),
    ("SKLZ", "Skillz Inc."),
    ("OPEN", "Opendoor Technologies Inc."),
    ("UPST", "Upstart Holdings Inc."),
    ("AFRM", "Affirm Holdings Inc."),
    ("SOFI", "SoFi Technologies Inc."),
    ("LMND", "Lemonade Inc."),
    ("ROOT", "Root Inc."),
    ("MTTR", "Matterport Inc."),
    ("SPCE", "Virgin Galactic Holdings Inc."),
    ("NKLA", "Nikola Corporation"),
    ("RIDE", "Lordstown Motors Corp."),
    ("GOEV", "Canoo Inc."),
    ("HYLN", "Hyliion Holdings Corp."),
    ("QS", "QuantumScape Corporation"),
    ("STEM", "Stem Inc."),
    ("SUNW", "Sunworks Inc."),
    ("NOVA", "Sunnova Energy International Inc."),
    ("CSIQ", "Canadian Solar Inc."),
    ("SPWR", "SunPower Corporation"),
    ("MAXN", "Maxeon Solar Technologies Ltd."),
    ("NEE", "NextEra Energy Inc."),
    ("DUK", "Duke Energy Corporation"),
    ("SO", "The Southern Company"),
    ("AEP", "American Electric Power Company Inc."),
    ("D", "Dominion Energy Inc."),
    ("PCG", "PG&E Corporation"),
    ("EIX", "Edison International"),
    ("SRE", "Sempra Energy"),
    ("PEG", "Public Service Enterprise Group Incorporated"),
    ("ED", "Consolidated Edison Inc.")
]

# Progress tracking file
PROGRESS_FILE = "/tmp/nasdaq_progress.json"

def save_progress(processed_symbols, failed_symbols):
    """Save progress to file"""
    progress = {
        'timestamp': datetime.now().isoformat(),
        'processed': list(processed_symbols),
        'failed': list(failed_symbols),
        'total': len(TOP_200_NASDAQ_COMPANIES)
    }
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def load_progress():
    """Load progress from file"""
    try:
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, 'r') as f:
                progress = json.load(f)
                return set(progress.get('processed', [])), set(progress.get('failed', []))
    except Exception as e:
        logger.warning(f"Could not load progress: {e}")
    return set(), set()

def add_nasdaq_200():
    """Add all 200 NASDAQ companies with progress tracking"""
    try:
        logger.info("Initializing stock data service...")
        stock_service = StockDataService(DB_CONFIG)
        
        # Load previous progress
        processed_symbols, failed_symbols = load_progress()
        logger.info(f"Loaded progress: {len(processed_symbols)} processed, {len(failed_symbols)} failed")
        
        successful = len(processed_symbols)
        failed = len(failed_symbols)
        skipped = 0
        
        logger.info(f"Adding {len(TOP_200_NASDAQ_COMPANIES)} NASDAQ companies...")
        
        for i, (symbol, name) in enumerate(TOP_200_NASDAQ_COMPANIES, 1):
            try:
                # Skip if already processed or failed
                if symbol in processed_symbols:
                    logger.info(f"[{i}/{len(TOP_200_NASDAQ_COMPANIES)}] {symbol} already processed - skipping")
                    continue
                    
                if symbol in failed_symbols:
                    logger.info(f"[{i}/{len(TOP_200_NASDAQ_COMPANIES)}] {symbol} previously failed - skipping")
                    continue
                
                # Check if stock already exists with data
                existing_count = stock_service.get_stock_data_count(symbol)
                if existing_count > 0:
                    logger.info(f"[{i}/{len(TOP_200_NASDAQ_COMPANIES)}] {symbol} already exists with {existing_count} records - skipping")
                    processed_symbols.add(symbol)
                    skipped += 1
                    save_progress(processed_symbols, failed_symbols)
                    continue
                
                logger.info(f"[{i}/{len(TOP_200_NASDAQ_COMPANIES)}] Processing {symbol} ({name})...")
                
                # Fetch and store stock data
                result = stock_service.fetch_and_store_stock_data(
                    symbol=symbol,
                    name=name,
                    exchange="NASDAQ"
                )
                
                if result.get('success', False):
                    successful += 1
                    processed_symbols.add(symbol)
                    logger.info(f"✅ Successfully added {symbol} - {result.get('records', 0)} records")
                else:
                    failed += 1
                    failed_symbols.add(symbol)
                    logger.warning(f"⚠️ Failed to add {symbol}: {result.get('error', 'Unknown error')}")
                
                # Save progress after each stock
                save_progress(processed_symbols, failed_symbols)
                
                # Add delay to avoid rate limiting
                time.sleep(0.5)
                
                # Progress update every 10 stocks
                if i % 10 == 0:
                    logger.info(f"Progress: {successful + skipped} successful, {failed} failed, {len(TOP_200_NASDAQ_COMPANIES) - i} remaining")
                
            except Exception as e:
                failed += 1
                failed_symbols.add(symbol)
                logger.error(f"❌ Error processing {symbol}: {e}")
                save_progress(processed_symbols, failed_symbols)
                continue
        
        logger.info(f"")
        logger.info(f"{'='*80}")
        logger.info(f"FINAL SUMMARY:")
        logger.info(f"{'='*80}")
        logger.info(f"Total companies in list: {len(TOP_200_NASDAQ_COMPANIES)}")
        logger.info(f"Successfully processed: {successful}")
        logger.info(f"Already existed: {skipped}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Success rate: {(successful/(len(TOP_200_NASDAQ_COMPANIES)-skipped)*100):.1f}%" if len(TOP_200_NASDAQ_COMPANIES)-skipped > 0 else "N/A")
        
        return successful, failed, skipped
        
    except Exception as e:
        logger.error(f"Error in main process: {e}")
        return 0, len(TOP_200_NASDAQ_COMPANIES), 0

def main():
    """Main function"""
    try:
        logger.info("🚀 Starting Complete Top 200 NASDAQ companies addition process...")
        logger.info("This will fetch 20 years of daily + 1 year of hourly data for each stock...")
        logger.info("Process supports resuming from interruptions...")
        
        successful, failed, skipped = add_nasdaq_200()
        
        if successful > 0 or skipped > 0:
            logger.info(f"🎉 Process completed! Added {successful} new stocks, {skipped} already existed.")
            logger.info(f"You now have access to {successful + skipped} NASDAQ companies!")
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