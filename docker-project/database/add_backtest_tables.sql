-- Add backtesting strategy tables
-- This creates the schema to store and manage dynamic backtesting strategies

-- Table to store different backtesting strategies
CREATE TABLE IF NOT EXISTS backtest_strategies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    parameters JSONB NOT NULL, -- Store strategy parameters as JSON
    category VARCHAR(50) DEFAULT 'technical', -- technical, fundamental, etc.
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table to store backtest results for each strategy-crypto combination
CREATE TABLE IF NOT EXISTS backtest_results (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER REFERENCES backtest_strategies(id) ON DELETE CASCADE,
    crypto_id INTEGER REFERENCES cryptocurrencies(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    strategy_parameters JSONB NOT NULL,
    
    -- Performance metrics
    initial_investment DECIMAL(15,2) NOT NULL,
    final_value DECIMAL(15,2) NOT NULL,
    total_return DECIMAL(10,4) NOT NULL, -- percentage
    total_trades INTEGER DEFAULT 0,
    profitable_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    win_rate DECIMAL(5,2) DEFAULT 0, -- percentage
    
    -- Time period
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    days_invested INTEGER NOT NULL,
    
    -- Additional metrics
    max_drawdown DECIMAL(10,4), -- percentage
    sharpe_ratio DECIMAL(8,4),
    volatility DECIMAL(10,4), -- percentage
    avg_holding_days DECIMAL(8,2),
    
    -- Trade details (JSON array of trade objects)
    trade_history JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_backtest_results_strategy ON backtest_results(strategy_id);
CREATE INDEX IF NOT EXISTS idx_backtest_results_crypto ON backtest_results(crypto_id);
CREATE INDEX IF NOT EXISTS idx_backtest_results_return ON backtest_results(total_return DESC);
CREATE INDEX IF NOT EXISTS idx_backtest_strategies_active ON backtest_strategies(is_active);

-- Insert default strategies
INSERT INTO backtest_strategies (name, description, parameters, category) VALUES
('Simple Moving Average Crossover', 'Buy when short MA crosses above long MA, sell when it crosses below', 
 '{"short_period": {"type": "integer", "default": 10, "min": 5, "max": 50, "description": "Short MA period (days)"}, 
   "long_period": {"type": "integer", "default": 30, "min": 10, "max": 200, "description": "Long MA period (days)"}}',
 'technical'),

('RSI Oversold/Overbought', 'Buy when RSI is oversold, sell when overbought', 
 '{"rsi_period": {"type": "integer", "default": 14, "min": 5, "max": 30, "description": "RSI calculation period"}, 
   "oversold_threshold": {"type": "integer", "default": 30, "min": 10, "max": 40, "description": "Oversold threshold"}, 
   "overbought_threshold": {"type": "integer", "default": 70, "min": 60, "max": 90, "description": "Overbought threshold"}}',
 'technical'),

('Bollinger Bands', 'Buy when price touches lower band, sell when it touches upper band', 
 '{"period": {"type": "integer", "default": 20, "min": 10, "max": 50, "description": "Bollinger Bands period"}, 
   "std_multiplier": {"type": "float", "default": 2.0, "min": 1.0, "max": 3.0, "description": "Standard deviation multiplier"}}',
 'technical'),

('MACD Signal', 'Buy on MACD bullish crossover, sell on bearish crossover', 
 '{"fast_period": {"type": "integer", "default": 12, "min": 5, "max": 20, "description": "Fast EMA period"}, 
   "slow_period": {"type": "integer", "default": 26, "min": 15, "max": 40, "description": "Slow EMA period"}, 
   "signal_period": {"type": "integer", "default": 9, "min": 5, "max": 15, "description": "Signal line period"}}',
 'technical'),

('Support and Resistance', 'Buy at support levels, sell at resistance levels', 
 '{"lookback_period": {"type": "integer", "default": 50, "min": 20, "max": 100, "description": "Lookback period for S/R calculation"}, 
   "min_touches": {"type": "integer", "default": 3, "min": 2, "max": 5, "description": "Minimum touches to confirm S/R level"}, 
   "break_threshold": {"type": "float", "default": 0.02, "min": 0.01, "max": 0.05, "description": "Break threshold (percentage)"}}',
 'technical')
ON CONFLICT (name) DO NOTHING;

-- Grant permissions (adjust as needed)
-- GRANT ALL PRIVILEGES ON backtest_strategies TO your_app_user;
-- GRANT ALL PRIVILEGES ON backtest_results TO your_app_user;