-- Cryptocurrency Backtesting Performance Optimization Indexes
-- Created: October 5, 2025
-- Purpose: Dramatically improve backtest query performance

-- ============================================================================
-- Primary Optimization: Crypto Prices Query Performance
-- ============================================================================

-- 1. Composite index for the most common query pattern
-- This covers: WHERE crypto_id = X AND interval_type = Y ORDER BY datetime
CREATE INDEX IF NOT EXISTS idx_crypto_prices_crypto_interval_datetime 
ON crypto_prices(crypto_id, interval_type, datetime);

-- 2. Partial index specifically for daily data (most common for backtesting)
-- This is smaller and faster than a full index
CREATE INDEX IF NOT EXISTS idx_crypto_prices_daily 
ON crypto_prices(crypto_id, datetime) 
WHERE interval_type = '1d';

-- 3. Covering index to avoid table lookups (includes all needed columns)
-- This allows index-only scans for complete query fulfillment
CREATE INDEX IF NOT EXISTS idx_crypto_prices_backtest_covering 
ON crypto_prices(crypto_id, interval_type, datetime, open_price, high_price, low_price, close_price, volume);

-- ============================================================================
-- Secondary Optimization: Strategy and Result Lookups
-- ============================================================================

-- 4. Optimize strategy parameter lookups
CREATE INDEX IF NOT EXISTS idx_crypto_strategy_params_strategy_order 
ON crypto_strategy_parameters(strategy_id, display_order);

-- 5. Optimize backtest result caching lookups
CREATE INDEX IF NOT EXISTS idx_crypto_backtest_results_lookup 
ON crypto_backtest_results(strategy_id, cryptocurrency_id, parameters_hash);

-- 6. Optimize result sorting by performance
CREATE INDEX IF NOT EXISTS idx_crypto_backtest_results_return 
ON crypto_backtest_results(total_return DESC);

-- ============================================================================
-- Statistics Update (helps query planner choose best indexes)
-- ============================================================================

-- Update table statistics for better query planning
ANALYZE crypto_prices;
ANALYZE crypto_strategies;
ANALYZE crypto_strategy_parameters;
ANALYZE crypto_backtest_results;
ANALYZE cryptocurrencies;

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Check index sizes and usage
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE tablename IN ('crypto_prices', 'crypto_strategies', 'crypto_strategy_parameters', 'crypto_backtest_results')
ORDER BY tablename, indexname;

-- Show query plan for typical backtest query
EXPLAIN ANALYZE
SELECT datetime, open_price, high_price, low_price, close_price, volume
FROM crypto_prices 
WHERE crypto_id = 1 AND interval_type = '1d'
ORDER BY datetime ASC;

-- Expected output should show "Index Scan" or "Index Only Scan" instead of "Seq Scan"
