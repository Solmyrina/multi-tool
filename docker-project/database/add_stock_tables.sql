-- Stock market data tables
-- Add to existing init.sql or run separately

-- Create stocks table to store different stocks/symbols
CREATE TABLE IF NOT EXISTS stocks (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    exchange VARCHAR(50) NOT NULL DEFAULT 'NASDAQ',
    currency VARCHAR(3) DEFAULT 'USD',
    sector VARCHAR(100),
    industry VARCHAR(100),
    market_cap BIGINT,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create stock_prices table for historical price data
CREATE TABLE IF NOT EXISTS stock_prices (
    id BIGSERIAL PRIMARY KEY,
    stock_id INTEGER REFERENCES stocks(id) ON DELETE CASCADE,
    datetime TIMESTAMP NOT NULL,
    open_price DECIMAL(12,4) NOT NULL,
    high_price DECIMAL(12,4) NOT NULL,
    low_price DECIMAL(12,4) NOT NULL,
    close_price DECIMAL(12,4) NOT NULL,
    adjusted_close DECIMAL(12,4),
    volume BIGINT NOT NULL DEFAULT 0,
    interval_type VARCHAR(10) DEFAULT '1h', -- 1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_id, datetime, interval_type)
);

-- Create data_sources table to track data fetching
CREATE TABLE IF NOT EXISTS data_sources (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(50) NOT NULL,
    api_endpoint VARCHAR(255),
    last_fetch TIMESTAMP,
    total_records BIGINT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active', -- active, inactive, error
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create stock_fetch_logs table for monitoring data collection
CREATE TABLE IF NOT EXISTS stock_fetch_logs (
    id BIGSERIAL PRIMARY KEY,
    stock_id INTEGER REFERENCES stocks(id) ON DELETE CASCADE,
    data_source_id INTEGER REFERENCES data_sources(id),
    fetch_start TIMESTAMP NOT NULL,
    fetch_end TIMESTAMP,
    records_fetched INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending', -- pending, success, error, partial
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_stock_prices_stock_datetime ON stock_prices(stock_id, datetime DESC);
CREATE INDEX IF NOT EXISTS idx_stock_prices_datetime ON stock_prices(datetime DESC);
CREATE INDEX IF NOT EXISTS idx_stock_prices_symbol_interval ON stock_prices(stock_id, interval_type, datetime DESC);
CREATE INDEX IF NOT EXISTS idx_stocks_symbol ON stocks(symbol);
CREATE INDEX IF NOT EXISTS idx_stocks_active ON stocks(is_active);

-- Insert default data sources
INSERT INTO data_sources (source_name, api_endpoint, status) VALUES 
('Yahoo Finance', 'https://query1.finance.yahoo.com/v8/finance/chart/', 'active'),
('Alpha Vantage', 'https://www.alphavantage.co/query', 'inactive')
ON CONFLICT DO NOTHING;

-- Insert NASDAQ index symbol
INSERT INTO stocks (symbol, name, exchange, description) VALUES 
('^IXIC', 'NASDAQ Composite Index', 'NASDAQ', 'The NASDAQ Composite Index is a stock market index that includes almost all stocks listed on the Nasdaq stock exchange.')
ON CONFLICT (symbol) DO NOTHING;

-- Add user permissions for stock features
INSERT INTO user_levels (level_name, level_code, permissions, description) VALUES
('Stock Trader', 'trader', ARRAY['basic_access', 'stock_view', 'stock_data'], 'User with stock market data access')
ON CONFLICT (level_code) DO NOTHING;

-- Update existing permissions to include stock features for admins
UPDATE user_levels SET permissions = array_append(permissions, 'stock_admin') 
WHERE level_code IN ('admin', 'super_admin') AND NOT ('stock_admin' = ANY(permissions));

UPDATE user_levels SET permissions = array_append(permissions, 'stock_view') 
WHERE level_code IN ('admin', 'super_admin', 'user') AND NOT ('stock_view' = ANY(permissions));