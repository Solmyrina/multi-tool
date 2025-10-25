-- Add stop_loss_threshold parameter to strategies that don't have it
-- Strategy 1: RSI Buy/Sell
-- Strategy 2: Moving Average Crossover
-- Strategy 5: Bollinger Bands
-- Strategy 6: Mean Reversion

-- RSI Buy/Sell (strategy_id = 1)
INSERT INTO crypto_strategy_parameters (
    strategy_id, parameter_name, parameter_type, default_value,
    min_value, max_value, description, display_order
) VALUES (
    1, 'stop_loss_threshold', 'number', '10',
    '1', '50', 'Stop loss threshold (%) - Exit position if loss exceeds this percentage', 50
);

-- Moving Average Crossover (strategy_id = 2)
INSERT INTO crypto_strategy_parameters (
    strategy_id, parameter_name, parameter_type, default_value,
    min_value, max_value, description, display_order
) VALUES (
    2, 'stop_loss_threshold', 'number', '10',
    '1', '50', 'Stop loss threshold (%) - Exit position if loss exceeds this percentage', 50
);

-- Bollinger Bands (strategy_id = 5)
INSERT INTO crypto_strategy_parameters (
    strategy_id, parameter_name, parameter_type, default_value,
    min_value, max_value, description, display_order
) VALUES (
    5, 'stop_loss_threshold', 'number', '10',
    '1', '50', 'Stop loss threshold (%) - Exit position if loss exceeds this percentage', 50
);

-- Mean Reversion (strategy_id = 6)
INSERT INTO crypto_strategy_parameters (
    strategy_id, parameter_name, parameter_type, default_value,
    min_value, max_value, description, display_order
) VALUES (
    6, 'stop_loss_threshold', 'number', '10',
    '1', '50', 'Stop loss threshold (%) - Exit position if loss exceeds this percentage', 50
);
