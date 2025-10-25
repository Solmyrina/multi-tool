-- ============================================================================
-- Add Support/Resistance Strategy Parameters
-- ============================================================================
-- Purpose: Add missing parameters for Support/Resistance strategy
-- Created: October 8, 2025
-- ============================================================================

-- Add parameters for Support/Resistance Strategy
INSERT INTO crypto_strategy_parameters (strategy_id, parameter_name, parameter_type, default_value, min_value, max_value, description, display_order) 
SELECT id, 'initial_investment', 'number', '1000', 100, 1000000, 'Initial investment amount ($)', 1
FROM crypto_strategies WHERE name = 'Support/Resistance'
ON CONFLICT DO NOTHING;

INSERT INTO crypto_strategy_parameters (strategy_id, parameter_name, parameter_type, default_value, min_value, max_value, description, display_order) 
SELECT id, 'lookback_period', 'integer', '50', 20, 100, 'Lookback period for support/resistance calculation (days)', 2
FROM crypto_strategies WHERE name = 'Support/Resistance'
ON CONFLICT DO NOTHING;

INSERT INTO crypto_strategy_parameters (strategy_id, parameter_name, parameter_type, default_value, min_value, max_value, description, display_order) 
SELECT id, 'min_touches', 'integer', '3', 2, 5, 'Minimum price touches to confirm support/resistance level', 3
FROM crypto_strategies WHERE name = 'Support/Resistance'
ON CONFLICT DO NOTHING;

INSERT INTO crypto_strategy_parameters (strategy_id, parameter_name, parameter_type, default_value, min_value, max_value, description, display_order) 
SELECT id, 'break_threshold', 'percentage', '2', 0.5, 5, 'Price break threshold to trigger buy/sell (%)', 4
FROM crypto_strategies WHERE name = 'Support/Resistance'
ON CONFLICT DO NOTHING;

INSERT INTO crypto_strategy_parameters (strategy_id, parameter_name, parameter_type, default_value, min_value, max_value, description, display_order) 
SELECT id, 'stop_loss_threshold', 'number', '10', 1, 50, 'Maximum acceptable loss (%)', 5
FROM crypto_strategies WHERE name = 'Support/Resistance'
ON CONFLICT DO NOTHING;

INSERT INTO crypto_strategy_parameters (strategy_id, parameter_name, parameter_type, default_value, min_value, max_value, description, display_order) 
SELECT id, 'cooldown_unit', 'text', 'hours', NULL, NULL, 'Cooldown period unit (hours/days)', 6
FROM crypto_strategies WHERE name = 'Support/Resistance'
ON CONFLICT DO NOTHING;

INSERT INTO crypto_strategy_parameters (strategy_id, parameter_name, parameter_type, default_value, min_value, max_value, description, display_order) 
SELECT id, 'cooldown_value', 'integer', '24', 0, 168, 'Cooldown period value (0 = no cooldown)', 7
FROM crypto_strategies WHERE name = 'Support/Resistance'
ON CONFLICT DO NOTHING;

INSERT INTO crypto_strategy_parameters (strategy_id, parameter_name, parameter_type, default_value, min_value, max_value, description, display_order) 
SELECT id, 'transaction_fee', 'percentage', '0.1', 0, 5, 'Transaction fee per trade (%)', 8
FROM crypto_strategies WHERE name = 'Support/Resistance'
ON CONFLICT DO NOTHING;

-- Verify parameters were added
SELECT s.name, COUNT(p.id) as parameter_count
FROM crypto_strategies s
LEFT JOIN crypto_strategy_parameters p ON s.id = p.strategy_id
WHERE s.name = 'Support/Resistance'
GROUP BY s.name;
