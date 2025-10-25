#!/usr/bin/env python3
"""
Cryptocurrency Data Collection Script
Fetches 5 years of hourly data for top 200 cryptocurrencies from Binance
"""

import sys
import os
import time
from datetime import datetime, timedelta
import logging
from crypto_service import CryptoDataService
import json

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/crypto_collection.log')
    ]
)
logger = logging.getLogger(__name__)

# Progress file
PROGRESS_FILE = '/tmp/crypto_collection_progress.json'

def load_progress():
    """Load collection progress from file"""
    try:
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load progress file: {e}")
    
    return {
        'processed_symbols': [],
        'failed_symbols': [],
        'last_updated': None,
        'total_processed': 0,
        'total_failed': 0
    }

def save_progress(progress):
    """Save collection progress to file"""
    try:
        progress['last_updated'] = datetime.now().isoformat()
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(progress, f, indent=2)
    except Exception as e:
        logger.error(f"Could not save progress: {e}")

def collect_crypto_data():
    """Main collection function"""
    logger.info("🚀 Starting Cryptocurrency Data Collection...")
    logger.info("This will fetch 5 years of hourly data for top 200 cryptocurrencies")
    logger.info("Process supports resuming from interruptions...")
    
    # Get Binance API credentials from environment if available
    api_key = os.getenv('BINANCE_API_KEY')
    secret_key = os.getenv('BINANCE_SECRET_KEY')
    
    if api_key:
        logger.info("✅ Using Binance API key for higher rate limits (6000/min)")
    else:
        logger.info("📝 Using public API (1200/min)")
        logger.info("💡 TIP: Add BINANCE_API_KEY to .env file for 5x faster collection!")
        logger.info("   Get your key at: https://www.binance.com/en/my/settings/api-management")
    
    try:
        # Initialize service
        logger.info("Initializing crypto data service...")
        service = CryptoDataService(binance_api_key=api_key, binance_secret_key=secret_key)
        
        # Load progress
        progress = load_progress()
        logger.info(f"Loaded progress: {progress['total_processed']} processed, {progress['total_failed']} failed")
        
        # Get top cryptocurrencies
        logger.info("Fetching top 200 cryptocurrencies by volume...")
        top_cryptos = service.get_top_cryptocurrencies(200)
        logger.info(f"Found {len(top_cryptos)} cryptocurrencies to process")
        
        # Filter out already processed
        remaining_cryptos = [
            crypto for crypto in top_cryptos 
            if crypto['binance_symbol'] not in progress['processed_symbols'] and
               crypto['binance_symbol'] not in progress['failed_symbols']
        ]
        
        logger.info(f"Processing {len(remaining_cryptos)} remaining cryptocurrencies...")
        
        for i, crypto_data in enumerate(remaining_cryptos):
            symbol = crypto_data['binance_symbol']
            logger.info(f"[{i+1}/{len(remaining_cryptos)}] Processing {symbol} ({crypto_data['base_asset']})...")
            
            try:
                # Get or create cryptocurrency record
                crypto_id = service.get_or_create_cryptocurrency(crypto_data)
                
                # Update market stats
                service.update_market_stats(crypto_id, crypto_data)
                
                # Fetch 5 years of hourly historical data
                logger.info(f"Fetching 5 years of hourly data for {symbol}...")
                df = service.fetch_historical_data_paginated(
                    symbol=symbol,
                    interval='1h',
                    years_back=5
                )
                
                if not df.empty:
                    # Store the data
                    records_stored = service.store_crypto_data(crypto_id, df, '1h')
                    
                    # Log the operation
                    service.log_fetch_operation(
                        crypto_id=crypto_id,
                        interval_type='1h',
                        records_fetched=records_stored,
                        start_time=df['open_time'].min(),
                        end_time=df['open_time'].max(),
                        status='success'
                    )
                    
                    logger.info(f"✅ Successfully processed {symbol} - {records_stored} hourly records")
                    progress['processed_symbols'].append(symbol)
                    progress['total_processed'] += 1
                    
                else:
                    logger.warning(f"⚠️ No data returned for {symbol}")
                    progress['failed_symbols'].append(symbol)
                    progress['total_failed'] += 1
                    
                    # Log the failure
                    service.log_fetch_operation(
                        crypto_id=crypto_id,
                        interval_type='1h',
                        records_fetched=0,
                        status='error',
                        error_message='No data returned from API'
                    )
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"❌ Failed to process {symbol}: {error_msg}")
                progress['failed_symbols'].append(symbol)
                progress['total_failed'] += 1
                
                # Try to log the failure if we have crypto_id
                try:
                    crypto_id = service.get_or_create_cryptocurrency(crypto_data)
                    service.log_fetch_operation(
                        crypto_id=crypto_id,
                        interval_type='1h',
                        records_fetched=0,
                        status='error',
                        error_message=error_msg
                    )
                except:
                    pass
            
            # Save progress after each crypto
            save_progress(progress)
            logger.info(f"Progress: {progress['total_processed']} successful, {progress['total_failed']} failed, {len(remaining_cryptos) - i - 1} remaining")
            
            # Small delay to be nice to API
            time.sleep(1)
        
        # Final summary
        total_attempted = progress['total_processed'] + progress['total_failed']
        success_rate = (progress['total_processed'] / total_attempted * 100) if total_attempted > 0 else 0
        
        logger.info("🎉 Cryptocurrency data collection completed!")
        logger.info(f"📊 Summary:")
        logger.info(f"   • Total processed: {progress['total_processed']}")
        logger.info(f"   • Total failed: {progress['total_failed']}")
        logger.info(f"   • Success rate: {success_rate:.1f}%")
        
        if progress['failed_symbols']:
            logger.info(f"❌ Failed symbols: {', '.join(progress['failed_symbols'][:10])}{'...' if len(progress['failed_symbols']) > 10 else ''}")
        
    except KeyboardInterrupt:
        logger.info("Collection interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Collection failed with error: {e}")
        return 1
    
    return 0

