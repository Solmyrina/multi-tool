#!/usr/bin/env python3
"""
Script to add the top 200 NASDAQ companies by market capitalization
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

# Top 200 NASDAQ companies by market cap
TOP_NASDAQ_STOCKS = [
    # Mega Cap (> $200B)
    ("AAPL", "Apple Inc."),
    ("MSFT", "Microsoft Corporation"),
    ("GOOGL", "Alphabet Inc. Class A"),
    ("GOOG", "Alphabet Inc. Class C"),
    ("AMZN", "Amazon.com Inc."),
    ("NVDA", "NVIDIA Corporation"),
    ("TSLA", "Tesla Inc."),
    ("META", "Meta Platforms Inc."),
    
    # Large Cap ($10B - $200B)
    ("AVGO", "Broadcom Inc."),
    ("NFLX", "Netflix Inc."),
    ("ADBE", "Adobe Inc."),
    ("ORCL", "Oracle Corporation"),
    ("CRM", "Salesforce Inc."),
    ("CSCO", "Cisco Systems Inc."),
    ("PEP", "PepsiCo Inc."),
    ("COST", "Costco Wholesale Corporation"),
    ("CMCSA", "Comcast Corporation"),
    ("TMUS", "T-Mobile US Inc."),
    ("INTC", "Intel Corporation"),
    ("AMD", "Advanced Micro Devices Inc."),
    ("QCOM", "QUALCOMM Incorporated"),
    ("TXN", "Texas Instruments Incorporated"),
    ("INTU", "Intuit Inc."),
    ("ISRG", "Intuitive Surgical Inc."),
    ("AMAT", "Applied Materials Inc."),
    ("BKNG", "Booking Holdings Inc."),
    ("ADI", "Analog Devices Inc."),
    ("MU", "Micron Technology Inc."),
    ("LRCX", "Lam Research Corporation"),
    ("MDLZ", "Mondelez International Inc."),
    ("GILD", "Gilead Sciences Inc."),
    ("MELI", "MercadoLibre Inc."),
    ("KLAC", "KLA Corporation"),
    ("PYPL", "PayPal Holdings Inc."),
    ("REGN", "Regeneron Pharmaceuticals Inc."),
    ("SNPS", "Synopsys Inc."),
    ("CDNS", "Cadence Design Systems Inc."),
    ("MAR", "Marriott International Inc."),
    ("ORLY", "O'Reilly Automotive Inc."),
    ("MRVL", "Marvell Technology Inc."),
    ("CSX", "CSX Corporation"),
    ("FTNT", "Fortinet Inc."),
    ("ADSK", "Autodesk Inc."),
    ("NXPI", "NXP Semiconductors N.V."),
    ("ADP", "Automatic Data Processing Inc."),
    ("ABNB", "Airbnb Inc."),
    ("WDAY", "Workday Inc."),
    ("MNST", "Monster Beverage Corporation"),
    ("PAYX", "Paychex Inc."),
    ("CPRT", "Copart Inc."),
    ("ROST", "Ross Stores Inc."),
    ("ODFL", "Old Dominion Freight Line Inc."),
    ("FAST", "Fastenal Company"),
    ("BKR", "Baker Hughes Company"),
    ("EA", "Electronic Arts Inc."),
    ("VRSK", "Verisk Analytics Inc."),
    ("EXC", "Exelon Corporation"),
    ("XEL", "Xcel Energy Inc."),
    ("DDOG", "Datadog Inc."),
    ("TEAM", "Atlassian Corporation"),
    ("CTSH", "Cognizant Technology Solutions"),
    ("GEHC", "GE HealthCare Technologies"),
    ("CRWD", "CrowdStrike Holdings Inc."),
    ("BIIB", "Biogen Inc."),
    ("IDXX", "IDEXX Laboratories Inc."),
    ("FANG", "Diamondback Energy Inc."),
    ("ZS", "Zscaler Inc."),
    ("CTAS", "Cintas Corporation"),
    ("MRNA", "Moderna Inc."),
    ("WBD", "Warner Bros. Discovery Inc."),
    ("DXCM", "DexCom Inc."),
    ("ILMN", "Illumina Inc."),
    ("TTD", "The Trade Desk Inc."),
    ("SGEN", "Seagen Inc."),
    ("EBAY", "eBay Inc."),
    ("ANSS", "ANSYS Inc."),
    ("CHTR", "Charter Communications Inc."),
    ("PDD", "PDD Holdings Inc."),
    ("ZM", "Zoom Video Communications"),
    ("SPLK", "Splunk Inc."),
    ("MTCH", "Match Group Inc."),
    ("WBA", "Walgreens Boots Alliance"),
    ("DLTR", "Dollar Tree Inc."),
    ("LCID", "Lucid Group Inc."),
    ("ALGN", "Align Technology Inc."),
    ("RIVN", "Rivian Automotive Inc."),
    ("CROX", "Crocs Inc."),
    
    # Mid Cap ($2B - $10B)
    ("OKTA", "Okta Inc."),
    ("DOCU", "DocuSign Inc."),
    ("HOOD", "Robinhood Markets Inc."),
    ("COIN", "Coinbase Global Inc."),
    ("RBLX", "Roblox Corporation"),
    ("NET", "Cloudflare Inc."),
    ("SNAP", "Snap Inc."),
    ("ROKU", "Roku Inc."),
    ("PINS", "Pinterest Inc."),
    ("TWTR", "Twitter Inc."),
    ("SQ", "Block Inc."),
    ("SHOP", "Shopify Inc."),
    ("SNOW", "Snowflake Inc."),
    ("PLTR", "Palantir Technologies"),
    ("U", "Unity Software Inc."),
    ("TWLO", "Twilio Inc."),
    ("UBER", "Uber Technologies Inc."),
    ("LYFT", "Lyft Inc."),
    ("DASH", "DoorDash Inc."),
    ("ZI", "ZoomInfo Technologies"),
    ("MDB", "MongoDB Inc."),
    ("VEEV", "Veeva Systems Inc."),
    ("NOW", "ServiceNow Inc."),
    ("PANW", "Palo Alto Networks"),
    ("OKTA", "Okta Inc."),
    ("DOCU", "DocuSign Inc."),
    ("CRWD", "CrowdStrike Holdings"),
    ("ZS", "Zscaler Inc."),
    ("DDOG", "Datadog Inc."),
    ("NET", "Cloudflare Inc."),
    ("FSLY", "Fastly Inc."),
    ("ESTC", "Elastic N.V."),
    ("DOCN", "DigitalOcean Holdings"),
    ("GTLB", "GitLab Inc."),
    ("S", "SentinelOne Inc."),
    ("PATH", "UiPath Inc."),
    ("AI", "C3.ai Inc."),
    ("SMCI", "Super Micro Computer"),
    ("ENPH", "Enphase Energy Inc."),
    ("SEDG", "SolarEdge Technologies"),
    ("PLUG", "Plug Power Inc."),
    ("FSLR", "First Solar Inc."),
    ("RUN", "Sunrun Inc."),
    ("VRTX", "Vertex Pharmaceuticals"),
    ("BMRN", "BioMarin Pharmaceutical"),
    ("TECH", "Bio-Techne Corporation"),
    ("EXAS", "Exact Sciences Corporation"),
    ("VRTX", "Vertex Pharmaceuticals"),
    ("SIRI", "Sirius XM Holdings"),
    ("NCLH", "Norwegian Cruise Line"),
    ("CCL", "Carnival Corporation"),
    ("RCL", "Royal Caribbean Group"),
    ("WYNN", "Wynn Resorts Limited"),
    ("MGM", "MGM Resorts International"),
    ("BIDU", "Baidu Inc."),
    ("JD", "JD.com Inc."),
    ("NTES", "NetEase Inc."),
    ("BILI", "Bilibili Inc."),
    ("BABA", "Alibaba Group Holding"),
    ("PEP", "PepsiCo Inc."),
    ("KO", "The Coca-Cola Company"),
    ("WMT", "Walmart Inc."),
    ("COST", "Costco Wholesale"),
    ("HD", "The Home Depot"),
    ("AMGN", "Amgen Inc."),
    ("CVS", "CVS Health Corporation"),
    ("UNH", "UnitedHealth Group"),
    ("JNJ", "Johnson & Johnson"),
    ("PFE", "Pfizer Inc."),
    ("ABBV", "AbbVie Inc."),
    ("LLY", "Eli Lilly and Company"),
    ("TMO", "Thermo Fisher Scientific"),
    ("ABT", "Abbott Laboratories"),
    ("DHR", "Danaher Corporation"),
    ("BMY", "Bristol-Myers Squibb"),
    ("MRK", "Merck & Co. Inc."),
    ("AMGN", "Amgen Inc."),
    ("GILD", "Gilead Sciences Inc."),
    ("VRTX", "Vertex Pharmaceuticals"),
    ("BIIB", "Biogen Inc."),
    ("REGN", "Regeneron Pharmaceuticals"),
    ("CELG", "Celgene Corporation"),
    ("INCY", "Incyte Corporation"),
    ("ALXN", "Alexion Pharmaceuticals"),
    ("BMRN", "BioMarin Pharmaceutical"),
    ("TECH", "Bio-Techne Corporation"),
    ("EXAS", "Exact Sciences Corporation"),
    ("HOLX", "Hologic Inc."),
    ("DXCM", "DexCom Inc."),
    ("ISRG", "Intuitive Surgical Inc."),
    ("SYK", "Stryker Corporation"),
    ("BSX", "Boston Scientific"),
    ("MDLZ", "Mondelez International"),
    ("KHC", "The Kraft Heinz Company"),
    ("GIS", "General Mills Inc."),
    ("K", "Kellogg Company"),
    ("CAG", "Conagra Brands Inc."),
    ("CPB", "Campbell Soup Company"),
    ("HSY", "The Hershey Company"),
    ("MKC", "McCormick & Company"),
    ("SJM", "The J.M. Smucker Company"),
    ("HRL", "Hormel Foods Corporation"),
    ("TSN", "Tyson Foods Inc."),
    ("TAP", "Molson Coors Beverage"),
    ("STZ", "Constellation Brands"),
    ("DEO", "Diageo plc"),
    ("BF.B", "Brown-Forman Corporation"),
    ("KDP", "Keurig Dr Pepper Inc."),
    ("CCEP", "Coca-Cola Europacific"),
    ("MNST", "Monster Beverage Corporation"),
    ("CELH", "Celsius Holdings Inc."),
    ("FIZZ", "National Beverage Corp."),
    ("COKE", "Coca-Cola Consolidated"),
    ("DPS", "Dr Pepper Snapple Group"),
    ("FMX", "Fomento Económico Mexicano"),
    ("KOF", "Coca-Cola FEMSA S.A.B."),
    ("SBUX", "Starbucks Corporation"),
    ("MCD", "McDonald's Corporation"),
    ("YUM", "Yum! Brands Inc."),
    ("QSR", "Restaurant Brands Intl"),
    ("CMG", "Chipotle Mexican Grill"),
    ("SBUX", "Starbucks Corporation")
]

def add_stocks_to_database():
    """Add the top NASDAQ stocks to the database"""
    try:
        logger.info("Initializing stock data service...")
        stock_service = StockDataService(DB_CONFIG)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_stocks = []
        for symbol, name in TOP_NASDAQ_STOCKS:
            if symbol not in seen:
                seen.add(symbol)
                unique_stocks.append((symbol, name))
        
        logger.info(f"Adding {len(unique_stocks)} unique NASDAQ stocks...")
        
        successful = 0
        failed = 0
        
        for i, (symbol, name) in enumerate(unique_stocks, 1):
            try:
                logger.info(f"[{i}/{len(unique_stocks)}] Processing {symbol} ({name})...")
                
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
                
                # Add small delay to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                failed += 1
                logger.error(f"❌ Error processing {symbol}: {e}")
                continue
        
        logger.info(f"")
        logger.info(f"{'='*60}")
        logger.info(f"SUMMARY:")
        logger.info(f"{'='*60}")
        logger.info(f"Total stocks processed: {len(unique_stocks)}")
        logger.info(f"Successfully added: {successful}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Success rate: {(successful/len(unique_stocks)*100):.1f}%")
        
        return successful, failed
        
    except Exception as e:
        logger.error(f"Error in main process: {e}")
        return 0, len(unique_stocks)

def main():
    """Main function"""
    try:
        logger.info("🚀 Starting Top 200 NASDAQ stocks addition process...")
        logger.info("This will fetch historical data for each stock, which may take a while...")
        
        successful, failed = add_stocks_to_database()
        
        if successful > 0:
            logger.info(f"🎉 Process completed! Added {successful} stocks successfully.")
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