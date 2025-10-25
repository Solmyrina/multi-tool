-- Performance Optimization: Add indexes to continuous aggregates
-- Part of Medium Effort Optimizations (Phase 2)
-- Expected impact: 5-10x faster aggregate queries

-- ============================================================================
-- 1. CONTINUOUS AGGREGATE INDEXES
-- ============================================================================

-- Index on crypto_prices_daily for backtest queries
CREATE INDEX IF NOT EXISTS idx_crypto_prices_daily_crypto_date 
ON crypto_prices_daily (crypto_id, day DESC);

CREATE INDEX IF NOT EXISTS idx_crypto_prices_daily_date 
ON crypto_prices_daily (day DESC);

-- Index with included columns for dashboard queries
CREATE INDEX IF NOT EXISTS idx_crypto_prices_daily_dashboard 
ON crypto_prices_daily (crypto_id, day DESC) 
INCLUDE (open_price, high_price, low_price, close_price, volume);

-- Index on crypto_prices_weekly for longer-term analysis
CREATE INDEX IF NOT EXISTS idx_crypto_prices_weekly_crypto_date 
ON crypto_prices_weekly (crypto_id, week DESC);

CREATE INDEX IF NOT EXISTS idx_crypto_prices_weekly_date 
ON crypto_prices_weekly (week DESC);

-- ============================================================================
-- 2. MATERIALIZED DASHBOARD VIEW
-- ============================================================================

-- Drop existing view if it exists
DROP MATERIALIZED VIEW IF EXISTS crypto_dashboard_summary CASCADE;

-- Create materialized view for instant dashboard loading (<50ms)
CREATE MATERIALIZED VIEW crypto_dashboard_summary AS
SELECT 
    c.id as crypto_id,
    c.symbol,
    c.name,
    
    -- Latest price data (from most recent daily aggregate)
    latest.close_price as current_price,
    latest.day as last_updated,
    
    -- 24-hour change
    COALESCE(
        ((latest.close_price - prev_day.close_price) / prev_day.close_price * 100), 
        0
    ) as change_24h_percent,
    
    -- 7-day statistics
    week_stats.high_7d,
    week_stats.low_7d,
    week_stats.avg_volume_7d,
    week_stats.change_7d_percent,
    
    -- 30-day statistics  
    month_stats.high_30d,
    month_stats.low_30d,
    month_stats.avg_volume_30d,
    month_stats.change_30d_percent,
    
    -- All-time statistics
    all_time.all_time_high,
    all_time.all_time_high_date,
    all_time.all_time_low,
    all_time.all_time_low_date,
    
    -- Data availability
    all_time.total_days as days_of_data,
    all_time.first_date as first_data_date
    
FROM cryptocurrencies c

-- Latest price (most recent daily close)
LEFT JOIN LATERAL (
    SELECT day, close_price
    FROM crypto_prices_daily
    WHERE crypto_id = c.id
    ORDER BY day DESC
    LIMIT 1
) latest ON true

-- Previous day price (for 24h change)
LEFT JOIN LATERAL (
    SELECT close_price
    FROM crypto_prices_daily
    WHERE crypto_id = c.id
      AND day < latest.day
    ORDER BY day DESC
    LIMIT 1
) prev_day ON true

-- 7-day statistics
LEFT JOIN LATERAL (
    SELECT 
        MAX(high_price) as high_7d,
        MIN(low_price) as low_7d,
        AVG(volume) as avg_volume_7d,
        COALESCE(
            ((MAX(CASE WHEN day = latest.day THEN close_price END) - 
              MAX(CASE WHEN day = latest.day - INTERVAL '7 days' THEN close_price END)) /
              NULLIF(MAX(CASE WHEN day = latest.day - INTERVAL '7 days' THEN close_price END), 0) * 100),
            0
        ) as change_7d_percent
    FROM crypto_prices_daily
    WHERE crypto_id = c.id
      AND day >= latest.day - INTERVAL '7 days'
      AND day <= latest.day
) week_stats ON true

