-- Cryptocurrency market data tables
-- Add to existing database or run separately

-- Create cryptocurrencies table to store different crypto symbols
CREATE TABLE IF NOT EXISTS cryptocurrencies (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    base_asset VARCHAR(20) NOT NULL, -- BTC, ETH, etc.
    quote_asset VARCHAR(20) NOT NULL DEFAULT 'USDT', -- USDT, USD, BTC, etc.
    binance_symbol VARCHAR(30) NOT NULL, -- BTCUSDT, ETHUSDT, etc.
    market_cap BIGINT,
    max_supply BIGINT,
    circulating_supply BIGINT,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    rank_position INTEGER, -- Market cap ranking
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(base_asset, quote_asset)
);

-- Create crypto_prices table for historical price data
CREATE TABLE IF NOT EXISTS crypto_prices (
    id BIGSERIAL PRIMARY KEY,
    crypto_id INTEGER REFERENCES cryptocurrencies(id) ON DELETE CASCADE,
    datetime TIMESTAMP NOT NULL,
    open_price DECIMAL(20,8) NOT NULL,
    high_price DECIMAL(20,8) NOT NULL,
    low_price DECIMAL(20,8) NOT NULL,
    close_price DECIMAL(20,8) NOT NULL,
    volume DECIMAL(20,8) NOT NULL DEFAULT 0,
    quote_asset_volume DECIMAL(20,8) NOT NULL DEFAULT 0, -- Volume in quote asset (USDT)
    number_of_trades INTEGER DEFAULT 0,
    taker_buy_base_asset_volume DECIMAL(20,8) DEFAULT 0,
    taker_buy_quote_asset_volume DECIMAL(20,8) DEFAULT 0,
    interval_type VARCHAR(10) DEFAULT '1h', -- 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(crypto_id, datetime, interval_type)
);

