-- ============================================================================
-- Crypto Backtest Performance Indexes
-- ============================================================================
-- Purpose: Add strategic indexes to optimize crypto backtesting queries
-- Expected improvement: 2-5x faster database queries
-- Created: October 6, 2025
-- ============================================================================

-- Note: CONCURRENTLY cannot run in a transaction, so no BEGIN/COMMIT
-- This is safer for production anyway (no long-running transactions)

-- Disable notices for cleaner output
SET client_min_messages TO WARNING;

-- ============================================================================
-- STEP 1: Drop old inefficient indexes if they exist
-- ============================================================================

DROP INDEX IF EXISTS idx_crypto_prices_cryptocurrency;
DROP INDEX IF EXISTS idx_crypto_prices_timestamp;
DROP INDEX IF EXISTS idx_crypto_prices_simple;

-- ============================================================================
-- STEP 2: Create optimized composite indexes for crypto_prices
-- ============================================================================

-- Primary index: cryptocurrency_id + timestamp (DESC for latest first)
-- This is THE MOST IMPORTANT index for backtesting queries
-- Covers: WHERE cryptocurrency_id = X ORDER BY timestamp
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_crypto_prices_crypto_timestamp 
ON crypto_prices(cryptocurrency_id, timestamp DESC)
WHERE timestamp IS NOT NULL;

-- Secondary index: timestamp + cryptocurrency_id
-- Covers: WHERE timestamp BETWEEN X AND Y AND cryptocurrency_id IN (...)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_crypto_prices_timestamp_crypto 
ON crypto_prices(timestamp, cryptocurrency_id)
WHERE timestamp IS NOT NULL;

-- Interval-specific index: crypto + interval + timestamp
-- Covers: WHERE cryptocurrency_id = X AND interval = '1d' AND timestamp BETWEEN...
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_crypto_prices_crypto_interval_timestamp 
ON crypto_prices(cryptocurrency_id, interval, timestamp DESC)
WHERE interval IN ('1h', '1d');

-- Covering index: Include frequently accessed columns
-- Avoids table lookup by including data in the index itself
-- This is a HUGE performance win for read-heavy workloads
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_crypto_prices_covering 
ON crypto_prices(cryptocurrency_id, timestamp DESC)
INCLUDE (open_price, high_price, low_price, close_price, volume, interval)
WHERE timestamp IS NOT NULL;

-- ============================================================================
-- STEP 3: Create indexes for crypto_strategies table
-- ============================================================================

-- Strategy type lookup (for filtering by strategy type)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_strategies_type 
ON crypto_strategies(strategy_type)
WHERE strategy_type IS NOT NULL;

-- Strategy name lookup (for exact name searches)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_strategies_name 
ON crypto_strategies(name)
WHERE name IS NOT NULL;

-- Strategy active status (for filtering only active strategies)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_strategies_active 
ON crypto_strategies(is_active)
WHERE is_active = TRUE;

-- ============================================================================
-- STEP 4: Create indexes for cryptocurrencies table
-- ============================================================================

-- Symbol lookup (most common search)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cryptocurrencies_symbol 
ON cryptocurrencies(symbol)
WHERE symbol IS NOT NULL;

-- Symbol + active status (for filtering tradeable cryptos)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cryptocurrencies_symbol_active 
ON cryptocurrencies(symbol, is_active)
WHERE is_active = TRUE;

-- Market cap ranking (for sorting by size)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cryptocurrencies_market_cap 
ON cryptocurrencies(market_cap_rank)
WHERE market_cap_rank IS NOT NULL;

-- ============================================================================
-- STEP 5: Create indexes for crypto_backtest_results (if exists)
-- ============================================================================

-- Check if table exists first
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'crypto_backtest_results') THEN
        -- User + timestamp (for showing user's recent results)
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_backtest_results_user_time 
        ON crypto_backtest_results(user_id, created_at DESC)
        WHERE user_id IS NOT NULL;
        
        -- Strategy + crypto (for comparing strategies on same crypto)
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_backtest_results_strategy_crypto 
        ON crypto_backtest_results(strategy_id, cryptocurrency_id, created_at DESC);
        
        -- Performance ranking (for leaderboards)
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_backtest_results_performance 
        ON crypto_backtest_results(total_return DESC)
        WHERE total_return IS NOT NULL;
    END IF;
END $$;

-- ============================================================================
-- STEP 6: Create indexes for crypto_strategy_parameters
-- ============================================================================

-- Strategy ID lookup (for loading strategy parameters)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_strategy_params_strategy 
ON crypto_strategy_parameters(strategy_id)
WHERE strategy_id IS NOT NULL;

-- Parameter order (for sorting parameters in UI)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_strategy_params_order 
ON crypto_strategy_parameters(strategy_id, display_order)
WHERE strategy_id IS NOT NULL;

-- ============================================================================
-- STEP 7: Analyze tables for query planner
-- ============================================================================

-- Update statistics for query planner optimization
ANALYZE crypto_prices;
ANALYZE crypto_strategies;
ANALYZE cryptocurrencies;
ANALYZE crypto_strategy_parameters;

-- Analyze backtest results if exists
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'crypto_backtest_results') THEN
        ANALYZE crypto_backtest_results;
    END IF;
