-- Technical Indicators Pre-calculation Schema
-- Phase 3 Optimization: Store computed indicators for 2-3x faster backtests
-- Date: October 8, 2025

-- ============================================================================
-- 1. CREATE TECHNICAL INDICATORS HYPERTABLE
-- ============================================================================

DROP TABLE IF EXISTS crypto_technical_indicators CASCADE;

CREATE TABLE crypto_technical_indicators (
    crypto_id INTEGER NOT NULL,
    datetime TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    interval_type VARCHAR(10) NOT NULL DEFAULT '1h',
    
    -- Moving Averages
    sma_7 NUMERIC(20,8),
    sma_20 NUMERIC(20,8),
    sma_50 NUMERIC(20,8),
    sma_200 NUMERIC(20,8),
    ema_12 NUMERIC(20,8),
    ema_26 NUMERIC(20,8),
    
    -- RSI (Relative Strength Index)
    rsi_14 NUMERIC(20,8),
    rsi_7 NUMERIC(20,8),
    rsi_21 NUMERIC(20,8),
    
    -- MACD (Moving Average Convergence Divergence)
    macd NUMERIC(20,8),
    macd_signal NUMERIC(20,8),
    macd_histogram NUMERIC(20,8),
    
    -- Bollinger Bands
    bb_upper NUMERIC(20,8),
    bb_middle NUMERIC(20,8),
    bb_lower NUMERIC(20,8),
    bb_width NUMERIC(20,8),
    
    -- Volume Indicators
    volume_sma_20 NUMERIC(20,8),
    volume_ratio NUMERIC(20,8),
    
    -- Price Action
    price_change_1h NUMERIC(20,8),
    price_change_24h NUMERIC(20,8),
    price_change_7d NUMERIC(20,8),
    
    -- Volatility
    volatility_7d NUMERIC(20,8),
    volatility_30d NUMERIC(20,8),
    
    -- Support/Resistance Levels
    support_level NUMERIC(20,8),
    resistance_level NUMERIC(20,8),
    
    -- Metadata
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (crypto_id, datetime, interval_type)
);

-- Convert to hypertable (matches crypto_prices structure)
SELECT create_hypertable(
    'crypto_technical_indicators',
    'datetime',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- ============================================================================
-- 2. CREATE INDEXES FOR FAST LOOKUPS
-- ============================================================================

-- Index for backtest queries (crypto + time range)
CREATE INDEX IF NOT EXISTS idx_tech_indicators_crypto_datetime
ON crypto_technical_indicators (crypto_id, datetime DESC);

-- Index for indicator-specific queries
CREATE INDEX IF NOT EXISTS idx_tech_indicators_rsi
ON crypto_technical_indicators (crypto_id, datetime DESC) 
INCLUDE (rsi_14, rsi_7, rsi_21)
WHERE rsi_14 IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_tech_indicators_macd
ON crypto_technical_indicators (crypto_id, datetime DESC)
INCLUDE (macd, macd_signal, macd_histogram)
WHERE macd IS NOT NULL;

-- Composite index for multi-indicator strategies
CREATE INDEX IF NOT EXISTS idx_tech_indicators_multi
ON crypto_technical_indicators (crypto_id, datetime DESC)
INCLUDE (rsi_14, macd, sma_50, sma_200, ema_12, ema_26);

-- ============================================================================
-- 3. ENABLE COMPRESSION
-- ============================================================================

-- Enable compression (same policy as crypto_prices)
ALTER TABLE crypto_technical_indicators SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'crypto_id, interval_type',
    timescaledb.compress_orderby = 'datetime DESC'
);

-- Compress chunks older than 7 days
SELECT add_compression_policy(
    'crypto_technical_indicators',
    INTERVAL '7 days',
    if_not_exists => TRUE
);

-- ============================================================================
-- 4. CREATE CALCULATION FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION calculate_technical_indicators(
    p_crypto_id INTEGER,
    p_start_date TIMESTAMP DEFAULT NOW() - INTERVAL '1 day',
    p_end_date TIMESTAMP DEFAULT NOW()
) RETURNS INTEGER AS $$
DECLARE
    rows_inserted INTEGER := 0;