-- Create crypto_data_sources table to track data fetching
CREATE TABLE IF NOT EXISTS crypto_data_sources (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(50) NOT NULL,
    api_endpoint VARCHAR(255),
    last_fetch TIMESTAMP,
    total_records BIGINT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active', -- active, inactive, error
    error_message TEXT,
    api_key_hash VARCHAR(255), -- Hashed API key for security
    rate_limit_per_minute INTEGER DEFAULT 1200, -- Binance default
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create crypto_fetch_logs table for monitoring data collection
CREATE TABLE IF NOT EXISTS crypto_fetch_logs (
    id BIGSERIAL PRIMARY KEY,
    crypto_id INTEGER REFERENCES cryptocurrencies(id) ON DELETE CASCADE,
    data_source_id INTEGER REFERENCES crypto_data_sources(id),
    fetch_start TIMESTAMP NOT NULL,
    fetch_end TIMESTAMP,
    records_fetched INTEGER DEFAULT 0,
    interval_type VARCHAR(10) NOT NULL,
    start_time TIMESTAMP, -- Start of data period fetched
    end_time TIMESTAMP, -- End of data period fetched
    status VARCHAR(20) DEFAULT 'pending', -- pending, success, error, partial
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create crypto_market_stats table for current market data
CREATE TABLE IF NOT EXISTS crypto_market_stats (
    id SERIAL PRIMARY KEY,
    crypto_id INTEGER REFERENCES cryptocurrencies(id) ON DELETE CASCADE,
    current_price DECIMAL(20,8) NOT NULL,
    price_change_24h DECIMAL(20,8),
    price_change_percent_24h DECIMAL(8,4),
    volume_24h DECIMAL(20,8),
    market_cap BIGINT,
    market_cap_rank INTEGER,
    high_24h DECIMAL(20,8),
    low_24h DECIMAL(20,8),
    ath DECIMAL(20,8), -- All time high
    ath_date TIMESTAMP,
    atl DECIMAL(20,8), -- All time low
    atl_date TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(crypto_id)
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_crypto_prices_crypto_datetime ON crypto_prices(crypto_id, datetime DESC);
CREATE INDEX IF NOT EXISTS idx_crypto_prices_datetime ON crypto_prices(datetime DESC);
CREATE INDEX IF NOT EXISTS idx_crypto_prices_symbol_interval ON crypto_prices(crypto_id, interval_type, datetime DESC);
CREATE INDEX IF NOT EXISTS idx_cryptocurrencies_symbol ON cryptocurrencies(symbol);
CREATE INDEX IF NOT EXISTS idx_cryptocurrencies_binance_symbol ON cryptocurrencies(binance_symbol);
CREATE INDEX IF NOT EXISTS idx_cryptocurrencies_active ON cryptocurrencies(is_active);
CREATE INDEX IF NOT EXISTS idx_crypto_market_stats_rank ON crypto_market_stats(market_cap_rank);

-- Insert default crypto data sources
INSERT INTO crypto_data_sources (source_name, api_endpoint, status, rate_limit_per_minute) VALUES 
('Binance', 'https://api.binance.com/api/v3/', 'active', 1200),
('CoinGecko', 'https://api.coingecko.com/api/v3/', 'active', 50)
ON CONFLICT DO NOTHING;

-- Insert top cryptocurrencies (top 50 by market cap as of 2024)
INSERT INTO cryptocurrencies (symbol, name, base_asset, quote_asset, binance_symbol, rank_position) VALUES
('BTCUSDT', 'Bitcoin', 'BTC', 'USDT', 'BTCUSDT', 1),
('ETHUSDT', 'Ethereum', 'ETH', 'USDT', 'ETHUSDT', 2),
('BNBUSDT', 'BNB', 'BNB', 'USDT', 'BNBUSDT', 3),
('XRPUSDT', 'XRP', 'XRP', 'USDT', 'XRPUSDT', 4),
('SOLUSDT', 'Solana', 'SOL', 'USDT', 'SOLUSDT', 5),
('ADAUSDT', 'Cardano', 'ADA', 'USDT', 'ADAUSDT', 6),
('DOGEUSDT', 'Dogecoin', 'DOGE', 'USDT', 'DOGEUSDT', 7),
('TRXUSDT', 'TRON', 'TRX', 'USDT', 'TRXUSDT', 8),
('MATICUSDT', 'Polygon', 'MATIC', 'USDT', 'MATICUSDT', 9),
('TONUSDT', 'Toncoin', 'TON', 'USDT', 'TONUSDT', 10),
('LINKUSDT', 'Chainlink', 'LINK', 'USDT', 'LINKUSDT', 11),
('AVAXUSDT', 'Avalanche', 'AVAX', 'USDT', 'AVAXUSDT', 12),
('SHIBUSDT', 'Shiba Inu', 'SHIB', 'USDT', 'SHIBUSDT', 13),
('XLMUSDT', 'Stellar', 'XLM', 'USDT', 'XLMUSDT', 14),
('BCHUSDT', 'Bitcoin Cash', 'BCH', 'USDT', 'BCHUSDT', 15),
('DOTUSDT', 'Polkadot', 'DOT', 'USDT', 'DOTUSDT', 16),
('LTCUSDT', 'Litecoin', 'LTC', 'USDT', 'LTCUSDT', 17),
('UNIUSDT', 'Uniswap', 'UNI', 'USDT', 'UNIUSDT', 18),
('NEARUSDT', 'NEAR Protocol', 'NEAR', 'USDT', 'NEARUSDT', 19),
('ICPUSDT', 'Internet Computer', 'ICP', 'USDT', 'ICPUSDT', 20),
('APTUSDT', 'Aptos', 'APT', 'USDT', 'APTUSDT', 21),
('ATOMUSDT', 'Cosmos', 'ATOM', 'USDT', 'ATOMUSDT', 22),
('FILUSDT', 'Filecoin', 'FIL', 'USDT', 'FILUSDT', 23),
('VETUSDT', 'VeChain', 'VET', 'USDT', 'VETUSDT', 24),
('ETCUSDT', 'Ethereum Classic', 'ETC', 'USDT', 'ETCUSDT', 25),
('ALGOUSDT', 'Algorand', 'ALGO', 'USDT', 'ALGOUSDT', 26),
('HBARUSDT', 'Hedera', 'HBAR', 'USDT', 'HBARUSDT', 27),
('MANAUSDT', 'Decentraland', 'MANA', 'USDT', 'MANAUSDT', 28),
('SANDUSDT', 'The Sandbox', 'SAND', 'USDT', 'SANDUSDT', 29),
('EGLDUSDT', 'MultiversX', 'EGLD', 'USDT', 'EGLDUSDT', 30),
('FLOWUSDT', 'Flow', 'FLOW', 'USDT', 'FLOWUSDT', 31),
('XTZUSDT', 'Tezos', 'XTZ', 'USDT', 'XTZUSDT', 32),
('AXSUSDT', 'Axie Infinity', 'AXS', 'USDT', 'AXSUSDT', 33),
('THETAUSDT', 'THETA', 'THETA', 'USDT', 'THETAUSDT', 34),
('EOSUSDT', 'EOS', 'EOS', 'USDT', 'EOSUSDT', 35),
('AAVEUSDT', 'Aave', 'AAVE', 'USDT', 'AAVEUSDT', 36),
('GRTUSDT', 'The Graph', 'GRT', 'USDT', 'GRTUSDT', 37),
('FTMUSDT', 'Fantom', 'FTM', 'USDT', 'FTMUSDT', 38),
('XMRUSDT', 'Monero', 'XMR', 'USDT', 'XMRUSDT', 39),
('CAKEUSDT', 'PancakeSwap', 'CAKE', 'USDT', 'CAKEUSDT', 40),
('NEOUSDT', 'Neo', 'NEO', 'USDT', 'NEOUSDT', 41),
('QNTUSDT', 'Quant', 'QNT', 'USDT', 'QNTUSDT', 42),
('MINAUSDT', 'Mina', 'MINA', 'USDT', 'MINAUSDT', 43),
('CHZUSDT', 'Chiliz', 'CHZ', 'USDT', 'CHZUSDT', 44),
('ENJUSDT', 'Enjin Coin', 'ENJ', 'USDT', 'ENJUSDT', 45),
('MKRUSDT', 'Maker', 'MKR', 'USDT', 'MKRUSDT', 46),
('KLAYUSDT', 'Klaytn', 'KLAY', 'USDT', 'KLAYUSDT', 47),
('ZILUSDT', 'Zilliqa', 'ZIL', 'USDT', 'ZILUSDT', 48),
('BATUSDT', 'Basic Attention Token', 'BAT', 'USDT', 'BATUSDT', 49),
('DYDXUSDT', 'dYdX', 'DYDX', 'USDT', 'DYDXUSDT', 50)
ON CONFLICT (symbol) DO NOTHING;

-- Add user permissions for crypto features
INSERT INTO user_levels (level_name, level_code, permissions, description) VALUES
('Crypto Trader', 'crypto_trader', ARRAY['basic_access', 'crypto_view', 'crypto_data'], 'User with cryptocurrency market data access')
ON CONFLICT (level_code) DO NOTHING;

-- Update existing permissions to include crypto features for admins
UPDATE user_levels SET permissions = array_append(permissions, 'crypto_admin') 
WHERE level_code IN ('admin', 'super_admin') AND NOT ('crypto_admin' = ANY(permissions));

UPDATE user_levels SET permissions = array_append(permissions, 'crypto_view') 
WHERE level_code IN ('admin', 'super_admin', 'user') AND NOT ('crypto_view' = ANY(permissions));