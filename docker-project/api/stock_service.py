"""
Stock Data Service for fetching and storing historical stock prices
"""
import yfinance as yf
import pandas as pd
import numpy as np
import psycopg
from psycopg.rows import dict_row
from datetime import datetime, timedelta
import pytz
import schedule
import time
import threading
import logging
import requests
import json
import os
from typing import Optional, List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiSourceDataFetcher:
    """Fetches stock data from multiple sources with fallback mechanism"""
    
    def __init__(self):
        # API configuration from environment variables
        self.alpha_vantage_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
        self.finnhub_key = os.environ.get('FINNHUB_API_KEY')
        self.iex_cloud_key = os.environ.get('IEX_CLOUD_API_KEY')
        
        # Simple rate limiting - just track last request
        self.last_request_time = {}
        self.min_interval = 1  # 1 second between requests
        
    def _wait_for_rate_limit(self, source: str):
        """Simple rate limiting - wait 1 second minimum between requests"""
        if source in self.last_request_time:
            elapsed = time.time() - self.last_request_time[source]
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
        self.last_request_time[source] = time.time()
    
    def fetch_from_alpha_vantage(self, symbol: str, interval: str = "1h") -> Optional[pd.DataFrame]:
        """Fetch data from Alpha Vantage API - SINGLE ATTEMPT"""
        if not self.alpha_vantage_key:
            logger.info("Alpha Vantage API key not configured")
            return None
            
        try:
            self._wait_for_rate_limit('alpha_vantage')
            
            # Map our intervals to Alpha Vantage intervals
            av_interval = "60min" if interval == "1h" else "daily"
            function = "TIME_SERIES_INTRADAY" if interval == "1h" else "TIME_SERIES_DAILY"
            
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': function,
                'symbol': symbol,
                'apikey': self.alpha_vantage_key,
                'outputsize': 'full'
            }
            
            if interval == "1h":
                params['interval'] = av_interval
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API limit message
            if 'Error Message' in data or 'Note' in data:
                logger.info(f"Alpha Vantage API limit/error for {symbol}")
                return None
                
            # Extract time series data
            ts_key = next((k for k in data.keys() if 'Time Series' in k), None)
            if not ts_key or ts_key not in data:
                logger.info(f"No time series data found for {symbol} from Alpha Vantage")
                return None
                
            ts_data = data[ts_key]
            
            # Convert to DataFrame
            df_data = []
            for timestamp, values in ts_data.items():
                df_data.append({
                    'datetime': pd.to_datetime(timestamp),
                    'Open': float(values.get('1. open', 0)),
                    'High': float(values.get('2. high', 0)),
                    'Low': float(values.get('3. low', 0)),
                    'Close': float(values.get('4. close', 0)),
                    'Volume': int(values.get('5. volume', 0))
                })
            
            if not df_data:
                return None
                
            df = pd.DataFrame(df_data)
            df.set_index('datetime', inplace=True)
            df.sort_index(inplace=True)
            
            return df
            
        except Exception as e:
            logger.info(f"Alpha Vantage failed for {symbol}: {e}")
            return None
    
    def fetch_from_finnhub(self, symbol: str, interval: str = "1h") -> Optional[pd.DataFrame]:
        """Fetch data from Finnhub API - SINGLE ATTEMPT"""
        if not self.finnhub_key:
            logger.info("Finnhub API key not configured")
            return None
            
        try:
            self._wait_for_rate_limit('finnhub')
            
            # Finnhub uses different resolution codes
            resolution = "60" if interval == "1h" else "D"
            
            # Get data for last 30 days for hourly, 1 year for daily
            end_time = int(time.time())
            if interval == "1h":
                start_time = end_time - (30 * 24 * 60 * 60)  # 30 days
            else:
                start_time = end_time - (365 * 24 * 60 * 60)  # 1 year
            
            url = f"https://finnhub.io/api/v1/stock/candle"
            params = {
                'symbol': symbol,
                'resolution': resolution,
                'from': start_time,
                'to': end_time,
                'token': self.finnhub_key
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('s') != 'ok':
                logger.info(f"Finnhub error for {symbol}")
                return None
                
            # Convert to DataFrame
            df = pd.DataFrame({
                'datetime': pd.to_datetime(data['t'], unit='s'),
                'Open': data['o'],
                'High': data['h'],
                'Low': data['l'],
                'Close': data['c'],
                'Volume': data['v']
            })
            
            df.set_index('datetime', inplace=True)
            df.sort_index(inplace=True)
            
            return df
            
        except Exception as e:
            logger.info(f"Finnhub failed for {symbol}: {e}")
            return None
    
    def fetch_from_twelve_data(self, symbol: str, interval: str = "1h") -> Optional[pd.DataFrame]:
        """Fetch data from Twelve Data API - SINGLE ATTEMPT"""
        try:
            self._wait_for_rate_limit('twelve_data')
            
            # Map intervals
            td_interval = "1h" if interval == "1h" else "1day"
            
            # Free tier endpoint
            url = f"https://api.twelvedata.com/time_series"
            params = {
                'symbol': symbol,
                'interval': td_interval,
                'outputsize': '100',  # Free tier limit
                'format': 'JSON'
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'values' in data and data['values']:
                    df_data = []
                    for point in data['values']:
                        try:
                            df_data.append({
                                'datetime': pd.to_datetime(point['datetime']),
                                'Open': float(point['open']),
                                'High': float(point['high']),
                                'Low': float(point['low']),
                                'Close': float(point['close']),
                                'Volume': int(point.get('volume', 0))
                            })
                        except (ValueError, KeyError):
                            continue
                    
                    if df_data:
                        df = pd.DataFrame(df_data)
                        df.set_index('datetime', inplace=True)
                        df.sort_index(inplace=True)
                        return df
                        
        except Exception as e:
            logger.info(f"Twelve Data failed for {symbol}: {e}")
        
        return None



    def fetch_from_iex_cloud(self, symbol: str, interval: str = "1h") -> Optional[pd.DataFrame]:
        """Fetch data from IEX Cloud API - SINGLE ATTEMPT"""
        if not self.iex_cloud_key:
            logger.info("IEX Cloud API key not configured")
            return None
            
        try:
            self._wait_for_rate_limit('iex_cloud')
            
            # IEX Cloud chart range
            chart_range = "1m" if interval == "1h" else "1y"
            
            url = f"https://cloud.iexapis.com/stable/stock/{symbol}/chart/{chart_range}"
            params = {
                'token': self.iex_cloud_key,
                'includeToday': 'true'
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                return None
                
            # Convert to DataFrame
            df_data = []
            for point in data:
                # Combine date and time if available
                if 'minute' in point:
                    dt_str = f"{point['date']} {point['minute']}"
                    dt = pd.to_datetime(dt_str)
                else:
                    dt = pd.to_datetime(point['date'])
                    
                df_data.append({
                    'datetime': dt,
                    'Open': point.get('open', point.get('close', 0)),
                    'High': point.get('high', point.get('close', 0)),
                    'Low': point.get('low', point.get('close', 0)),
                    'Close': point.get('close', 0),
                    'Volume': point.get('volume', 0)
                })
            
            df = pd.DataFrame(df_data)
            df.set_index('datetime', inplace=True)
            df.sort_index(inplace=True)
            
            return df
            
        except Exception as e:
            logger.info(f"IEX Cloud failed for {symbol}: {e}")
            return None

class StockDataService:
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.data_source_id = None
        self.multi_fetcher = MultiSourceDataFetcher()
        self.initialize_data_source()
    
    def get_connection(self):
        """Get database connection"""
        return psycopg.connect(**self.db_config)
    
    def initialize_data_source(self):
        """Initialize or get Yahoo Finance data source ID"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            # Get or create Yahoo Finance data source
            cur.execute("""
                SELECT id FROM data_sources WHERE source_name = 'Yahoo Finance'
            """)
            result = cur.fetchone()
            
            if result:
                self.data_source_id = result[0]
            else:
                cur.execute("""
                    INSERT INTO data_sources (source_name, api_endpoint, status)
                    VALUES ('Yahoo Finance', 'https://query1.finance.yahoo.com/v8/finance/chart/', 'active')
                    RETURNING id
                """)
                self.data_source_id = cur.fetchone()[0]
                conn.commit()
            
            logger.info(f"Initialized data source with ID: {self.data_source_id}")
            
        except Exception as e:
            logger.error(f"Error initializing data source: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def get_or_create_stock(self, symbol: str, name: str = None, exchange: str = 'NASDAQ') -> Optional[int]:
        """Get existing stock or create new one"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            # Check if stock exists
            cur.execute("SELECT id FROM stocks WHERE symbol = %s", (symbol,))
            result = cur.fetchone()
            
            if result:
                return result[0]
            
            # Create new stock entry
            if not name:
                name = f"{symbol} Stock"
            
            cur.execute("""
                INSERT INTO stocks (symbol, name, exchange, is_active)
                VALUES (%s, %s, %s, TRUE)
                RETURNING id
            """, (symbol, name, exchange))
            
            stock_id = cur.fetchone()[0]
            conn.commit()
            logger.info(f"Created new stock: {symbol} with ID: {stock_id}")
            return stock_id
            
        except Exception as e:
            logger.error(f"Error getting/creating stock {symbol}: {e}")
            return None
        finally:
            if 'conn' in locals():
                conn.close()
    
    def fetch_historical_data(self, symbol: str, period: str = "20y", interval: str = "1h") -> Optional[pd.DataFrame]:
        """Fetch historical data using multiple sources - ONE ATTEMPT PER API"""
        try:
            logger.info(f"Fetching {period} of {interval} data for {symbol}")
            
            # Define data sources in order of preference - ONE ATTEMPT EACH
            data_sources = [
                ("Yahoo Finance", self._fetch_from_yahoo_finance_simple),
                ("Twelve Data", self.multi_fetcher.fetch_from_twelve_data),
                ("Alpha Vantage", self.multi_fetcher.fetch_from_alpha_vantage),
                ("Finnhub", self.multi_fetcher.fetch_from_finnhub),
                ("IEX Cloud", self.multi_fetcher.fetch_from_iex_cloud)
            ]
            
            for source_name, fetch_function in data_sources:
                logger.info(f"Attempting {source_name} for {symbol} (single try)...")
                
                try:
                    if source_name == "Yahoo Finance":
                        data = fetch_function(symbol, period, interval)
                    else:
                        data = fetch_function(symbol, interval)
                    
                    if data is not None and not data.empty:
                        logger.info(f"SUCCESS: {source_name} returned {len(data)} records for {symbol}")
                        return data
                    else:
                        logger.info(f"FAILED: {source_name} returned no data for {symbol}")
                        
                except Exception as e:
                    logger.info(f"FAILED: {source_name} error for {symbol}: {e}")
                    # No retry - move to next API immediately
                    continue
            
            # All sources failed - stop here
            logger.error(f"All APIs failed for {symbol} - stopping")
            return None
            
        except Exception as e:
            logger.error(f"Error in fetch for {symbol}: {e}")
            return None
    
    def _fetch_from_yahoo_finance_simple(self, symbol: str, period: str = "20y", interval: str = "1h") -> Optional[pd.DataFrame]:
        """Fetch historical data using direct Yahoo Finance API - bypassing yfinance library"""
        try:
            logger.info(f"Direct Yahoo Finance API fetch for {symbol}")
            
            # Calculate date range based on period
            end_time = datetime.now()
            if period == "5d":
                start_time = end_time - timedelta(days=7)  # Extra buffer for weekends
            elif period == "1mo":
                start_time = end_time - timedelta(days=35)
            elif period == "1y":
                start_time = end_time - timedelta(days=370)
            elif period == "20y":
                start_time = end_time - timedelta(days=365 * 20)  # 20 years
            else:
                start_time = end_time - timedelta(days=365 * 5)  # Default to 5 years
            
            # Convert to timestamps
            period1 = int(start_time.timestamp())
            period2 = int(end_time.timestamp())
            
            # Map interval to Yahoo format
            yahoo_interval = "1d" if interval in ["1d", "1h"] else interval
            
            # Direct Yahoo Finance API call
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            params = {
                'period1': period1,
                'period2': period2,
                'interval': yahoo_interval,
                'includePrePost': 'false',
                'events': 'div,splits'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            if response.status_code != 200:
                logger.info(f"Yahoo Finance API returned status {response.status_code} for {symbol}")
                return None
                
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                logger.info(f"Yahoo Finance API returned invalid JSON for {symbol}: {e}")
                return None
            
            # Parse Yahoo Finance response
            if 'chart' not in data or 'result' not in data['chart'] or not data['chart']['result']:
                logger.info(f"Yahoo Finance API returned no chart data for {symbol}")
                return None
                
            result = data['chart']['result'][0]
            
            if 'timestamp' not in result or not result['timestamp']:
                logger.info(f"Yahoo Finance API returned no timestamps for {symbol}")
                return None
                
            timestamps = result['timestamp']
            quotes = result['indicators']['quote'][0]
            
            # Extract OHLCV data
            df_data = {
                'Open': quotes.get('open', []),
                'High': quotes.get('high', []),
                'Low': quotes.get('low', []),
                'Close': quotes.get('close', []),
                'Volume': quotes.get('volume', [])
            }
            
            # Create DataFrame with proper datetime index
            df = pd.DataFrame(df_data)
            df.index = pd.to_datetime([datetime.fromtimestamp(ts) for ts in timestamps])
            df.index.name = 'Datetime'
            
            # Remove rows with NaN close prices
            df = df.dropna(subset=['Close'])
            
            if not df.empty:
                logger.info(f"Yahoo Finance API returned {len(df)} records for {symbol}")
                return df
            else:
                logger.info(f"Yahoo Finance API returned no valid data for {symbol}")
                return None
                
        except Exception as e:
            logger.info(f"Yahoo Finance API failed for {symbol}: {e}")
            return None

    def store_stock_data(self, stock_id: int, data: pd.DataFrame, interval: str = "1h", symbol: str = None) -> int:
        """Store stock data in database with optional symbol validation"""
        stored_count = 0
        
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            # Optional: Verify stock_id matches expected symbol for data integrity
            if symbol:
                cur.execute("SELECT symbol FROM stocks WHERE id = %s", (stock_id,))
                result = cur.fetchone()
                if result and result[0] != symbol:
                    logger.warning(f"Symbol mismatch: expected {symbol}, got {result[0]} for stock_id {stock_id}")
            
            # Prepare batch insert data
            insert_data = []
            
            for timestamp, row in data.iterrows():
                # Ensure timestamp is timezone-aware
                if timestamp.tz is None:
                    timestamp = pytz.UTC.localize(timestamp)
                
                # Convert to UTC if needed
                if timestamp.tz != pytz.UTC:
                    timestamp = timestamp.astimezone(pytz.UTC)
                
                # Skip weekend data for daily intervals (markets typically closed)
                if interval == "1d" and timestamp.weekday() >= 5:  # Saturday=5, Sunday=6
                    continue
                
                # Skip future dates beyond today
                current_utc = datetime.now(pytz.UTC)
                if timestamp.date() > current_utc.date():
                    logger.warning(f"Skipping future date {timestamp.date()} for {symbol}")
                    continue
                
                insert_data.append((
                    stock_id,
                    timestamp,
                    float(row['Open']),
                    float(row['High']),
                    float(row['Low']),
                    float(row['Close']),
                    float(row.get('Adj Close', row['Close'])),
                    int(row['Volume']),
                    interval
                ))
            
            # Batch insert with ON CONFLICT handling
            if insert_data:
                cur.executemany("""
                    INSERT INTO stock_prices 
                    (stock_id, datetime, open_price, high_price, low_price, close_price, adjusted_close, volume, interval_type)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (stock_id, datetime, interval_type) 
                    DO UPDATE SET
                        open_price = EXCLUDED.open_price,
                        high_price = EXCLUDED.high_price,
                        low_price = EXCLUDED.low_price,
                        close_price = EXCLUDED.close_price,
                        adjusted_close = EXCLUDED.adjusted_close,
                        volume = EXCLUDED.volume
                """, insert_data)
                
                stored_count = len(insert_data)
                conn.commit()
                logger.info(f"Stored {stored_count} price records for stock ID {stock_id}")
            
        except Exception as e:
            logger.error(f"Error storing stock data: {e}")
            if 'conn' in locals():
                conn.rollback()
        finally:
            if 'conn' in locals():
                conn.close()
        
        return stored_count
    
    def log_fetch_operation(self, stock_id: int, start_time: datetime, end_time: datetime, 
                           records_count: int, status: str, error_msg: str = None):
        """Log fetch operation for monitoring"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO stock_fetch_logs 
                (stock_id, data_source_id, fetch_start, fetch_end, records_fetched, status, error_message)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (stock_id, self.data_source_id, start_time, end_time, records_count, status, error_msg))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error logging fetch operation: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def fetch_and_store_nasdaq_data(self):
        """Fetch and store NASDAQ Composite Index (^IXIC) historical data"""
        return self.fetch_and_store_stock_data("^IXIC", "NASDAQ Composite Index", "NASDAQ")
    
    def fetch_and_store_all_stocks(self):
        """Fetch and store latest data for all active stocks"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            # Get all active stocks
            cur.execute("SELECT symbol, name, exchange FROM stocks WHERE is_active = TRUE")
            stocks = cur.fetchall()
            
            logger.info(f"Updating {len(stocks)} active stocks...")
            
            success_count = 0
            error_count = 0
            
            for symbol, name, exchange in stocks:
                try:
                    # For regular updates, we only fetch recent data (last 30 days)
                    # to avoid overloading Yahoo Finance API
                    result = self.fetch_and_store_recent_data(symbol, name, exchange)
                    if result['success']:
                        success_count += 1
                        logger.info(f"✅ Updated {symbol}")
                    else:
                        error_count += 1
                        logger.error(f"❌ Failed to update {symbol}: {result.get('error', 'Unknown error')}")
                except Exception as e:
                    error_count += 1
                    logger.error(f"❌ Error updating {symbol}: {e}")
            
            logger.info(f"Stock update completed: {success_count} success, {error_count} errors")
            return {
                'success': error_count == 0,
                'updated': success_count,
                'errors': error_count,
                'total': len(stocks)
            }
            
        except Exception as e:
            logger.error(f"Error in fetch_and_store_all_stocks: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            if 'conn' in locals():
                conn.close()
    
    def get_latest_stock_data_timestamp(self, stock_id: int, interval: str = "1d") -> Optional[datetime]:
        """Get the latest timestamp for a stock's data"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT MAX(datetime) 
                FROM stock_prices 
                WHERE stock_id = %s AND interval_type = %s
            """, (stock_id, interval))
            
            result = cur.fetchone()
            return result[0] if result[0] else None
            
        except Exception as e:
            logger.error(f"Error getting latest timestamp for stock {stock_id}: {e}")
            return None

    def fetch_and_store_recent_data(self, symbol: str, name: str = None, exchange: str = "NASDAQ"):
        """Fetch and store only missing data for a stock (optimized)"""
        start_time = datetime.now()
        
        try:
            # Get or create stock entry
            if not name:
                name = f"{symbol} Stock"
            
            stock_id = self.get_or_create_stock(
                symbol=symbol,
                name=name,
                exchange=exchange
            )
            
            if not stock_id:
                raise Exception("Failed to get/create stock entry")
            
            # Check what data we already have
            latest_timestamp = self.get_latest_stock_data_timestamp(stock_id, "1d")
            
            # Determine what period to fetch
            if latest_timestamp is None:
                # No data exists, fetch last 30 days
                logger.info(f"No existing data for {symbol}, fetching last 30 days...")
                recent_data = self.fetch_historical_data(symbol, period="30d", interval="1d")
            else:
                # We have data, only fetch since last timestamp
                days_since_last = (datetime.now() - latest_timestamp.replace(tzinfo=None)).days
                
                if days_since_last <= 1:
                    # Data is recent (within 1 day), fetch just last 5 days to catch any missing data
                    logger.info(f"Recent data exists for {symbol} (last: {latest_timestamp}), fetching last 5 days...")
                    recent_data = self.fetch_historical_data(symbol, period="5d", interval="1d")
                elif days_since_last <= 7:
                    # Data is within a week, fetch last 10 days
                    logger.info(f"Week-old data for {symbol} (last: {latest_timestamp}), fetching last 10 days...")
                    recent_data = self.fetch_historical_data(symbol, period="10d", interval="1d")
                else:
                    # Data is old, fetch last 30 days
                    logger.info(f"Old data for {symbol} (last: {latest_timestamp}), fetching last 30 days...")
                    recent_data = self.fetch_historical_data(symbol, period="30d", interval="1d")
            
            records_stored = 0
            if recent_data is not None and not recent_data.empty:
                records_stored = self.store_stock_data(stock_id, recent_data, interval="1d", symbol=symbol)
                logger.info(f"Stored {records_stored} records for {symbol}")
            else:
                logger.warning(f"No data received from API for {symbol}")
            
            if records_stored == 0:
                logger.warning(f"No new data stored for {symbol}")
            
            end_time = datetime.now()
            
            # Log successful operation
            self.log_fetch_operation(
                stock_id=stock_id,
                start_time=start_time,
                end_time=end_time,
                records_count=records_stored,
                status='success'
            )
            
            return {
                'success': True,
                'symbol': symbol,
                'records': records_stored,
                'daily_records': records_stored,
                'hourly_records': 0
            }
            
        except Exception as e:
            logger.error(f"Error in recent data fetch for {symbol}: {e}")
            
            # Log failed operation
            if 'stock_id' in locals():
                self.log_fetch_operation(
                    stock_id=stock_id,
                    start_time=start_time,
                    end_time=datetime.now(),
                    records_count=0,
                    status='failed',
                    error_msg=str(e)
                )
            
            return {'success': False, 'error': str(e)}
    
    def fetch_and_store_stock_data(self, symbol: str, name: str = None, exchange: str = "NASDAQ"):
        """Fetch and store historical data for any stock symbol"""
        start_time = datetime.now()
        
        try:
            # Get or create stock entry
            if not name:
                name = f"{symbol} Stock"
            
            stock_id = self.get_or_create_stock(
                symbol=symbol,
                name=name,
                exchange=exchange
            )
            
            if not stock_id:
                raise Exception("Failed to get/create stock entry")
            
            # Fetch 20 years of daily data first (as hourly data is not available for 20 years)
            logger.info(f"Fetching 20 years of daily data for {symbol}...")
            daily_data = self.fetch_historical_data(symbol, period="20y", interval="1d")
            
            daily_records = 0
            if daily_data is not None and not daily_data.empty:
                daily_records = self.store_stock_data(stock_id, daily_data, interval="1d", symbol=symbol)
                logger.info(f"Stored {daily_records} daily records")
            
            # Also fetch recent 1 year of hourly data for more granular recent data
            logger.info(f"Fetching 1 year of hourly data for {symbol}...")
            hourly_data = self.fetch_historical_data(symbol, period="1y", interval="1h")
            
            hourly_records = 0
            if hourly_data is not None and not hourly_data.empty:
                hourly_records = self.store_stock_data(stock_id, hourly_data, interval="1h", symbol=symbol)
                logger.info(f"Stored {hourly_records} hourly records")
            
            total_records = daily_records + hourly_records
            
            if total_records == 0:
                raise Exception("No data fetched from Yahoo Finance")
            
            end_time = datetime.now()
            
            # Log successful operation
            self.log_fetch_operation(
                stock_id=stock_id,
                start_time=start_time,
                end_time=end_time,
                records_count=total_records,
                status="success"
            )
            
            # Update data source last fetch time
            self.update_data_source_stats(total_records)
            
            logger.info(f"Successfully fetched and stored {total_records} records for {symbol} ({daily_records} daily, {hourly_records} hourly)")
            return {"success": True, "records": total_records, "daily_records": daily_records, "hourly_records": hourly_records, "symbol": symbol}
            
        except Exception as e:
            end_time = datetime.now()
            error_msg = str(e)
            logger.error(f"Error in stock data fetch: {error_msg}")
            
            # Log failed operation
            if 'stock_id' in locals() and stock_id:
                self.log_fetch_operation(
                    stock_id=stock_id,
                    start_time=start_time,
                    end_time=end_time,
                    records_count=0,
                    status="error",
                    error_msg=error_msg
                )
            
            return {"success": False, "error": error_msg}
    
    def update_data_source_stats(self, new_records: int):
        """Update data source statistics"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                UPDATE data_sources 
                SET last_fetch = %s, 
                    total_records = total_records + %s
                WHERE id = %s
            """, (datetime.now(), new_records, self.data_source_id))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error updating data source stats: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def get_stock_data(self, symbol: str = "^IXIC", limit: int = 1000, interval: str = "1d") -> List[Dict]:
        """Get stored stock data for API responses"""
        try:
            conn = self.get_connection()
            cur = conn.cursor(row_factory=dict_row)
            
            # Handle weekly and monthly intervals by aggregating daily data
            if interval in ['1wk', '1mo']:
                return self._get_aggregated_stock_data(symbol, limit, interval, conn, cur)
            
            cur.execute("""
                SELECT sp.datetime, sp.open_price, sp.high_price, sp.low_price, 
                       sp.close_price, sp.adjusted_close, sp.volume, sp.interval_type,
                       s.symbol, s.name
                FROM stock_prices sp
                JOIN stocks s ON sp.stock_id = s.id
                WHERE s.symbol = %s AND sp.interval_type = %s
                ORDER BY sp.datetime DESC
                LIMIT %s
            """, (symbol, interval, limit))
            
            results = cur.fetchall()
            # Convert datetime objects and Decimal objects to strings for JSON serialization
            processed_results = []
            for row in results:
                row_dict = dict(row)
                for key, value in row_dict.items():
                    if hasattr(value, '__class__'):
                        if value.__class__.__name__ == 'datetime':
                            row_dict[key] = value.isoformat()
                        elif value.__class__.__name__ == 'Decimal':
                            row_dict[key] = float(value)
                processed_results.append(row_dict)
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Error fetching stock data: {e}")
            return []
        finally:
            if 'conn' in locals():
                conn.close()
    
    def _get_aggregated_stock_data(self, symbol: str, limit: int, interval: str, conn, cur) -> List[Dict]:
        """Get aggregated stock data for weekly/monthly intervals"""
        try:
            # Determine the aggregation period
            if interval == '1wk':
                date_trunc = 'week'
                # Get enough daily data to cover the requested number of weeks
                daily_limit = limit * 7
            elif interval == '1mo':
                date_trunc = 'month'
                # Get enough daily data to cover the requested number of months
                daily_limit = limit * 30
            else:
                return []
            
            # Aggregate daily data into weekly/monthly periods
            cur.execute("""
                WITH aggregated_data AS (
                    SELECT 
                        DATE_TRUNC(%s, sp.datetime) as period_start,
                        s.symbol,
                        s.name,
                        MIN(sp.datetime) as first_date,
                        MAX(sp.datetime) as last_date,
                        (ARRAY_AGG(sp.open_price ORDER BY sp.datetime ASC))[1] as open_price,
                        MAX(sp.high_price) as high_price,
                        MIN(sp.low_price) as low_price,
                        (ARRAY_AGG(sp.close_price ORDER BY sp.datetime DESC))[1] as close_price,
                        (ARRAY_AGG(sp.adjusted_close ORDER BY sp.datetime DESC))[1] as adjusted_close,
                        SUM(sp.volume) as volume
                    FROM stock_prices sp
                    JOIN stocks s ON sp.stock_id = s.id
                    WHERE s.symbol = %s AND sp.interval_type = '1d'
                    GROUP BY DATE_TRUNC(%s, sp.datetime), s.symbol, s.name
                    ORDER BY period_start DESC
                    LIMIT %s
                )
                SELECT 
                    last_date as datetime,
                    open_price,
                    high_price,
                    low_price,
                    close_price,
                    adjusted_close,
                    volume,
                    %s as interval_type,
                    symbol,
                    name
                FROM aggregated_data
                ORDER BY last_date DESC
            """, (date_trunc, symbol, date_trunc, limit, interval))
            
            results = cur.fetchall()
            
            # Convert datetime objects and Decimal objects for JSON serialization
            processed_results = []
            for row in results:
                row_dict = dict(row)
                for key, value in row_dict.items():
                    if hasattr(value, '__class__'):
                        if value.__class__.__name__ == 'datetime':
                            row_dict[key] = value.isoformat()
                        elif value.__class__.__name__ == 'Decimal':
                            row_dict[key] = float(value)
                processed_results.append(row_dict)
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Error fetching aggregated stock data: {e}")
            return []
    
    def get_latest_stock_prices(self, exchange: str = None) -> List[Dict]:
        """Get latest prices for all stocks or filtered by exchange"""
        try:
            conn = self.get_connection()
            cur = conn.cursor(row_factory=dict_row)
            
            # Build query with optional exchange filter
            base_query = """
                SELECT DISTINCT ON (s.symbol) 
                       s.symbol, s.name, s.exchange,
                       sp.close_price as current_price,
                       sp.datetime as last_update,
                       sp.volume,
                       sp.open_price,
                       sp.high_price,
                       sp.low_price
                FROM stocks s
                JOIN stock_prices sp ON s.id = sp.stock_id
                WHERE s.is_active = TRUE
            """
            
            if exchange:
                base_query += " AND s.exchange = %s"
                cur.execute(base_query + " ORDER BY s.symbol, sp.datetime DESC", (exchange,))
            else:
                cur.execute(base_query + " ORDER BY s.symbol, sp.datetime DESC")
            
            results = cur.fetchall()
            
            # Convert datetime objects and Decimal objects for JSON serialization
            processed_results = []
            for row in results:
                row_dict = dict(row)
                for key, value in row_dict.items():
                    if hasattr(value, '__class__'):
                        if value.__class__.__name__ == 'datetime':
                            row_dict[key] = value.isoformat()
                        elif value.__class__.__name__ == 'Decimal':
                            row_dict[key] = float(value)
                processed_results.append(row_dict)
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Error fetching latest prices: {e}")
            return []
        finally:
            if 'conn' in locals():
                conn.close()
    
    def get_stock_data_count(self, symbol: str) -> int:
        """Get the count of stock price records for a given symbol"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT COUNT(sp.id) as record_count
                FROM stock_prices sp
                JOIN stocks s ON sp.stock_id = s.id
                WHERE s.symbol = %s
            """, (symbol,))
            
            result = cur.fetchone()
            return result[0] if result else 0
            
        except Exception as e:
            logger.error(f"Error getting stock data count for {symbol}: {e}")
            return 0
        finally:
            if 'conn' in locals():
                conn.close()
    
    def get_yearly_growth_analysis(self, symbol: str = "^IXIC") -> List[Dict]:
        """Calculate yearly growth rates for the stock"""
        try:
            conn = self.get_connection()
            cur = conn.cursor(row_factory=dict_row)
            
            # Get yearly data (first and last trading day of each year) with proper deduplication
            cur.execute("""
                WITH yearly_data AS (
                    SELECT 
                        EXTRACT(YEAR FROM sp.datetime) as year,
                        MIN(DATE(sp.datetime)) as year_start_date,
                        MAX(DATE(sp.datetime)) as year_end_date
                    FROM stock_prices sp
                    JOIN stocks s ON sp.stock_id = s.id
                    WHERE s.symbol = %s AND sp.interval_type = '1d'
                    GROUP BY EXTRACT(YEAR FROM sp.datetime)
                    ORDER BY year
                ),
                yearly_prices AS (
                    SELECT DISTINCT ON (yd.year)
                        yd.year,
                        start_price.close_price as start_price,
                        end_price.close_price as end_price,
                        start_price.datetime as start_date,
                        end_price.datetime as end_date
                    FROM yearly_data yd
                    JOIN stock_prices start_price ON DATE(start_price.datetime) = yd.year_start_date
                    JOIN stock_prices end_price ON DATE(end_price.datetime) = yd.year_end_date
                    JOIN stocks s1 ON start_price.stock_id = s1.id
                    JOIN stocks s2 ON end_price.stock_id = s2.id
                    WHERE s1.symbol = %s AND s2.symbol = %s 
                      AND start_price.interval_type = '1d' 
                      AND end_price.interval_type = '1d'
                    ORDER BY yd.year DESC
                )
                SELECT 
                    year,
                    start_price,
                    end_price,
                    start_date,
                    end_date,
                    ROUND(((end_price - start_price) / start_price * 100)::numeric, 2) as growth_percentage,
                    ROUND((end_price - start_price)::numeric, 2) as price_change
                FROM yearly_prices
                ORDER BY year DESC
            """, (symbol, symbol, symbol))
            
            results = cur.fetchall()
            
            # Convert to list of dictionaries with proper serialization
            processed_results = []
            for row in results:
                row_dict = dict(row)
                for key, value in row_dict.items():
                    if hasattr(value, '__class__'):
                        if value.__class__.__name__ == 'datetime':
                            row_dict[key] = value.isoformat()
                        elif value.__class__.__name__ == 'Decimal':
                            row_dict[key] = float(value)
                        elif value.__class__.__name__ == 'date':
                            row_dict[key] = value.isoformat()
                processed_results.append(row_dict)
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Error calculating yearly growth: {e}")
            return []
        finally:
            if 'conn' in locals():
                conn.close()
    
    def calculate_investment_returns(self, symbol: str = "^IXIC", monthly_investment: float = 100.0, start_year: str = None) -> Dict:
        """Calculate returns for monthly investments over time"""
        try:
            conn = self.get_connection()
            cur = conn.cursor(row_factory=dict_row)
            
            # Validate input parameters
            if monthly_investment <= 0:
                return {"error": "Monthly investment must be greater than 0"}
            
            if monthly_investment > 1000000:  # Sanity check for extremely large values
                return {"error": "Monthly investment amount seems unreasonably large"}
            
            logger.info(f"Calculating investment returns for {symbol} with monthly investment of {monthly_investment}")
            
            # Get monthly data points (first trading day of each month)
            if start_year:
                start_date_filter = f"AND sp.datetime >= '{start_year}-01-01'"
            else:
                start_date_filter = ""
            
            cur.execute(f"""
                WITH monthly_data AS (
                    SELECT 
                        DATE_TRUNC('month', sp.datetime) as month,
                        MIN(DATE(sp.datetime)) as first_trading_date,
                        MAX(DATE(sp.datetime)) as last_trading_date
                    FROM stock_prices sp
                    JOIN stocks s ON sp.stock_id = s.id
                    WHERE s.symbol = %s AND sp.interval_type = '1d' {start_date_filter}
                    GROUP BY DATE_TRUNC('month', sp.datetime)
                    ORDER BY month
                ),
                start_prices AS (
                    SELECT DISTINCT ON (md.month)
                        md.month,
                        md.first_trading_date,
                        md.last_trading_date,
                        sp.close_price as purchase_price,
                        sp.datetime as investment_date
                    FROM monthly_data md
                    JOIN stock_prices sp ON DATE(sp.datetime) = md.first_trading_date
                    JOIN stocks s ON sp.stock_id = s.id
                    WHERE s.symbol = %s AND sp.interval_type = '1d'
                    ORDER BY md.month, sp.datetime
                ),
                end_prices AS (
                    SELECT DISTINCT ON (md.month)
                        md.month,
                        sp.close_price as month_end_price
                    FROM monthly_data md
                    JOIN stock_prices sp ON DATE(sp.datetime) = md.last_trading_date
                    JOIN stocks s ON sp.stock_id = s.id
                    WHERE s.symbol = %s AND sp.interval_type = '1d'
                    ORDER BY md.month, sp.datetime DESC
                )
                SELECT 
                    sp.month,
                    sp.purchase_price,
                    ep.month_end_price,
                    sp.investment_date
                FROM start_prices sp
                JOIN end_prices ep ON sp.month = ep.month
                ORDER BY sp.month
            """, (symbol, symbol, symbol))
            
            monthly_prices = cur.fetchall()
            
            if not monthly_prices:
                return {"error": "No monthly data available"}
            
            # Get current price
            cur.execute("""
                SELECT close_price 
                FROM stock_prices sp
                JOIN stocks s ON sp.stock_id = s.id
                WHERE s.symbol = %s AND sp.interval_type = '1d'
                ORDER BY sp.datetime DESC
                LIMIT 1
            """, (symbol,))
            
            current_result = cur.fetchone()
            if not current_result:
                return {"error": "No current price available"}
            
            current_price = float(current_result['close_price'])
            
            # Calculate investment returns
            total_invested = 0
            total_shares = 0
            investment_history = []
            
            for price_data in monthly_prices:
                purchase_price = float(price_data['purchase_price'])
                month_end_price = float(price_data['month_end_price'])
                
                # Validate prices are reasonable
                if purchase_price <= 0 or month_end_price <= 0:
                    logger.warning(f"Invalid price data for {symbol}: purchase={purchase_price}, month_end={month_end_price}")
                    continue
                
                shares_purchased = monthly_investment / purchase_price
                total_invested += monthly_investment
                total_shares += shares_purchased
                
                # Value portfolio at the end-of-month price for that month
                # This shows actual historical performance at each point
                value_at_time = total_shares * month_end_price
                total_return = value_at_time - total_invested
                return_percentage = (total_return / total_invested * 100) if total_invested > 0 else 0
                
                investment_history.append({
                    'date': price_data['investment_date'].isoformat(),
                    'month': price_data['month'].strftime('%Y-%m'),
                    'price': round(purchase_price, 4),
                    'month_end_price': round(month_end_price, 4),
                    'shares_purchased': round(shares_purchased, 4),
                    'total_invested': round(total_invested, 2),
                    'total_shares': round(total_shares, 4),
                    'current_value': round(value_at_time, 2),
                    'total_return': round(total_return, 2),
                    'return_percentage': round(return_percentage, 2)
                })
            
            # Calculate current value using today's price for summary
            current_total_value = total_shares * current_price
            current_total_return = current_total_value - total_invested
            current_return_percentage = (current_total_return / total_invested * 100) if total_invested > 0 else 0
            
            # Summary statistics
            years_invested = len(monthly_prices) / 12
            
            # Calculate proper annualized return using CAGR formula
            # CAGR = (Ending Value / Beginning Value)^(1/years) - 1
            if years_invested > 0 and total_invested > 0:
                # For dollar-cost averaging, we use the ratio of current value to total invested
                growth_ratio = current_total_value / total_invested
                annualized_return = (pow(growth_ratio, 1/years_invested) - 1) * 100
            else:
                annualized_return = 0
            
            return {
                'symbol': symbol,
                'monthly_investment': monthly_investment,
                'investment_history': investment_history,
                'summary': {
                    'total_invested': round(total_invested, 2),
                    'current_value': round(current_total_value, 2),
                    'total_return': round(current_total_return, 2),
                    'return_percentage': round(current_return_percentage, 2),
                    'annualized_return': round(annualized_return, 2),
                    'months_invested': len(monthly_prices),
                    'years_invested': round(years_invested, 2),
                    'current_price': current_price,
                    'total_shares': round(total_shares, 4)
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating investment returns: {e}")
            return {"error": str(e)}
        finally:
            if 'conn' in locals():
                conn.close()

    def get_available_years(self, symbol: str = "^IXIC") -> Dict:
        """Get available years for investment calculations"""
        try:
            conn = self.get_connection()
            cur = conn.cursor(row_factory=dict_row)
            
            # Get available years from stock data
            cur.execute("""
                SELECT DISTINCT EXTRACT(YEAR FROM sp.datetime) as year
                FROM stock_prices sp
                JOIN stocks s ON sp.stock_id = s.id
                WHERE s.symbol = %s AND sp.interval_type = '1d'
                ORDER BY year
            """, (symbol,))
            
            years_data = cur.fetchall()
            years = [int(row['year']) for row in years_data]
            
            return {
                'symbol': symbol,
                'years': years,
                'earliest_year': min(years) if years else None,
                'latest_year': max(years) if years else None
            }
            
        except Exception as e:
            logger.error(f"Error getting available years: {e}")
            return {"error": str(e)}
        finally:
            if 'conn' in locals():
                conn.close()

# Scheduled job runner
class StockDataScheduler:
    def __init__(self, stock_service: StockDataService):
        self.stock_service = stock_service
        self.running = False
        
    def start_scheduler(self):
        """Start the background scheduler"""
        if self.running:
            return
            
        self.running = True
        
        # Schedule daily data fetch at 6 AM for NASDAQ index
        schedule.every().day.at("06:00").do(self._safe_fetch_nasdaq_data)
        
        # Schedule hourly updates for all stocks (24/7 to catch different global markets)
        schedule.every().hour.do(self._safe_fetch_all_stocks)
        
        def run_scheduler():
            while self.running:
                try:
                    schedule.run_pending()
                except Exception as e:
                    logger.error(f"Scheduler error: {e}")
                time.sleep(60)  # Check every minute
        
        # Run scheduler in background thread
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        logger.info("Stock data scheduler started - running every hour")
    
    def _safe_fetch_nasdaq_data(self):
        """Safely fetch NASDAQ data with error handling"""
        try:
            logger.info("Starting scheduled NASDAQ data fetch...")
            result = self.stock_service.fetch_and_store_nasdaq_data()
            logger.info(f"NASDAQ fetch completed: {result}")
        except Exception as e:
            logger.error(f"Error in scheduled NASDAQ fetch: {e}")
    
    def _safe_fetch_all_stocks(self):
        """Safely fetch all stocks data with error handling"""
        try:
            logger.info("Starting scheduled all stocks data fetch...")
            result = self.stock_service.fetch_and_store_all_stocks()
            logger.info(f"All stocks fetch completed: {result}")
        except Exception as e:
            logger.error(f"Error in scheduled all stocks fetch: {e}")
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.running = False
        schedule.clear()
        logger.info("Stock data scheduler stopped")