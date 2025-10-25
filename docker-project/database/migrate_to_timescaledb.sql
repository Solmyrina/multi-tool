-- ============================================================================
-- TimescaleDB Migration for Crypto Prices
-- ============================================================================
-- Purpose: Convert crypto_prices table to TimescaleDB hypertable
-- Expected improvement: 2-3x query speedup, 50-70% storage reduction
-- Created: October 8, 2025
-- ============================================================================

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Verify TimescaleDB is available
SELECT default_version FROM pg_available_extensions WHERE name = 'timescaledb';

-- ============================================================================
-- STEP 1: Create temporary table for migration
-- ============================================================================

-- Create new table with same structure as crypto_prices
CREATE TABLE crypto_prices_new (
    id BIGSERIAL,
    crypto_id INTEGER NOT NULL,
    datetime TIMESTAMP NOT NULL,
    open_price NUMERIC(20,8) NOT NULL,
    high_price NUMERIC(20,8) NOT NULL,
    low_price NUMERIC(20,8) NOT NULL,
    close_price NUMERIC(20,8) NOT NULL,
    volume NUMERIC(20,8) NOT NULL DEFAULT 0,
    quote_asset_volume NUMERIC(20,8) NOT NULL DEFAULT 0,
    number_of_trades INTEGER DEFAULT 0,
    taker_buy_base_asset_volume NUMERIC(20,8) DEFAULT 0,
    taker_buy_quote_asset_volume NUMERIC(20,8) DEFAULT 0,
    interval_type VARCHAR(10) DEFAULT '1h',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

\echo 'Step 1: Temporary table created';

-- ============================================================================
-- STEP 2: Convert to hypertable BEFORE inserting data
-- ============================================================================

-- Convert crypto_prices_new to hypertable
-- Partition by time (datetime column) with 7-day chunks
SELECT create_hypertable(
    'crypto_prices_new',
    'datetime',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- Add dimension for crypto_id (space partitioning)
-- This allows parallel queries across different cryptocurrencies
SELECT add_dimension(
    'crypto_prices_new',
    'crypto_id',
    number_partitions => 4
);

\echo 'Step 2: Hypertable created successfully!';

-- ============================================================================
-- STEP 3: Migrate data from old table to new hypertable
-- ============================================================================

-- Insert all data (this may take a few minutes)
-- TimescaleDB will automatically partition into chunks
\echo 'Step 3: Starting data migration... (this may take 2-5 minutes)';

INSERT INTO crypto_prices_new 
    (crypto_id, datetime, open_price, high_price, low_price, close_price, 
     volume, quote_asset_volume, number_of_trades, 
     taker_buy_base_asset_volume, taker_buy_quote_asset_volume, 
     interval_type, created_at)
SELECT 
    crypto_id, datetime, open_price, high_price, low_price, close_price,
    volume, quote_asset_volume, number_of_trades,
    taker_buy_base_asset_volume, taker_buy_quote_asset_volume,
    interval_type, created_at
FROM crypto_prices
ORDER BY datetime, crypto_id;

\echo 'Step 3: Data migration complete!';

-- Verify migration
\echo 'Verifying data migration...';
SELECT 
    (SELECT COUNT(*) FROM crypto_prices) as old_count,
    (SELECT COUNT(*) FROM crypto_prices_new) as new_count,
    (SELECT COUNT(*) FROM crypto_prices) = (SELECT COUNT(*) FROM crypto_prices_new) as counts_match;

-- ============================================================================
-- STEP 4: Add indexes to hypertable
-- ============================================================================

\echo 'Step 4: Creating indexes...';

-- Unique constraint (prevents duplicates)
CREATE UNIQUE INDEX idx_crypto_prices_new_unique 
    ON crypto_prices_new (crypto_id, datetime, interval_type);

-- Composite index for common queries
CREATE INDEX idx_crypto_prices_new_crypto_datetime 
    ON crypto_prices_new (crypto_id, interval_type, datetime DESC);

-- Index for time-range queries
CREATE INDEX idx_crypto_prices_new_datetime 
    ON crypto_prices_new (datetime DESC);

-- Index for specific interval types
CREATE INDEX idx_crypto_prices_new_interval 
    ON crypto_prices_new (interval_type, datetime DESC) 
    WHERE interval_type IN ('1h', '1d');

\echo 'Step 4: Indexes created successfully!';

-- ============================================================================
-- STEP 5: Enable compression
-- ============================================================================

\echo 'Step 5: Enabling compression...';

-- Enable compression with segmentby for better compression ratio
-- Segment by crypto_id so each crypto's data is compressed together
ALTER TABLE crypto_prices_new SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'crypto_id,interval_type',
    timescaledb.compress_orderby = 'datetime DESC'
);

-- Add compression policy: compress chunks older than 7 days
SELECT add_compression_policy('crypto_prices_new', INTERVAL '7 days');

\echo 'Step 5: Compression enabled! Chunks older than 7 days will be compressed automatically.';

-- ============================================================================
-- STEP 6: Create continuous aggregates for common queries
-- ============================================================================

\echo 'Step 6: Creating continuous aggregates...';

-- Daily aggregates (pre-computed OHLCV for each crypto per day)
CREATE MATERIALIZED VIEW crypto_prices_daily
WITH (timescaledb.continuous) AS
SELECT 
    crypto_id,
    interval_type,
    time_bucket('1 day', datetime) AS day,
    (array_agg(open_price ORDER BY datetime ASC))[1] AS open_price,
    MAX(high_price) AS high_price,
    MIN(low_price) AS low_price,
    (array_agg(close_price ORDER BY datetime DESC))[1] AS close_price,
    SUM(volume) AS volume,
    COUNT(*) AS data_points
FROM crypto_prices_new
GROUP BY crypto_id, interval_type, time_bucket('1 day', datetime);

-- Add refresh policy (update every hour)
SELECT add_continuous_aggregate_policy('crypto_prices_daily',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

\echo 'Daily continuous aggregate created!';

-- Weekly aggregates (for longer-term analysis)
CREATE MATERIALIZED VIEW crypto_prices_weekly
WITH (timescaledb.continuous) AS
SELECT 
    crypto_id,
    interval_type,
    time_bucket('1 week', datetime) AS week,
    (array_agg(open_price ORDER BY datetime ASC))[1] AS open_price,
    MAX(high_price) AS high_price,
    MIN(low_price) AS low_price,
    (array_agg(close_price ORDER BY datetime DESC))[1] AS close_price,
    SUM(volume) AS volume,
    COUNT(*) AS data_points
FROM crypto_prices_new
GROUP BY crypto_id, interval_type, time_bucket('1 week', datetime);

-- Add refresh policy
SELECT add_continuous_aggregate_policy('crypto_prices_weekly',
    start_offset => INTERVAL '1 month',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day');

\echo 'Step 6: Weekly continuous aggregate created!';

-- ============================================================================
-- STEP 7: Add retention policy (OPTIONAL - DISABLED BY DEFAULT)
-- ============================================================================

-- ⚠️  RETENTION POLICY IS DISABLED BY DEFAULT - ALL HOURLY DATA IS KEPT ⚠️
--
-- By default, this implementation keeps ALL hourly data forever.
-- The compression policy (above) saves 50-70% storage while keeping all data.
--
-- Only enable retention if you want to automatically delete old data.
-- Example: Keep only last 5 years of hourly data
-- 
-- UNCOMMENT ONLY IF YOU WANT TO DELETE OLD DATA:
-- SELECT add_retention_policy('crypto_prices_new', INTERVAL '5 years');
--
-- Note: Even with retention enabled, continuous aggregates (daily/weekly)
--       are preserved separately, so you keep historical summaries forever.

-- ============================================================================
-- STEP 8: Swap tables (zero downtime deployment)
-- ============================================================================

\echo 'Step 8: Swapping tables...';

BEGIN;

-- Drop foreign key constraints referencing crypto_prices
ALTER TABLE crypto_fetch_logs 
    DROP CONSTRAINT IF EXISTS crypto_fetch_logs_crypto_id_fkey;

-- Drop old indexes to avoid conflicts
DROP INDEX IF EXISTS idx_crypto_prices_crypto_datetime;
DROP INDEX IF EXISTS idx_crypto_prices_datetime;
DROP INDEX IF EXISTS idx_crypto_prices_symbol_interval;
DROP INDEX IF EXISTS idx_crypto_prices_crypto_datetime_opt;
DROP INDEX IF EXISTS idx_crypto_prices_datetime_crypto_opt;
DROP INDEX IF EXISTS idx_crypto_prices_crypto_interval_datetime_opt;
DROP INDEX IF EXISTS idx_crypto_prices_covering_opt;
DROP INDEX IF EXISTS idx_crypto_prices_unique;

-- Rename tables
ALTER TABLE crypto_prices RENAME TO crypto_prices_old;
ALTER TABLE crypto_prices_new RENAME TO crypto_prices;

-- Rename indexes to match original names
ALTER INDEX idx_crypto_prices_new_unique 
    RENAME TO idx_crypto_prices_unique;
ALTER INDEX idx_crypto_prices_new_crypto_datetime 
    RENAME TO idx_crypto_prices_crypto_datetime;
ALTER INDEX idx_crypto_prices_new_datetime 
    RENAME TO idx_crypto_prices_datetime;
ALTER INDEX idx_crypto_prices_new_interval 
    RENAME TO idx_crypto_prices_interval;

-- Recreate foreign key
ALTER TABLE crypto_fetch_logs 
    ADD CONSTRAINT crypto_fetch_logs_crypto_id_fkey 
    FOREIGN KEY (crypto_id) REFERENCES cryptocurrencies(id) ON DELETE CASCADE;

COMMIT;

\echo 'Step 8: Tables swapped successfully!';
\echo 'Old table saved as crypto_prices_old (can be dropped after validation)';

-- ============================================================================
-- STEP 9: Analyze and verify
-- ============================================================================

\echo 'Step 9: Running final analysis...';

-- Update statistics
ANALYZE crypto_prices;

-- Show hypertable info
\echo '';
\echo '=== Hypertable Information ===';
SELECT * FROM timescaledb_information.hypertables 
WHERE hypertable_name = 'crypto_prices';

-- Show chunks
\echo '';
\echo '=== Recent Chunks (Last 10) ===';
SELECT 
    chunk_name,
    range_start,
    range_end,
    pg_size_pretty(total_bytes) as size
FROM timescaledb_information.chunks
WHERE hypertable_name = 'crypto_prices'
ORDER BY range_start DESC
LIMIT 10;

-- Show compression stats (after compression runs)
\echo '';
\echo '=== Compression Settings ===';
SELECT * FROM timescaledb_information.compression_settings
WHERE hypertable_name = 'crypto_prices';

-- ============================================================================
-- SUCCESS!
-- ============================================================================

\echo '';
\echo '✅ ====================================================================';
\echo '✅ TimescaleDB migration complete!';
\echo '✅ ====================================================================';
\echo '';
\echo 'Summary:';
\echo '  - All hourly data migrated successfully';
\echo '  - Hypertable with 7-day chunks created';
\echo '  - Compression enabled (chunks older than 7 days)';
\echo '  - Continuous aggregates created (daily & weekly)';
\echo '  - Old table saved as crypto_prices_old';
\echo '';
\echo 'Next steps:';
\echo '  1. Test backtesting queries';
\echo '  2. Monitor performance improvements';
\echo '  3. Drop old table after validation: DROP TABLE crypto_prices_old;';
\echo '  4. Wait 7+ days for automatic compression to begin';
\echo '';
\echo '⚠️  IMPORTANT: All hourly data is preserved. Retention policy is DISABLED.';
\echo '';