END $$;

-- ============================================================================
-- STEP 8: Set index usage statistics
-- ============================================================================

-- Enable index scan statistics
ALTER TABLE crypto_prices SET (autovacuum_analyze_scale_factor = 0.01);
ALTER TABLE crypto_strategies SET (autovacuum_analyze_scale_factor = 0.1);
ALTER TABLE cryptocurrencies SET (autovacuum_analyze_scale_factor = 0.1);

-- ============================================================================
-- STEP 9: Verify indexes were created
-- ============================================================================

-- Display created indexes
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_indexes
JOIN pg_class ON pg_class.relname = indexname
WHERE schemaname = 'public'
  AND tablename IN ('crypto_prices', 'crypto_strategies', 'cryptocurrencies', 'crypto_strategy_parameters')
ORDER BY tablename, indexname;

-- ============================================================================
-- Performance Verification Queries
-- ============================================================================

-- Run these to verify performance improvements:

-- Query 1: Single crypto date range (should use idx_crypto_prices_crypto_timestamp)
-- EXPLAIN ANALYZE
-- SELECT timestamp, close_price, volume
-- FROM crypto_prices
-- WHERE cryptocurrency_id = 1
--   AND timestamp >= '2024-01-01'
--   AND timestamp <= '2024-12-31'
--   AND interval = '1d'
-- ORDER BY timestamp;

-- Query 2: Multiple cryptos (should use idx_crypto_prices_timestamp_crypto)
-- EXPLAIN ANALYZE
-- SELECT cryptocurrency_id, timestamp, close_price
-- FROM crypto_prices
-- WHERE cryptocurrency_id IN (1, 2, 3, 4, 5)
--   AND timestamp >= '2024-01-01'
--   AND timestamp <= '2024-12-31'
-- ORDER BY cryptocurrency_id, timestamp;

-- Query 3: Strategy lookup (should use idx_strategies_name)
-- EXPLAIN ANALYZE
-- SELECT * FROM crypto_strategies
-- WHERE name = 'RSI Buy/Sell';

-- Query 4: Crypto symbol lookup (should use idx_cryptocurrencies_symbol)
-- EXPLAIN ANALYZE
-- SELECT * FROM cryptocurrencies
-- WHERE symbol = 'BTCUSDT';

-- ============================================================================
-- Index Maintenance
-- ============================================================================

-- To check index usage statistics (run after some queries):
-- SELECT 
--     schemaname,
--     tablename,
--     indexname,
--     idx_scan AS index_scans,
--     idx_tup_read AS tuples_read,
--     idx_tup_fetch AS tuples_fetched
-- FROM pg_stat_user_indexes
-- WHERE schemaname = 'public'
--   AND tablename IN ('crypto_prices', 'crypto_strategies', 'cryptocurrencies')
-- ORDER BY idx_scan DESC;

-- To find unused indexes (run after a few days):
-- SELECT 
--     schemaname,
--     tablename,
--     indexname,
--     idx_scan,
--     pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
-- FROM pg_stat_user_indexes
-- WHERE schemaname = 'public'
--   AND idx_scan = 0
--   AND indexrelid::regclass::text NOT LIKE '%pkey%'
-- ORDER BY pg_relation_size(indexrelid) DESC;

-- ============================================================================
-- NOTES
-- ============================================================================
-- 
-- 1. CONCURRENTLY: Indexes are created without locking the table (safe for production)
-- 2. WHERE clauses: Partial indexes save space by excluding NULLs
-- 3. INCLUDE: Covering indexes avoid table lookups (huge performance win)
-- 4. DESC: Optimizes ORDER BY timestamp DESC queries
-- 5. Composite indexes: Order matters! Most selective column first
-- 
-- Expected Performance:
-- - Before: ~50-200ms per crypto query (sequential scan)
-- - After:  ~5-20ms per crypto query (index scan) → 5-10x faster!
-- 
-- Disk Space Impact:
-- - Indexes will use ~10-20% of table size
-- - For 1GB crypto_prices table → ~100-200MB indexes
-- - Well worth it for the performance gain!
-- 
-- ============================================================================
