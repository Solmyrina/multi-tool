-- Initialize database for webapp
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table for authentication
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP WITH TIME ZONE
);

-- Login attempts table for security logging
CREATE TABLE login_attempts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50),
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN NOT NULL,
    attempted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    failure_reason VARCHAR(100)
);

-- Sessions table for user sessions
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create indexes for better performance
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_login_attempts_username ON login_attempts(username);
CREATE INDEX idx_login_attempts_attempted_at ON login_attempts(attempted_at);
CREATE INDEX idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);

-- User levels and permissions table
CREATE TABLE user_levels (
    id SERIAL PRIMARY KEY,
    level_name VARCHAR(50) UNIQUE NOT NULL,
    level_code VARCHAR(20) UNIQUE NOT NULL,
    permissions TEXT[] DEFAULT '{}',
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add user_level_id to users table
ALTER TABLE users ADD COLUMN user_level_id INTEGER REFERENCES user_levels(id) DEFAULT 4;

-- Insert user levels
INSERT INTO user_levels (level_name, level_code, permissions, description) VALUES
('Super Admin', 'super_admin', ARRAY['all'], 'Full system access'),
('Admin', 'admin', ARRAY['basic_access', 'user_management', 'admin_access', 'stock_admin', 'stock_view'], 'Administrative access'),
('Moderator', 'moderator', ARRAY['basic_access', 'user_view'], 'Limited administrative access'),
('User', 'user', ARRAY['basic_access', 'stock_view'], 'Standard user access'),
('Stock Trader', 'trader', ARRAY['basic_access', 'stock_view', 'stock_data'], 'User with stock market data access');

-- Stock market data tables
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

-- Additional indexes for stock data
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

-- Insert a default admin user (password: admin123) with admin level
INSERT INTO users (username, email, password_hash, user_level_id) VALUES 
('admin', 'admin@example.com', '$2b$12$XeG8uxI94ZsHzIpD0qZO6OJcYutTrbtvg1zlE5v3CvQsqmyIgNLyi', 2)
ON CONFLICT (username) DO UPDATE SET user_level_id = 2;