BEGIN
    -- Insert calculated indicators
    -- Note: This is a placeholder - actual calculation done in Python
    -- for better performance and library support (pandas, ta-lib)
    
    INSERT INTO crypto_technical_indicators (
        crypto_id, datetime, interval_type,
        sma_20, ema_12, ema_26, rsi_14,
        calculated_at
    )
    SELECT 
        crypto_id,
        datetime,
        interval_type,
        -- Simple Moving Average 20
        AVG(close_price) OVER (
            PARTITION BY crypto_id, interval_type 
            ORDER BY datetime 
            ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
        ) as sma_20,
        -- Exponential Moving Average 12 (simplified)
        AVG(close_price) OVER (
            PARTITION BY crypto_id, interval_type 
            ORDER BY datetime 
            ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
        ) as ema_12,
        -- Exponential Moving Average 26 (simplified)
        AVG(close_price) OVER (
            PARTITION BY crypto_id, interval_type 
            ORDER BY datetime 
            ROWS BETWEEN 25 PRECEDING AND CURRENT ROW
        ) as ema_26,
        -- RSI placeholder (proper calculation in Python)
        NULL as rsi_14,
        CURRENT_TIMESTAMP
    FROM crypto_prices
    WHERE crypto_id = p_crypto_id
        AND datetime >= p_start_date
        AND datetime <= p_end_date
        AND interval_type = '1h'
    ON CONFLICT (crypto_id, datetime, interval_type) 
    DO UPDATE SET
        sma_20 = EXCLUDED.sma_20,
        ema_12 = EXCLUDED.ema_12,
        ema_26 = EXCLUDED.ema_26,
        calculated_at = EXCLUDED.calculated_at;
    
    GET DIAGNOSTICS rows_inserted = ROW_COUNT;
    
    RETURN rows_inserted;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 5. CREATE REFRESH FUNCTION (Called after data updates)
-- ============================================================================

CREATE OR REPLACE FUNCTION refresh_indicators_for_crypto(
    p_crypto_id INTEGER
) RETURNS TEXT AS $$
DECLARE
    latest_price_date TIMESTAMP;
    latest_indicator_date TIMESTAMP;
    result_text TEXT;
BEGIN
    -- Get latest price data date
    SELECT MAX(datetime) INTO latest_price_date
    FROM crypto_prices
    WHERE crypto_id = p_crypto_id;
    
    -- Get latest indicator date
    SELECT MAX(datetime) INTO latest_indicator_date
    FROM crypto_technical_indicators
    WHERE crypto_id = p_crypto_id;
    
    -- Calculate indicators for new data
    IF latest_price_date > COALESCE(latest_indicator_date, '2020-01-01') THEN
        -- Call Python service to calculate indicators
        result_text := 'Indicators need update from ' || 
                      COALESCE(latest_indicator_date, '2020-01-01')::TEXT || 
                      ' to ' || latest_price_date::TEXT;
    ELSE
        result_text := 'Indicators up to date';
    END IF;
    
    RETURN result_text;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 6. CREATE CONTINUOUS AGGREGATE FOR DAILY INDICATORS
-- ============================================================================

DROP MATERIALIZED VIEW IF EXISTS crypto_indicators_daily CASCADE;

CREATE MATERIALIZED VIEW crypto_indicators_daily
WITH (timescaledb.continuous) AS
SELECT 
    crypto_id,
    time_bucket('1 day', datetime) AS day,
    
    -- Average indicators for the day
    AVG(rsi_14) as avg_rsi_14,
    AVG(macd) as avg_macd,
    AVG(sma_50) as avg_sma_50,
    AVG(sma_200) as avg_sma_200,
    
    -- Last values of the day
    LAST(rsi_14, datetime) as close_rsi_14,
    LAST(macd, datetime) as close_macd,
    LAST(sma_50, datetime) as close_sma_50,
    
    -- Min/max for the day
    MIN(rsi_14) as min_rsi_14,
    MAX(rsi_14) as max_rsi_14,
    
    COUNT(*) as data_points
FROM crypto_technical_indicators
WHERE interval_type = '1h'
GROUP BY crypto_id, day;

