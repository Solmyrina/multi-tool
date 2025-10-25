#!/usr/bin/env python3
"""
Check what the top 200 cryptocurrencies are according to Binance
"""

from crypto_service import CryptoDataService

def check_top_200():
    # Initialize service
    service = CryptoDataService()
    
    # Get top 200 cryptocurrencies by volume
    print('🔍 Fetching top 200 cryptocurrencies from Binance...')
    top_cryptos = service.get_top_cryptocurrencies(200)
    
    print(f'📊 Found {len(top_cryptos)} cryptocurrencies')
    print()
    print('🏆 Top 20 by 24h Volume:')
    for i, crypto in enumerate(top_cryptos[:20]):
        volume = float(crypto['quote_volume'])
        print(f'   {i+1:2d}. {crypto["binance_symbol"]:12s} - {crypto["base_asset"]:8s} - ${volume:,.0f}')
    
    print()
    print('📈 Volume Range:')
    volumes = [float(c['quote_volume']) for c in top_cryptos]
    print(f'   Highest: ${max(volumes):,.0f}')
    print(f'   Lowest (rank 200): ${min(volumes):,.0f}')
    print(f'   Median: ${sorted(volumes)[len(volumes)//2]:,.0f}')
    
    print()
    print('🔍 Checking current database configuration:')
    
    # Check what's in database
    import psycopg
    from psycopg.rows import dict_row
    import os
    
    db_config = {
        'host': os.getenv('DB_HOST', 'database'),
        'dbname': os.getenv('DB_NAME', 'webapp_db'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', '530NWC0Gm3pt4O'),
        'port': os.getenv('DB_PORT', 5432)
    }
    
    with psycopg.connect(**db_config) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT COUNT(*) as total FROM cryptocurrencies WHERE is_active = true;")
            db_count = cur.fetchone()['total']
            
            print(f'   Database has {db_count} active cryptocurrencies')
            
            # Check if the current collection is using all 200
            top_200_symbols = [crypto['binance_symbol'] for crypto in top_cryptos]
            
            # Get symbols from database
            cur.execute("SELECT binance_symbol FROM cryptocurrencies WHERE is_active = true;")
            db_symbols = [row['binance_symbol'] for row in cur.fetchall()]
            
            missing_from_db = set(top_200_symbols) - set(db_symbols)
            extra_in_db = set(db_symbols) - set(top_200_symbols)
            
            print(f'   Missing from database: {len(missing_from_db)} symbols')
            print(f'   Extra in database: {len(extra_in_db)} symbols')
            
            if missing_from_db:
                print(f'   First 10 missing: {list(missing_from_db)[:10]}')

if __name__ == "__main__":
    check_top_200()