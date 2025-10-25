#!/usr/bin/env python3
"""
Technical Indicators Calculation Service
Computes and stores technical indicators for cryptocurrency price data
Uses pandas and numpy for efficient vectorized calculations
"""

import pandas as pd
import numpy as np
import psycopg
# psycopg3 uses executemany for bulk inserts (no need for execute_values)
import logging
import os
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TechnicalIndicatorsService:
    def __init__(self, db_config=None):
        if db_config is None:
            db_config = {
                'host': os.getenv('DB_HOST', 'database'),
                'dbname': os.getenv('DB_NAME', 'webapp_db'),
                'user': os.getenv('DB_USER', 'root'),
                'password': os.getenv('DB_PASSWORD', '530NWC0Gm3pt4O'),
                'port': os.getenv('DB_PORT', 5432)
            }
        self.db_config = db_config
    
    def get_connection(self):
        """Get database connection"""
        return psycopg.connect(**self.db_config)
    
    def calculate_sma(self, data, period):
        """Calculate Simple Moving Average"""
        return data.rolling(window=period, min_periods=period).mean()
    
    def calculate_ema(self, data, period):
        """Calculate Exponential Moving Average"""
        return data.ewm(span=period, adjust=False, min_periods=period).mean()
    
    def calculate_rsi(self, data, period=14):
        """
        Calculate Relative Strength Index
        RSI = 100 - (100 / (1 + RS))
        RS = Average Gain / Average Loss
        """
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period, min_periods=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period, min_periods=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, data, fast=12, slow=26, signal=9):
        """
        Calculate MACD (Moving Average Convergence Divergence)
        MACD = EMA(12) - EMA(26)
        Signal = EMA(9) of MACD
        Histogram = MACD - Signal
        """
        ema_fast = self.calculate_ema(data, fast)
        ema_slow = self.calculate_ema(data, slow)
        
        macd = ema_fast - ema_slow
        macd_signal = self.calculate_ema(macd, signal)
        macd_histogram = macd - macd_signal
        
        return macd, macd_signal, macd_histogram
    
    def calculate_bollinger_bands(self, data, period=20, std_dev=2):
        """
        Calculate Bollinger Bands
        Middle Band = SMA(20)
        Upper Band = Middle + (2 * STD)
        Lower Band = Middle - (2 * STD)
        """
        middle = self.calculate_sma(data, period)
        std = data.rolling(window=period, min_periods=period).std()
        
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)
        width = upper - lower
        
        return upper, middle, lower, width
    
    def calculate_volatility(self, data, period):
        """Calculate price volatility (standard deviation of returns)"""
        returns = data.pct_change()
        volatility = returns.rolling(window=period, min_periods=period).std() * 100
        return volatility
    
    def calculate_support_resistance(self, data, window=20):
        """
        Calculate support and resistance levels
        Support = Recent low
        Resistance = Recent high
        """
        support = data.rolling(window=window, min_periods=window).min()
        resistance = data.rolling(window=window, min_periods=window).max()
        return support, resistance
    
    def calculate_all_indicators(self, df):
        """
        Calculate all technical indicators for a DataFrame
        Input: DataFrame with columns [datetime, open_price, high_price, low_price, close_price, volume]
        Output: DataFrame with all indicators
        """
        if df.empty or len(df) < 200:
            logger.warning(f"Not enough data for indicator calculation: {len(df)} rows")
            return pd.DataFrame()
        
        # Sort by datetime to ensure correct calculation
        df = df.sort_values('datetime')
        
        close = df['close_price']
        high = df['high_price']
        low = df['low_price']
        volume = df['volume']
        
        # Moving Averages
        df['sma_7'] = self.calculate_sma(close, 7)
        df['sma_20'] = self.calculate_sma(close, 20)
        df['sma_50'] = self.calculate_sma(close, 50)
        df['sma_200'] = self.calculate_sma(close, 200)
        df['ema_12'] = self.calculate_ema(close, 12)
        df['ema_26'] = self.calculate_ema(close, 26)
        
        # RSI
        df['rsi_7'] = self.calculate_rsi(close, 7)
        df['rsi_14'] = self.calculate_rsi(close, 14)
        df['rsi_21'] = self.calculate_rsi(close, 21)
        
        # MACD
        df['macd'], df['macd_signal'], df['macd_histogram'] = self.calculate_macd(close)
        
        # Bollinger Bands
        df['bb_upper'], df['bb_middle'], df['bb_lower'], df['bb_width'] = \
            self.calculate_bollinger_bands(close)
        
        # Volume indicators
        df['volume_sma_20'] = self.calculate_sma(volume, 20)
        df['volume_ratio'] = volume / df['volume_sma_20']
        
        # Price changes
        df['price_change_1h'] = close.pct_change(1) * 100
        df['price_change_24h'] = close.pct_change(24) * 100
        df['price_change_7d'] = close.pct_change(24*7) * 100
        
        # Volatility
        df['volatility_7d'] = self.calculate_volatility(close, 24*7)
        df['volatility_30d'] = self.calculate_volatility(close, 24*30)
        
        # Support/Resistance
        df['support_level'], df['resistance_level'] = \
            self.calculate_support_resistance(close, window=20)
        
        return df
    
    def fetch_price_data(self, crypto_id, start_date=None, end_date=None, interval='1h'):
        """Fetch price data for a cryptocurrency"""
        with self.get_connection() as conn:
            query = """
                SELECT 
                    crypto_id,
                    datetime,
                    interval_type,
                    open_price,
                    high_price,
                    low_price,
                    close_price,
                    volume
                FROM crypto_prices
                WHERE crypto_id = %s
                    AND interval_type = %s
            """
            
            params = [crypto_id, interval]
            
            if start_date:
                query += " AND datetime >= %s"
                params.append(start_date)
            
            if end_date:
                query += " AND datetime <= %s"
                params.append(end_date)
            
            query += " ORDER BY datetime"
            
            df = pd.read_sql(query, conn, params=params)
            return df
    
    def store_indicators(self, crypto_id, df, interval='1h'):
        """Store calculated indicators in database"""
        if df.empty:
            logger.warning(f"No indicators to store for crypto {crypto_id}")
            return 0
        
        # Select only indicator columns
        indicator_columns = [
            'crypto_id', 'datetime', 'interval_type',
            'sma_7', 'sma_20', 'sma_50', 'sma_200',
            'ema_12', 'ema_26',
            'rsi_7', 'rsi_14', 'rsi_21',
            'macd', 'macd_signal', 'macd_histogram',
            'bb_upper', 'bb_middle', 'bb_lower', 'bb_width',
            'volume_sma_20', 'volume_ratio',
            'price_change_1h', 'price_change_24h', 'price_change_7d',
            'volatility_7d', 'volatility_30d',
            'support_level', 'resistance_level'
        ]
        
        # Add metadata columns
        df['interval_type'] = interval
        
        # Filter to only rows with valid indicators (skip first 200 rows typically)
        df_valid = df.dropna(subset=['sma_200'])  # SMA_200 is the last to be calculated
        
        if df_valid.empty:
            logger.warning(f"No valid indicators after calculation for crypto {crypto_id}")
            return 0
        
        # Prepare data for insertion
        df_valid = df_valid[indicator_columns]
        
        # Convert to list of tuples
        values = [tuple(row) for row in df_valid.to_numpy()]
        
        # Insert with ON CONFLICT UPDATE
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                query = """
                    INSERT INTO crypto_technical_indicators (
                        crypto_id, datetime, interval_type,
                        sma_7, sma_20, sma_50, sma_200,
                        ema_12, ema_26,
                        rsi_7, rsi_14, rsi_21,
                        macd, macd_signal, macd_histogram,
                        bb_upper, bb_middle, bb_lower, bb_width,
                        volume_sma_20, volume_ratio,
                        price_change_1h, price_change_24h, price_change_7d,
                        volatility_7d, volatility_30d,
                        support_level, resistance_level
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s
                    )
                    ON CONFLICT (crypto_id, datetime, interval_type)
                    DO UPDATE SET
                        sma_7 = EXCLUDED.sma_7,
                        sma_20 = EXCLUDED.sma_20,
                        sma_50 = EXCLUDED.sma_50,
                        sma_200 = EXCLUDED.sma_200,
                        ema_12 = EXCLUDED.ema_12,
                        ema_26 = EXCLUDED.ema_26,
                        rsi_7 = EXCLUDED.rsi_7,
                        rsi_14 = EXCLUDED.rsi_14,
                        rsi_21 = EXCLUDED.rsi_21,
                        macd = EXCLUDED.macd,
                        macd_signal = EXCLUDED.macd_signal,
                        macd_histogram = EXCLUDED.macd_histogram,
                        bb_upper = EXCLUDED.bb_upper,
                        bb_middle = EXCLUDED.bb_middle,
                        bb_lower = EXCLUDED.bb_lower,
                        bb_width = EXCLUDED.bb_width,
                        volume_sma_20 = EXCLUDED.volume_sma_20,
                        volume_ratio = EXCLUDED.volume_ratio,
                        price_change_1h = EXCLUDED.price_change_1h,
                        price_change_24h = EXCLUDED.price_change_24h,
                        price_change_7d = EXCLUDED.price_change_7d,
                        volatility_7d = EXCLUDED.volatility_7d,
                        volatility_30d = EXCLUDED.volatility_30d,
                        support_level = EXCLUDED.support_level,
                        resistance_level = EXCLUDED.resistance_level,
                        calculated_at = CURRENT_TIMESTAMP
                """
                
                # psycopg3 uses executemany instead of execute_values
                cur.executemany(query, values)
                conn.commit()
                
                return len(values)
    
    def calculate_and_store_indicators(self, crypto_id, start_date=None, end_date=None):
        """
        Main method: Fetch price data, calculate indicators, and store them
        """
        try:
            logger.info(f"📊 Calculating indicators for crypto {crypto_id}...")
            
            # Fetch price data (fetch extra for moving averages)
            if start_date:
                # Fetch 200 days before start_date for indicator warmup
                fetch_start = pd.to_datetime(start_date) - timedelta(days=200)
            else:
                fetch_start = None
            
            df = self.fetch_price_data(crypto_id, fetch_start, end_date)
            
            if df.empty:
                logger.warning(f"No price data found for crypto {crypto_id}")
                return 0
            
            logger.info(f"Fetched {len(df)} price records")
            
            # Calculate all indicators
            df_with_indicators = self.calculate_all_indicators(df)
            
            if df_with_indicators.empty:
                logger.warning(f"Indicator calculation failed for crypto {crypto_id}")
                return 0
            
            # Store indicators
            rows_stored = self.store_indicators(crypto_id, df_with_indicators)
            
            logger.info(f"✅ Stored {rows_stored} indicator records for crypto {crypto_id}")
            
            return rows_stored
            
        except Exception as e:
            logger.error(f"❌ Error calculating indicators for crypto {crypto_id}: {e}")
            return 0
    
    def calculate_all_cryptos(self, limit=None):
        """Calculate indicators for all cryptocurrencies"""
        with self.get_connection() as conn:
            query = "SELECT id, symbol FROM cryptocurrencies WHERE is_active = true ORDER BY id"
            if limit:
                query += f" LIMIT {limit}"
            
            cryptos = pd.read_sql(query, conn)
        
        total_stored = 0
        for idx, row in cryptos.iterrows():
            crypto_id = row['id']
            symbol = row['symbol']
            
            logger.info(f"\n[{idx+1}/{len(cryptos)}] Processing {symbol} (ID: {crypto_id})")
            
            rows = self.calculate_and_store_indicators(crypto_id)
            total_stored += rows
        
        logger.info(f"\n✅ Total indicators stored: {total_stored}")
        return total_stored


if __name__ == "__main__":
    import sys
    
    service = TechnicalIndicatorsService()
    
    if len(sys.argv) > 1:
        # Calculate for specific crypto
        crypto_id = int(sys.argv[1])
        service.calculate_and_store_indicators(crypto_id)
    else:
        # Calculate for first 10 cryptos (test mode)
        logger.info("📊 Calculating indicators for first 10 cryptocurrencies...")
        service.calculate_all_cryptos(limit=10)