def update_crypto_data():
    """Update existing crypto data with latest prices"""
    logger.info("🔄 Starting Cryptocurrency Data Update...")
    
    api_key = os.getenv('BINANCE_API_KEY')
    secret_key = os.getenv('BINANCE_SECRET_KEY')
    
    try:
        service = CryptoDataService(binance_api_key=api_key, binance_secret_key=secret_key)
        
        # Get top cryptocurrencies for current market data
        top_cryptos = service.get_top_cryptocurrencies(200)
        
        updated_count = 0
        for crypto_data in top_cryptos:
            try:
                crypto_id = service.get_or_create_cryptocurrency(crypto_data)
                service.update_market_stats(crypto_id, crypto_data)
                
                # Fetch latest hourly data (last 24 hours)
                end_time = datetime.now()
                start_time = end_time - timedelta(hours=24)
                
                df = service.get_historical_klines(
                    symbol=crypto_data['binance_symbol'],
                    interval='1h',
                    start_time=start_time,
                    end_time=end_time
                )
                
                if not df.empty:
                    records_stored = service.store_crypto_data(crypto_id, df, '1h')
                    if records_stored > 0:
                        updated_count += 1
                        
                        # Invalidate backtest cache for this crypto
                        try:
                            from cache_service import get_cache_service
                            cache = get_cache_service()
                            if cache and cache.enabled:
                                pattern = f"backtest:*:{crypto_id}:*"
                                keys = cache.redis_client.keys(pattern)
                                if keys:
                                    cache.redis_client.delete(*keys)
                                    logger.info(f"🗑️ Invalidated {len(keys)} cache entries for crypto {crypto_id}")
                        except Exception as e:
                            logger.warning(f"Cache invalidation failed: {e}")
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                logger.warning(f"Failed to update {crypto_data['binance_symbol']}: {e}")
        
        logger.info(f"✅ Updated {updated_count} cryptocurrencies")
        
        # Refresh dashboard materialized view after update
        if updated_count > 0:
            try:
                import psycopg
                db_config = {
                    'host': os.getenv('DB_HOST', 'database'),
                    'dbname': os.getenv('DB_NAME', 'webapp_db'),
                    'user': os.getenv('DB_USER', 'root'),
                    'password': os.getenv('DB_PASSWORD', '530NWC0Gm3pt4O'),
                    'port': os.getenv('DB_PORT', 5432)
                }
                conn = psycopg.connect(**db_config)
                cur = conn.cursor()
                cur.execute("SELECT refresh_crypto_dashboard();")
                conn.commit()
                cur.close()
                conn.close()
                logger.info("📊 Dashboard summary refreshed")
            except Exception as e:
                logger.warning(f"Dashboard refresh failed: {e}")
            
            # Calculate technical indicators for updated cryptos
            try:
                from technical_indicators_service import TechnicalIndicatorsService
                indicators_service = TechnicalIndicatorsService()
                
                # Get list of updated crypto IDs
                conn = psycopg.connect(**db_config)
                cur = conn.cursor()
                cur.execute("""
                    SELECT DISTINCT crypto_id 
                    FROM crypto_prices 
                    WHERE datetime >= NOW() - INTERVAL '2 hours'
                    ORDER BY crypto_id
                """)
                updated_crypto_ids = [row[0] for row in cur.fetchall()]
                cur.close()
                conn.close()
                
                # Calculate indicators for updated cryptos
                logger.info(f"📊 Calculating indicators for {len(updated_crypto_ids)} updated cryptos...")
                for crypto_id in updated_crypto_ids:
                    try:
                        # Calculate only for recent data (last 7 days + 200 for warmup)
                        start_date = datetime.now() - timedelta(days=207)
                        indicators_service.calculate_and_store_indicators(
                            crypto_id, 
                            start_date=start_date.strftime('%Y-%m-%d')
                        )
                    except Exception as e:
                        logger.warning(f"Indicator calculation failed for crypto {crypto_id}: {e}")
                
                logger.info("✅ Technical indicators updated")
            except Exception as e:
                logger.warning(f"Indicator calculation failed: {e}")
        
    except Exception as e:
        logger.error(f"Update failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "update":
        exit_code = update_crypto_data()
    else:
        exit_code = collect_crypto_data()
    
    sys.exit(exit_code)