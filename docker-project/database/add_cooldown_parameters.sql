-- Add cooldown period parameters to all strategies

-- Cooldown value parameter (number of hours/days)
INSERT INTO crypto_strategy_parameters (strategy_id, parameter_name, parameter_type, default_value, min_value, max_value, description, display_order) 
SELECT id, 'cooldown_value', 'integer', '0', 0, 168, 'Cooldown period length (0 = disabled)', 98
FROM crypto_strategies 
WHERE name IN ('RSI Buy/Sell', 'Moving Average Crossover', 'Price Momentum', 'Bollinger Bands', 'Mean Reversion')
ON CONFLICT DO NOTHING;

-- Cooldown unit parameter (hours or days)
INSERT INTO crypto_strategy_parameters (strategy_id, parameter_name, parameter_type, default_value, min_value, max_value, description, display_order) 
SELECT id, 'cooldown_unit', 'text', 'hours', NULL, NULL, 'Cooldown period unit (hours/days)', 97
FROM crypto_strategies 
WHERE name IN ('RSI Buy/Sell', 'Moving Average Crossover', 'Price Momentum', 'Bollinger Bands', 'Mean Reversion')
ON CONFLICT DO NOTHING;
