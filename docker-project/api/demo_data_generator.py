"""
Demo stock data generator for testing the stock dashboard
"""
import random
import pandas as pd
from datetime import datetime, timedelta
import psycopg
from psycopg.rows import dict_row
import numpy as np

class DemoStockDataGenerator:
    def __init__(self, db_config):
        self.db_config = db_config
    
    def get_connection(self):
        return psycopg.connect(**self.db_config)
    
    def generate_sample_data(self, symbol="AAPL", days=365):
        """Generate realistic sample stock data"""
        
        # Starting parameters
        start_price = 150.0  # Starting price for AAPL
        current_price = start_price
        
        # Generate dates
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        data = []
        
        for date in dates:
            # Skip weekends (basic simulation)
            if date.weekday() >= 5:
                continue
                
            # Generate realistic price movements
            daily_volatility = 0.02  # 2% daily volatility
            price_change = np.random.normal(0, daily_volatility)
            
            # Apply some trending behavior
            trend = 0.0002  # Slight upward trend
            current_price *= (1 + price_change + trend)
            
            # Generate OHLC data
            open_price = current_price * (1 + np.random.normal(0, 0.005))
            high_price = max(open_price, current_price) * (1 + abs(np.random.normal(0, 0.01)))
            low_price = min(open_price, current_price) * (1 - abs(np.random.normal(0, 0.01)))
            close_price = current_price
            
            # Generate volume
            volume = int(np.random.lognormal(16, 0.5))  # Log-normal distribution for volume
            
            data.append({
                'datetime': date,
                'open_price': round(open_price, 2),
                'high_price': round(high_price, 2),
                'low_price': round(low_price, 2),
                'close_price': round(close_price, 2),
                'adjusted_close': round(close_price, 2),
                'volume': volume
            })
        
        return pd.DataFrame(data)
    
    def create_demo_data(self):
        """Create demo stock data in the database"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            # Ensure AAPL stock exists
            cur.execute("""
                INSERT INTO stocks (symbol, name, exchange) 
                VALUES ('AAPL', 'Apple Inc.', 'NASDAQ') 
                ON CONFLICT (symbol) DO NOTHING RETURNING id
            """)
            
            result = cur.fetchone()
            if result:
                stock_id = result[0]
            else:
                cur.execute("SELECT id FROM stocks WHERE symbol = 'AAPL'")
                stock_id = cur.fetchone()[0]
            
            # Generate sample data
            sample_data = self.generate_sample_data("AAPL", days=365)
            
            # Clear existing data
            cur.execute("DELETE FROM stock_prices WHERE stock_id = %s", (stock_id,))
            
            # Insert sample data
            insert_data = []
            for _, row in sample_data.iterrows():
                insert_data.append((
                    stock_id,
                    row['datetime'],
                    row['open_price'],
                    row['high_price'],
                    row['low_price'],
                    row['close_price'],
                    row['adjusted_close'],
                    row['volume'],
                    '1d'  # daily interval
                ))
            
            cur.executemany("""
                INSERT INTO stock_prices 
                (stock_id, datetime, open_price, high_price, low_price, close_price, adjusted_close, volume, interval_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (stock_id, datetime, interval_type) DO NOTHING
            """, insert_data)
            
            conn.commit()
            
            # Also create some recent hourly data for the last 30 days
            self.create_hourly_demo_data(stock_id, cur, conn)
            
            print(f"Created {len(insert_data)} daily records for AAPL")
            return {"success": True, "records": len(insert_data), "symbol": "AAPL"}
            
        except Exception as e:
            print(f"Error creating demo data: {e}")
            return {"success": False, "error": str(e)}
        finally:
            if 'conn' in locals():
                conn.close()
    
    def create_hourly_demo_data(self, stock_id, cur, conn):
        """Create hourly demo data for recent days"""
        try:
            # Get the latest daily price
            cur.execute("""
                SELECT close_price FROM stock_prices 
                WHERE stock_id = %s AND interval_type = '1d'
                ORDER BY datetime DESC LIMIT 1
            """, (stock_id,))
            
            result = cur.fetchone()
            if not result:
                return
                
            latest_price = float(result[0])
            
            # Generate hourly data for last 7 days
            end_time = datetime.now().replace(minute=0, second=0, microsecond=0)
            start_time = end_time - timedelta(days=7)
            
            hourly_data = []
            current_price = latest_price
            
            current_time = start_time
            while current_time <= end_time:
                # Only generate data for market hours (9 AM - 4 PM weekdays)
                if current_time.weekday() < 5 and 9 <= current_time.hour <= 16:
                    # Small hourly movements
                    price_change = np.random.normal(0, 0.005)  # 0.5% hourly volatility
                    current_price *= (1 + price_change)
                    
                    open_price = current_price * (1 + np.random.normal(0, 0.001))
                    high_price = max(open_price, current_price) * (1 + abs(np.random.normal(0, 0.002)))
                    low_price = min(open_price, current_price) * (1 - abs(np.random.normal(0, 0.002)))
                    close_price = current_price
                    
                    volume = int(np.random.lognormal(14, 0.3))  # Smaller volume for hourly
                    
                    hourly_data.append((
                        stock_id,
                        current_time,
                        round(open_price, 2),
                        round(high_price, 2),
                        round(low_price, 2),
                        round(close_price, 2),
                        round(close_price, 2),
                        volume,
                        '1h'
                    ))
                
                current_time += timedelta(hours=1)
            
            # Insert hourly data
            cur.executemany("""
                INSERT INTO stock_prices 
                (stock_id, datetime, open_price, high_price, low_price, close_price, adjusted_close, volume, interval_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (stock_id, datetime, interval_type) DO NOTHING
            """, hourly_data)
            
            conn.commit()
            print(f"Created {len(hourly_data)} hourly records for AAPL")
            
        except Exception as e:
            print(f"Error creating hourly demo data: {e}")

if __name__ == "__main__":
    # Database configuration
    DB_CONFIG = {
        'host': 'database',
        'dbname': 'webapp_db',
        'user': 'root',
        'password': '530NWC0Gm3pt4O',
        'port': '5432'
    }
    
    generator = DemoStockDataGenerator(DB_CONFIG)
    result = generator.create_demo_data()
    print(result)