-- 30-day statistics
LEFT JOIN LATERAL (
    SELECT 
        MAX(high_price) as high_30d,
        MIN(low_price) as low_30d,
        AVG(volume) as avg_volume_30d,
        COALESCE(
            ((MAX(CASE WHEN day = latest.day THEN close_price END) - 
              MAX(CASE WHEN day = latest.day - INTERVAL '30 days' THEN close_price END)) /
              NULLIF(MAX(CASE WHEN day = latest.day - INTERVAL '30 days' THEN close_price END), 0) * 100),
            0
        ) as change_30d_percent
    FROM crypto_prices_daily
    WHERE crypto_id = c.id
      AND day >= latest.day - INTERVAL '30 days'
      AND day <= latest.day
) month_stats ON true

-- All-time statistics
LEFT JOIN LATERAL (
    SELECT 
        MAX(high_price) as all_time_high,
        (SELECT day FROM crypto_prices_daily 
         WHERE crypto_id = c.id 
         ORDER BY high_price DESC LIMIT 1) as all_time_high_date,
        MIN(low_price) as all_time_low,
        (SELECT day FROM crypto_prices_daily 
         WHERE crypto_id = c.id 
         ORDER BY low_price ASC LIMIT 1) as all_time_low_date,
        COUNT(*) as total_days,
        MIN(day) as first_date
    FROM crypto_prices_daily
    WHERE crypto_id = c.id
) all_time ON true

WHERE c.is_active = true
ORDER BY c.symbol;

-- Create indexes on materialized view for fast lookups
CREATE UNIQUE INDEX idx_crypto_dashboard_summary_id 
ON crypto_dashboard_summary (crypto_id);

CREATE INDEX idx_crypto_dashboard_summary_symbol 
ON crypto_dashboard_summary (symbol);

CREATE INDEX idx_crypto_dashboard_summary_change_24h 
ON crypto_dashboard_summary (change_24h_percent DESC);

-- ============================================================================
-- 3. AUTO-REFRESH FUNCTION
-- ============================================================================

-- Function to refresh dashboard view
CREATE OR REPLACE FUNCTION refresh_crypto_dashboard()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY crypto_dashboard_summary;
    RAISE NOTICE 'Dashboard summary refreshed at %', NOW();
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 4. VERIFICATION QUERIES
-- ============================================================================

-- Test dashboard view performance
SELECT 
    'Dashboard View Performance Test' as test,
    COUNT(*) as total_cryptos,
    pg_size_pretty(pg_total_relation_size('crypto_dashboard_summary')) as view_size
FROM crypto_dashboard_summary;

-- Show top gainers (24h)
SELECT 
    symbol, 
    current_price, 
    change_24h_percent,
    avg_volume_7d
FROM crypto_dashboard_summary
ORDER BY change_24h_percent DESC
LIMIT 5;

-- Show index sizes
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE tablename IN ('crypto_prices_daily', 'crypto_prices_weekly', 'crypto_dashboard_summary')
ORDER BY pg_relation_size(indexrelid) DESC;

-- ============================================================================
-- NOTES
-- ============================================================================
-- 
-- REFRESH SCHEDULE:
-- - Dashboard view should be refreshed after new data arrives
-- - Add to cron: SELECT refresh_crypto_dashboard();
-- - Or trigger after crypto data update
--
-- EXPECTED PERFORMANCE:
-- - Dashboard query: 500ms → <50ms (10x faster)
-- - Aggregate queries: 200ms → 20-50ms (5-10x faster)
-- - View refresh time: ~1-2 seconds
-- - View size: ~100-200 KB (minimal overhead)
--
-- MAINTENANCE:
-- - Refresh after hourly crypto update
-- - Rebuild weekly: DROP/CREATE if schema changes
-- - Monitor view size growth over time
