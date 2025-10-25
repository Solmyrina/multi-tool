DO $$
DECLARE
    momentum_id INTEGER;
BEGIN
    SELECT id INTO momentum_id FROM crypto_strategies WHERE name = 'Price Momentum';
    IF momentum_id IS NOT NULL THEN
        IF NOT EXISTS (
            SELECT 1
            FROM crypto_strategy_parameters
            WHERE strategy_id = momentum_id
              AND parameter_name = 'buy_threshold_window_hours'
        ) THEN
            -- Shift existing display order to make room for the new parameter
            UPDATE crypto_strategy_parameters
            SET display_order = display_order + 1
            WHERE strategy_id = momentum_id
              AND display_order >= 2;

            -- Insert the new time window parameter for the buy threshold
            INSERT INTO crypto_strategy_parameters (
                strategy_id,
                parameter_name,
                parameter_type,
                default_value,
                min_value,
                max_value,
                description,
                display_order
            ) VALUES (
                momentum_id,
                'buy_threshold_window_hours',
                'integer',
                '24',
                1,
                168,
                'Hours over which the price increase must occur',
                2
            );
                END IF;

                -- Ensure buy threshold parameter allows negative values and updated description
                UPDATE crypto_strategy_parameters
                SET min_value = -50,
                        max_value = 50,
                        description = 'Price change % to trigger buy (positive = momentum, negative = dip)'
                WHERE strategy_id = momentum_id
                    AND parameter_name = 'buy_threshold';

                -- Refresh description for the window parameter to cover gains or dips
                UPDATE crypto_strategy_parameters
                SET description = 'Hours over which the price change must occur'
                WHERE strategy_id = momentum_id
                    AND parameter_name = 'buy_threshold_window_hours';
    END IF;
END $$;
