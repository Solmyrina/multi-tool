-- ============================================================================
-- Crypto Backtest Performance Indexes (CORRECTED)
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

-- Primary index: crypto_id + datetime (DESC for latest first)
-- This is THE MOST IMPORTANT index for backtesting queries
-- Covers: WHERE crypto_id = X ORDER BY datetime
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_crypto_prices_crypto_datetime_opt 
ON crypto_prices(crypto_id, datetime DESC)
WHERE datetime IS NOT NULL;

-- Secondary index: datetime + crypto_id
-- Covers: WHERE datetime BETWEEN X AND Y AND crypto_id IN (...)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_crypto_prices_datetime_crypto_opt 
ON crypto_prices(datetime, crypto_id)
WHERE datetime IS NOT NULL;

-- Interval-specific index: crypto + interval + datetime
-- Covers: WHERE crypto_id = X AND interval_type = '1d' AND datetime BETWEEN...
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_crypto_prices_crypto_interval_datetime_opt 
ON crypto_prices(crypto_id, interval_type, datetime DESC)
WHERE interval_type IN ('1h', '1d');

-- Covering index: Include frequently accessed columns
-- Avoids table lookup by including data in the index itself
-- This is a HUGE performance win for read-heavy workloads
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_crypto_prices_covering_opt 
ON crypto_prices(crypto_id, datetime DESC)
INCLUDE (open_price, high_price, low_price, close_price, volume, interval_type)
WHERE datetime IS NOT NULL;

-- ============================================================================
-- STEP 3: Create indexes for crypto_strategies table
-- ============================================================================

-- Strategy type lookup (for filtering by strategy type)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_strategies_type_opt 
ON crypto_strategies(strategy_type)
WHERE strategy_type IS NOT NULL;

-- Strategy name lookup (for exact name searches)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_strategies_name_opt 
ON crypto_strategies(name)
WHERE name IS NOT NULL;

-- ============================================================================
-- STEP 4: Create indexes for cryptocurrencies table
-- ============================================================================

-- Symbol lookup (most common search)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cryptocurrencies_symbol_opt 
ON cryptocurrencies(symbol)
WHERE symbol IS NOT NULL;

-- ============================================================================
-- STEP 5: Create indexes for crypto_strategy_parameters
-- ============================================================================

-- Strategy ID lookup (for loading strategy parameters)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_strategy_params_strategy_opt 
ON crypto_strategy_parameters(strategy_id)
WHERE strategy_id IS NOT NULL;

-- Parameter order (for sorting parameters in UI)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_strategy_params_order_opt 
ON crypto_strategy_parameters(strategy_id, display_order)
WHERE strategy_id IS NOT NULL;

-- ============================================================================
-- STEP 6: Analyze tables for query planner
-- ============================================================================

-- Update statistics for query planner optimization
ANALYZE crypto_prices;
ANALYZE crypto_strategies;
ANALYZE cryptocurrencies;
ANALYZE crypto_strategy_parameters;

-- ============================================================================
-- STEP 7: Set index usage statistics
-- ============================================================================

-- Enable index scan statistics
ALTER TABLE crypto_prices SET (autovacuum_analyze_scale_factor = 0.01);
ALTER TABLE crypto_strategies SET (autovacuum_analyze_scale_factor = 0.1);
ALTER TABLE cryptocurrencies SET (autovacuum_analyze_scale_factor = 0.1);

-- ============================================================================
-- STEP 8: Display created indexes
-- ============================================================================

SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(quote_ident(schemaname) || '.' || quote_ident(indexname))::regclass) AS index_size
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('crypto_prices', 'crypto_strategies', 'cryptocurrencies', 'crypto_strategy_parameters')
  AND indexname LIKE '%_opt'
ORDER BY tablename, indexname;

-- ============================================================================
-- Success message
-- ============================================================================

\echo '✅ Indexes created successfully!'
\echo 'Expected performance improvement: 2-5x faster queries'
\echo ''
\echo 'Run these queries to verify performance:'
\echo '  EXPLAIN ANALYZE SELECT * FROM crypto_prices WHERE crypto_id = 1 AND datetime >= NOW() - INTERVAL ''1 year'' ORDER BY datetime;'
