"""
Cryptocurrency Data Service - Binance API Integration

This service is designed to work optimally with both public API and authenticated API access.

CURRENT STATUS: Using Public API (1200 requests/minute)

UPGRADING TO API KEY (5x faster collection):
1. Get your Binance API key: https://www.binance.com/en/my/settings/api-management
2. Security: ONLY enable "Enable Reading" permission (no trading needed)
3. Add to .env file:
   BINANCE_API_KEY=your_api_key_here
   BINANCE_SECRET_KEY=your_secret_key_here
4. Restart containers: docker compose down && docker compose up -d
5. Collection will automatically use 6000 requests/minute (5x faster)

The code is fully prepared for API key usage - no code changes needed!
"""

import requests
import pandas as pd
import time
import hashlib
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import psycopg
from psycopg.rows import dict_row
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CryptoDataService:
    def __init__(self, db_config=None, binance_api_key=None, binance_secret_key=None):
        """
        Initialize the Crypto Data Service
        
        Args:
            db_config: Database configuration dict
            binance_api_key: Binance API key (optional, for higher rate limits)
            binance_secret_key: Binance secret key (optional, for private endpoints)
        """
        # Database configuration
        if db_config is None:
            db_config = {
                'host': os.getenv('DB_HOST', 'database'),
                'dbname': os.getenv('DB_NAME', 'webapp_db'),
                'user': os.getenv('DB_USER', 'root'),
                'password': os.getenv('DB_PASSWORD', '530NWC0Gm3pt4O'),
                'port': os.getenv('DB_PORT', 5432)
            }
        
        self.db_config = db_config
        self.binance_api_key = binance_api_key
        self.binance_secret_key = binance_secret_key
        
        # Binance API endpoints
        self.base_url = "https://api.binance.com"
        self.api_v3 = f"{self.base_url}/api/v3"
        
        # Rate limiting - optimized for API key when available
        if binance_api_key:
            self.requests_per_minute = 6000  # 5x higher with API key
            logger.info("Using Binance API key - Higher rate limits enabled (6000/min)")
        else:
            self.requests_per_minute = 1200  # Public API limit
            logger.info("Using public API - Standard rate limits (1200/min)")
            
        self.last_request_time = 0
        self.request_count = 0
        self.rate_limit_window = 60  # 1 minute
        
        # Rate limiting
        self.requests_per_minute = 6000 if binance_api_key else 1200  # 5x higher with API key
        self.last_request_time = 0
        self.request_count = 0
        self.rate_limit_window = 60  # 1 minute
        
        # Initialize data source
        self._initialize_data_source()
        
        # Calculate optimal delay between requests for public API
        if not binance_api_key:
            # For public API, be more conservative to avoid rate limiting
            self.min_delay_between_requests = 0.5  # 500ms between requests
        else:
            self.min_delay_between_requests = 0.1  # 100ms with API key
        
        logger.info("Initialized crypto data service")

    def _get_db_connection(self):
        """Get database connection"""
        return psycopg.connect(**self.db_config)

    def _initialize_data_source(self):
        """Initialize or update the Binance data source in database"""
        try:
            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Check if Binance source exists
                    cur.execute("SELECT id FROM crypto_data_sources WHERE source_name = 'Binance'")
                    result = cur.fetchone()
                    
                    if result:
                        self.data_source_id = result[0]
                        # Update API key hash if provided
                        if self.binance_api_key:
                            api_key_hash = hashlib.sha256(self.binance_api_key.encode()).hexdigest()
                            cur.execute(
                                "UPDATE crypto_data_sources SET api_key_hash = %s, updated_at = %s WHERE id = %s",
                                (api_key_hash, datetime.now(), self.data_source_id)
                            )
                    else:
                        # Create new data source
                        api_key_hash = None
                        if self.binance_api_key:
                            api_key_hash = hashlib.sha256(self.binance_api_key.encode()).hexdigest()
                        
                        cur.execute("""
                            INSERT INTO crypto_data_sources (source_name, api_endpoint, api_key_hash, rate_limit_per_minute)
                            VALUES (%s, %s, %s, %s) RETURNING id
                        """, ('Binance', self.api_v3, api_key_hash, self.requests_per_minute))
                        
                        self.data_source_id = cur.fetchone()[0]
                    
                    conn.commit()
                    logger.info(f"Initialized data source with ID: {self.data_source_id}")
                    
        except Exception as e:
            logger.error(f"Error initializing data source: {e}")
            raise

    def _rate_limit_check(self):
        """Check and enforce rate limiting"""
        current_time = time.time()
        
        # Reset counter if window has passed
        if current_time - self.last_request_time > self.rate_limit_window:
            self.request_count = 0
            self.last_request_time = current_time
        
        # Check if we're at the limit
        if self.request_count >= self.requests_per_minute:
            sleep_time = self.rate_limit_window - (current_time - self.last_request_time)
            if sleep_time > 0:
                logger.info(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
                self.request_count = 0
                self.last_request_time = time.time()
        
        self.request_count += 1

    def _make_binance_request(self, endpoint: str, params: dict = None) -> dict:
        """Make a request to Binance API with rate limiting"""
        self._rate_limit_check()
        
        headers = {}
        if self.binance_api_key:
            headers['X-MBX-APIKEY'] = self.binance_api_key
        
        try:
            response = requests.get(f"{self.api_v3}/{endpoint}", params=params, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Binance API request failed: {e}")
            raise

    def get_exchange_info(self) -> dict:
        """Get exchange information including all trading pairs"""
        try:
            return self._make_binance_request("exchangeInfo")
        except Exception as e:
            logger.error(f"Failed to get exchange info: {e}")
            raise

    def get_top_cryptocurrencies(self, limit: int = 200) -> List[Dict]:
        """
        Get top cryptocurrencies by 24h volume from Binance
        
        Args:
            limit: Number of cryptocurrencies to return
            
        Returns:
            List of cryptocurrency data dicts
        """
        try:
            # Get 24hr ticker statistics
            ticker_data = self._make_binance_request("ticker/24hr")
            
            # Filter USDT pairs and sort by volume
            usdt_pairs = [
                ticker for ticker in ticker_data 
                if ticker['symbol'].endswith('USDT') and 
                float(ticker['quoteVolume']) > 0
            ]
            
            # Sort by 24h volume (quote volume)
            usdt_pairs.sort(key=lambda x: float(x['quoteVolume']), reverse=True)
            
            # Take top N
            top_pairs = usdt_pairs[:limit]
            
            result = []
            for i, ticker in enumerate(top_pairs):
                symbol = ticker['symbol']
                base_asset = symbol.replace('USDT', '')
                
                result.append({
                    'symbol': symbol,
                    'base_asset': base_asset,
                    'quote_asset': 'USDT',
                    'binance_symbol': symbol,
                    'rank_position': i + 1,
                    'current_price': float(ticker['lastPrice']),
                    'price_change_24h': float(ticker['priceChange']),
                    'price_change_percent_24h': float(ticker['priceChangePercent']),
                    'volume_24h': float(ticker['volume']),
                    'quote_volume_24h': float(ticker['quoteVolume']),
                    'high_24h': float(ticker['highPrice']),
                    'low_24h': float(ticker['lowPrice']),
                    'count': int(ticker['count'])
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get top cryptocurrencies: {e}")
            raise

    def get_historical_klines(self, symbol: str, interval: str = '1h', 
                            start_time: datetime = None, end_time: datetime = None,
                            limit: int = 1000) -> pd.DataFrame:
        """
        Get historical kline/candlestick data from Binance
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            interval: Kline interval (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
            start_time: Start time for data
            end_time: End time for data
            limit: Number of records to return (max 1000)
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            params = {
                'symbol': symbol.upper(),
                'interval': interval,
                'limit': limit
            }
            
            if start_time:
                params['startTime'] = int(start_time.timestamp() * 1000)
            if end_time:
                params['endTime'] = int(end_time.timestamp() * 1000)
            
            klines = self._make_binance_request("klines", params)
            
            if not klines:
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(klines, columns=[
                'open_time', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # Convert timestamps
            df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
            df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
            
            # Convert numeric columns
            numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'quote_asset_volume',
                             'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col])
            
            # Remove the 'ignore' column
            df = df.drop('ignore', axis=1)
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to get historical klines for {symbol}: {e}")
            raise

    def fetch_historical_data_paginated(self, symbol: str, interval: str = '1h', 
                                      years_back: int = 5) -> pd.DataFrame:
        """
        Fetch historical data for a longer period by paginating through API calls
        
        Args:
            symbol: Trading pair symbol
            interval: Kline interval
            years_back: Number of years of data to fetch
            
        Returns:
            DataFrame with complete historical data
        """
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(days=years_back * 365)
            
            all_data = []
            current_start = start_time
            
            logger.info(f"Fetching {years_back} years of {interval} data for {symbol}")
            
            while current_start < end_time:
                # Calculate batch end time (1000 intervals per request)
                if interval == '1h':
                    batch_end = current_start + timedelta(hours=1000)
                elif interval == '1d':
                    batch_end = current_start + timedelta(days=1000)
                elif interval == '1m':
                    batch_end = current_start + timedelta(minutes=1000)
                elif interval == '4h':
                    batch_end = current_start + timedelta(hours=4000)
                else:
                    # Default: assume hourly
                    batch_end = current_start + timedelta(hours=1000)
                
                if batch_end > end_time:
                    batch_end = end_time
                
                # Fetch batch
                batch_data = self.get_historical_klines(
                    symbol=symbol,
                    interval=interval,
                    start_time=current_start,
                    end_time=batch_end,
                    limit=1000
                )
                
                if not batch_data.empty:
                    all_data.append(batch_data)
                    current_start = batch_data['close_time'].max() + timedelta(seconds=1)
                    logger.info(f"Fetched batch: {len(batch_data)} records, up to {current_start}")
                else:
                    # No more data available
                    break
                
                # Adaptive delay based on API key availability
                time.sleep(self.min_delay_between_requests)
            
            if all_data:
                result_df = pd.concat(all_data, ignore_index=True)
                result_df = result_df.drop_duplicates(subset=['open_time']).sort_values('open_time')
                logger.info(f"Total {symbol} records fetched: {len(result_df)}")
                return result_df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Failed to fetch paginated historical data for {symbol}: {e}")
            raise

    def store_crypto_data(self, crypto_id: int, df: pd.DataFrame, interval_type: str) -> int:
        """
        Store cryptocurrency price data in database
        
        Args:
            crypto_id: Cryptocurrency ID from database
            df: DataFrame with price data
            interval_type: Interval type (1h, 1d, etc.)
            
        Returns:
            Number of records stored
        """
        if df.empty:
            return 0
        
        try:
            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    records_stored = 0
                    
                    for _, row in df.iterrows():
                        try:
                            cur.execute("""
                                INSERT INTO crypto_prices 
                                (crypto_id, datetime, open_price, high_price, low_price, close_price, 
                                 volume, quote_asset_volume, number_of_trades, taker_buy_base_asset_volume, 
                                 taker_buy_quote_asset_volume, interval_type)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (crypto_id, datetime, interval_type) DO UPDATE SET
                                    open_price = EXCLUDED.open_price,
                                    high_price = EXCLUDED.high_price,
                                    low_price = EXCLUDED.low_price,
                                    close_price = EXCLUDED.close_price,
                                    volume = EXCLUDED.volume,
                                    quote_asset_volume = EXCLUDED.quote_asset_volume,
                                    number_of_trades = EXCLUDED.number_of_trades,
                                    taker_buy_base_asset_volume = EXCLUDED.taker_buy_base_asset_volume,
                                    taker_buy_quote_asset_volume = EXCLUDED.taker_buy_quote_asset_volume
                            """, (
                                crypto_id, row['open_time'], row['open'], row['high'], row['low'], row['close'],
                                row['volume'], row['quote_asset_volume'], row['number_of_trades'],
                                row['taker_buy_base_asset_volume'], row['taker_buy_quote_asset_volume'], interval_type
                            ))
                            records_stored += 1
                        except Exception as e:
                            logger.warning(f"Failed to store record: {e}")
                    
                    conn.commit()
                    logger.info(f"Stored {records_stored} price records for crypto ID {crypto_id}")
                    return records_stored
                    
        except Exception as e:
            logger.error(f"Error storing crypto data: {e}")
            raise

    def get_or_create_cryptocurrency(self, symbol_data: dict) -> int:
        """
        Get existing cryptocurrency ID or create new one
        
        Args:
            symbol_data: Dict with cryptocurrency information
            
        Returns:
            Cryptocurrency ID
        """
        try:
            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Check if crypto exists
                    cur.execute("SELECT id FROM cryptocurrencies WHERE binance_symbol = %s", (symbol_data['binance_symbol'],))
                    result = cur.fetchone()
                    
                    if result:
                        return result[0]
                    else:
                        # Create new cryptocurrency
                        cur.execute("""
                            INSERT INTO cryptocurrencies (symbol, name, base_asset, quote_asset, binance_symbol, rank_position)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            RETURNING id
                        """, (
                            symbol_data['symbol'],
                            symbol_data.get('name', symbol_data['base_asset']),
                            symbol_data['base_asset'],
                            symbol_data['quote_asset'],
                            symbol_data['binance_symbol'],
                            symbol_data.get('rank_position', None)
                        ))
                        
                        crypto_id = cur.fetchone()[0]
                        conn.commit()
                        logger.info(f"Created new cryptocurrency: {symbol_data['symbol']} with ID {crypto_id}")
                        return crypto_id
                        
        except Exception as e:
            logger.error(f"Error getting/creating cryptocurrency: {e}")
            raise

    def update_market_stats(self, crypto_id: int, market_data: dict):
        """Update current market statistics for a cryptocurrency"""
        try:
            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO crypto_market_stats 
                        (crypto_id, current_price, price_change_24h, price_change_percent_24h,
                         volume_24h, high_24h, low_24h, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (crypto_id) DO UPDATE SET
                            current_price = EXCLUDED.current_price,
                            price_change_24h = EXCLUDED.price_change_24h,
                            price_change_percent_24h = EXCLUDED.price_change_percent_24h,
                            volume_24h = EXCLUDED.volume_24h,
                            high_24h = EXCLUDED.high_24h,
                            low_24h = EXCLUDED.low_24h,
                            updated_at = EXCLUDED.updated_at
                    """, (
                        crypto_id,
                        market_data.get('current_price'),
                        market_data.get('price_change_24h'),
                        market_data.get('price_change_percent_24h'),
                        market_data.get('volume_24h'),
                        market_data.get('high_24h'),
                        market_data.get('low_24h'),
                        datetime.now()
                    ))
                    conn.commit()
                    
        except Exception as e:
            logger.error(f"Error updating market stats: {e}")
            raise

    def log_fetch_operation(self, crypto_id: int, interval_type: str, records_fetched: int, 
                          start_time: datetime = None, end_time: datetime = None, 
                          status: str = 'success', error_message: str = None):
        """Log data fetch operation"""
        try:
            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO crypto_fetch_logs 
                        (crypto_id, data_source_id, fetch_start, fetch_end, records_fetched,
                         interval_type, start_time, end_time, status, error_message)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        crypto_id, self.data_source_id, datetime.now(), datetime.now(),
                        records_fetched, interval_type, start_time, end_time, status, error_message
                    ))
                    conn.commit()
                    
        except Exception as e:
            logger.error(f"Error logging fetch operation: {e}")

    def get_configuration_info(self):
        """Get current configuration information"""
        return {
            'api_key_configured': bool(self.binance_api_key),
            'rate_limit_per_minute': self.requests_per_minute,
            'min_delay_between_requests': getattr(self, 'min_delay_between_requests', 0.1),
            'data_source_id': self.data_source_id,
            'performance_tier': 'Premium (API Key)' if self.binance_api_key else 'Standard (Public API)',
            'upgrade_available': not bool(self.binance_api_key),
            'upgrade_instructions': {
                'step1': 'Get API key from https://www.binance.com/en/my/settings/api-management',
                'step2': 'Enable only "Enable Reading" permission (no trading)',
                'step3': 'Add BINANCE_API_KEY and BINANCE_SECRET_KEY to .env file', 
                'step4': 'Restart containers: docker compose down && docker compose up -d',
                'benefit': '5x faster data collection (6000 vs 1200 requests/minute)'
            } if not self.binance_api_key else None
        }

if __name__ == "__main__":
    # Test the service
    service = CryptoDataService()
    
    # Test getting top cryptocurrencies
    top_cryptos = service.get_top_cryptocurrencies(10)
    for crypto in top_cryptos:
        print(f"{crypto['symbol']}: ${crypto['current_price']:.2f} ({crypto['price_change_percent_24h']:.2f}%)")