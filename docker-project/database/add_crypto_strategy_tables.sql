-- Cryptocurrency Strategy Backtesting Schema
-- This schema allows dynamic strategy creation and parameter configuration

-- Strategy definitions table
CREATE TABLE IF NOT EXISTS crypto_strategies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    strategy_type VARCHAR(50) NOT NULL, -- 'technical', 'momentum', 'mean_reversion', etc.
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Strategy parameters table (dynamic parameters for each strategy)
CREATE TABLE IF NOT EXISTS crypto_strategy_parameters (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER REFERENCES crypto_strategies(id) ON DELETE CASCADE,
    parameter_name VARCHAR(50) NOT NULL,
    parameter_type VARCHAR(20) NOT NULL, -- 'number', 'percentage', 'integer', 'boolean'
    default_value VARCHAR(50),
    min_value DECIMAL(15,8),
    max_value DECIMAL(15,8),
    description TEXT,
    display_order INTEGER DEFAULT 0
);

-- Backtesting results cache table
CREATE TABLE IF NOT EXISTS crypto_backtest_results (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER REFERENCES crypto_strategies(id) ON DELETE CASCADE,
    cryptocurrency_id INTEGER REFERENCES cryptocurrencies(id) ON DELETE CASCADE,
    parameters_hash VARCHAR(64) NOT NULL, -- MD5 hash of parameters for caching
    initial_investment DECIMAL(15,2) NOT NULL,
    final_value DECIMAL(15,2) NOT NULL,
    total_return_percentage DECIMAL(10,4),
    total_trades INTEGER DEFAULT 0,
    profitable_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    buy_and_hold_return DECIMAL(10,4),
    strategy_vs_hold_difference DECIMAL(10,4),
    max_drawdown DECIMAL(10,4),
    total_fees DECIMAL(15,2) DEFAULT 0,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    calculation_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial strategies
INSERT INTO crypto_strategies (name, description, strategy_type) VALUES
('RSI Buy/Sell', 'Buy when RSI drops below oversold threshold, sell when RSI rises above overbought threshold', 'technical'),
('Moving Average Crossover', 'Buy when short MA crosses above long MA, sell when short MA crosses below long MA', 'technical'),
('Price Momentum', 'Buy after X% price increase, sell after Y% price increase or Z% loss', 'momentum'),
('Support/Resistance', 'Buy at support levels, sell at resistance levels based on recent price action', 'technical'),
('Bollinger Bands', 'Buy when price touches lower band, sell when price touches upper band', 'technical'),
('Mean Reversion', 'Buy when price deviates X% below moving average, sell when it returns to average', 'mean_reversion')
ON CONFLICT (name) DO NOTHING;

-- Insert parameters for RSI Strategy
INSERT INTO crypto_strategy_parameters (strategy_id, parameter_name, parameter_type, default_value, min_value, max_value, description, display_order) 
SELECT id, 'rsi_period', 'integer', '14', 5, 50, 'RSI calculation period (days)', 1
FROM crypto_strategies WHERE name = 'RSI Buy/Sell';

INSERT INTO crypto_strategy_parameters (strategy_id, parameter_name, parameter_type, default_value, min_value, max_value, description, display_order) 
SELECT id, 'oversold_threshold', 'number', '30', 10, 40, 'RSI oversold threshold (buy signal)', 2
FROM crypto_strategies WHERE name = 'RSI Buy/Sell';

INSERT INTO crypto_strategy_parameters (strategy_id, parameter_name, parameter_type, default_value, min_value, max_value, description, display_order) 
SELECT id, 'overbought_threshold', 'number', '70', 60, 90, 'RSI overbought threshold (sell signal)', 3
FROM crypto_strategies WHERE name = 'RSI Buy/Sell';

-- Insert parameters for Moving Average Crossover Strategy
INSERT INTO crypto_strategy_parameters (strategy_id, parameter_name, parameter_type, default_value, min_value, max_value, description, display_order) 
SELECT id, 'short_ma_period', 'integer', '10', 5, 50, 'Short moving average period (days)', 1
FROM crypto_strategies WHERE name = 'Moving Average Crossover';

INSERT INTO crypto_strategy_parameters (strategy_id, parameter_name, parameter_type, default_value, min_value, max_value, description, display_order) 
SELECT id, 'long_ma_period', 'integer', '30', 10, 200, 'Long moving average period (days)', 2
FROM crypto_strategies WHERE name = 'Moving Average Crossover';

-- Insert parameters for Price Momentum Strategy
INSERT INTO crypto_strategy_parameters (strategy_id, parameter_name, parameter_type, default_value, min_value, max_value, description, display_order) 
SELECT id, 'buy_threshold', 'percentage', '5', -50, 50, 'Price change % to trigger buy (positive = momentum, negative = dip)', 1
FROM crypto_strategies WHERE name = 'Price Momentum';

INSERT INTO crypto_strategy_parameters (strategy_id, parameter_name, parameter_type, default_value, min_value, max_value, description, display_order) 
SELECT id, 'buy_threshold_window_hours', 'integer', '24', 1, 168, 'Hours over which the price increase must occur', 2
FROM crypto_strategies WHERE name = 'Price Momentum';

INSERT INTO crypto_strategy_parameters (strategy_id, parameter_name, parameter_type, default_value, min_value, max_value, description, display_order) 
SELECT id, 'sell_profit_threshold', 'percentage', '15', 5, 100, 'Price increase % to trigger profit sell', 3
FROM crypto_strategies WHERE name = 'Price Momentum';

INSERT INTO crypto_strategy_parameters (strategy_id, parameter_name, parameter_type, default_value, min_value, max_value, description, display_order) 
SELECT id, 'stop_loss_threshold', 'percentage', '10', 2, 25, 'Price decrease % to trigger stop loss', 4
FROM crypto_strategies WHERE name = 'Price Momentum';

-- Insert parameters for Bollinger Bands Strategy  
INSERT INTO crypto_strategy_parameters (strategy_id, parameter_name, parameter_type, default_value, min_value, max_value, description, display_order) 
SELECT id, 'ma_period', 'integer', '20', 10, 50, 'Moving average period for bands', 1
FROM crypto_strategies WHERE name = 'Bollinger Bands';

INSERT INTO crypto_strategy_parameters (strategy_id, parameter_name, parameter_type, default_value, min_value, max_value, description, display_order) 
SELECT id, 'std_multiplier', 'number', '2', 1, 3, 'Standard deviation multiplier', 2
FROM crypto_strategies WHERE name = 'Bollinger Bands';

-- Insert parameters for Mean Reversion Strategy
INSERT INTO crypto_strategy_parameters (strategy_id, parameter_name, parameter_type, default_value, min_value, max_value, description, display_order) 
SELECT id, 'ma_period', 'integer', '50', 10, 200, 'Moving average period', 1
FROM crypto_strategies WHERE name = 'Mean Reversion';

INSERT INTO crypto_strategy_parameters (strategy_id, parameter_name, parameter_type, default_value, min_value, max_value, description, display_order) 
SELECT id, 'deviation_threshold', 'percentage', '15', 5, 30, 'Deviation from MA to trigger buy', 2
FROM crypto_strategies WHERE name = 'Mean Reversion';

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_backtest_results_strategy_crypto ON crypto_backtest_results(strategy_id, cryptocurrency_id);
CREATE INDEX IF NOT EXISTS idx_backtest_results_hash ON crypto_backtest_results(parameters_hash);
CREATE INDEX IF NOT EXISTS idx_strategy_parameters_strategy ON crypto_strategy_parameters(strategy_id, display_order);

-- Add initial investment amount as a global parameter
INSERT INTO crypto_strategy_parameters (strategy_id, parameter_name, parameter_type, default_value, min_value, max_value, description, display_order) 
SELECT id, 'initial_investment', 'number', '1000', 100, 100000, 'Initial investment amount ($)', 0
FROM crypto_strategies WHERE name IN ('RSI Buy/Sell', 'Moving Average Crossover', 'Price Momentum', 'Bollinger Bands', 'Mean Reversion');

-- Add transaction fee parameter
INSERT INTO crypto_strategy_parameters (strategy_id, parameter_name, parameter_type, default_value, min_value, max_value, description, display_order) 
SELECT id, 'transaction_fee', 'percentage', '0.1', 0, 2, 'Transaction fee per trade (%)', 99
FROM crypto_strategies WHERE name IN ('RSI Buy/Sell', 'Moving Average Crossover', 'Price Momentum', 'Bollinger Bands', 'Mean Reversion');