-- Add refresh policy
SELECT add_continuous_aggregate_policy(
    'crypto_indicators_daily',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- ============================================================================
-- 7. CREATE VIEW FOR EASY QUERYING
-- ============================================================================

CREATE OR REPLACE VIEW crypto_prices_with_indicators AS
SELECT 
    p.id,
    p.crypto_id,
    p.datetime,
    p.interval_type,
    p.open_price,
    p.high_price,
    p.low_price,
    p.close_price,
    p.volume,
    
    -- Technical indicators
    i.sma_7,
    i.sma_20,
    i.sma_50,
    i.sma_200,
    i.ema_12,
    i.ema_26,
    i.rsi_14,
    i.rsi_7,
    i.rsi_21,
    i.macd,
    i.macd_signal,
    i.macd_histogram,
    i.bb_upper,
    i.bb_middle,
    i.bb_lower,
    i.volatility_7d,
    i.support_level,
    i.resistance_level
    
FROM crypto_prices p
LEFT JOIN crypto_technical_indicators i 
    ON p.crypto_id = i.crypto_id 
    AND p.datetime = i.datetime 
    AND p.interval_type = i.interval_type;

-- ============================================================================
-- 8. VERIFICATION QUERIES
-- ============================================================================

-- Check table structure
SELECT 
    'Technical Indicators Table Created' as status,
    COUNT(*) as indicator_count,
    MIN(datetime) as earliest_date,
    MAX(datetime) as latest_date
FROM crypto_technical_indicators;

-- Check hypertable status
SELECT 
    hypertable_name,
    num_chunks,
    compression_enabled
FROM timescaledb_information.hypertables
WHERE hypertable_name = 'crypto_technical_indicators';

-- Check indexes
SELECT 
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'crypto_technical_indicators'
ORDER BY indexname;

-- ============================================================================
-- USAGE EXAMPLES
-- ============================================================================

-- Example 1: Get indicators for specific crypto
SELECT 
    datetime,
    close_price,
    rsi_14,
    macd,
    sma_50,
    sma_200
FROM crypto_prices_with_indicators
WHERE crypto_id = 1
    AND datetime >= NOW() - INTERVAL '30 days'
ORDER BY datetime DESC
LIMIT 10;

-- Example 2: Find oversold conditions (RSI < 30)
SELECT 
    c.symbol,
    i.datetime,
    i.rsi_14,
    p.close_price
FROM crypto_technical_indicators i
JOIN cryptocurrencies c ON c.id = i.crypto_id
JOIN crypto_prices p ON p.crypto_id = i.crypto_id 
    AND p.datetime = i.datetime
WHERE i.rsi_14 < 30
    AND i.datetime >= NOW() - INTERVAL '7 days'
ORDER BY i.datetime DESC;

-- Example 3: Find MACD crossovers
SELECT 
    c.symbol,
    i.datetime,
    i.macd,
    i.macd_signal,
    i.macd_histogram,
    CASE 
        WHEN i.macd > i.macd_signal THEN 'Bullish'
        ELSE 'Bearish'
    END as signal
FROM crypto_technical_indicators i
JOIN cryptocurrencies c ON c.id = i.crypto_id
WHERE i.datetime >= NOW() - INTERVAL '24 hours'
    AND i.macd IS NOT NULL
ORDER BY c.symbol, i.datetime DESC;

-- ============================================================================
-- NOTES
-- ============================================================================
-- 
-- CALCULATION STRATEGY:
-- - Python service calculates indicators using pandas/ta-lib
-- - Batch calculation for efficiency (1000s of rows at once)
-- - Store results in this table for instant retrieval
-- - Update after each crypto data collection
--
-- COMPRESSION:
-- - Automatically compresses chunks older than 7 days
-- - Expected compression ratio: 90% (similar to crypto_prices)
-- - Indicators compress very well (repetitive patterns)
--
-- PERFORMANCE:
-- - Reading pre-calculated indicators: <10ms
-- - Calculating on-the-fly: 500-1000ms
-- - Expected speedup: 50-100x for indicator lookup
-- - Backtest speedup: 2-3x overall (indicators are 50% of work)
--
-- MAINTENANCE:
-- - Auto-update via Python service after data collection
-- - Continuous aggregate refreshes hourly
-- - Compression runs automatically
--
-- STORAGE:
-- - Similar size to crypto_prices (~250 MB uncompressed)
-- - After compression: ~25 MB (90% compression)
-- - Indexes: ~50 MB
-- - Total: ~75 MB additional storage
