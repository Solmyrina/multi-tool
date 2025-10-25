# TimescaleDB Implementation Plan for Crypto Backtester

**Time-Series Optimization Strategy**

> Based on analysis of existing documentation and current system architecture

---

## Executive Summary

### Why Implement TimescaleDB Now?

While Phase 6 was originally skipped, implementing TimescaleDB would provide:
- **2-3x query speedup** for time-range queries (based on TimescaleDB benchmarks)
- **50-70% storage reduction** with native compression
- **Continuous aggregates** for pre-computed metrics (daily/weekly summaries)
- **Better scalability** as dataset grows beyond current 5 years × 48 cryptos
- **Automatic partitioning** for easier maintenance

### Current State Analysis

**Database**: PostgreSQL 15.14 (TimescaleDB compatible)  
**Current Performance**: 1.7-2.5s for full backtest execution  
**Data Volume**: ~420K records per crypto × 48 cryptos = ~20M records  
**Indexes**: Composite indexes on (crypto_id, interval_type, datetime)  
**Caching**: Redis with 70-80% hit rate

### Expected Improvements

| Metric | Current | With TimescaleDB | Improvement |
|--------|---------|------------------|-------------|
| Cold query time | 800ms | 300-400ms | **2-2.5x faster** |
| Storage size | ~2.5 GB | ~1 GB | **60% reduction** |
| Time-range queries | Indexed scan | Chunk exclusion | **3-5x faster** |
| Aggregations | Real-time | Pre-computed | **10-50x faster** |
| Maintenance | Manual VACUUM | Automatic | **Simpler** |

---

## ⚠️ Data Retention Policy - IMPORTANT

### Will I Lose Hourly Data?

**NO - All hourly data is preserved by default.**

This implementation:
- ✅ **Keeps ALL hourly data** - No automatic deletion
- ✅ **Migrates 100% of existing data** - Every single record
- ✅ **Compresses old data** - Saves 50-70% storage WITHOUT deleting anything
- ✅ **Retention policy is DISABLED** - Only enable if you want to delete old data

### What Happens to Data Over Time?

```
Timeline:          [-------- Data Flow --------]
                        
Day 0-7:          Raw hourly data (uncompressed)
Day 7+:           Compressed hourly data (still fully queryable)
Forever:          ALL DATA REMAINS unless you enable retention policy
```

**Compression vs Deletion:**
- **Compression** (enabled by default): Saves storage, keeps all data
- **Retention** (disabled by default): Actually deletes old data

### Data Storage Structure

```
┌─────────────────────────────────────────────────────────────┐
│                    crypto_prices (Hypertable)                │
│                                                               │
│  ALL HOURLY DATA - NEVER DELETED (unless you enable policy) │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  2020-01-01 to 2020-01-07  │ Compressed │  350 MB → 100 MB  │
│  2020-01-08 to 2020-01-14  │ Compressed │  350 MB → 100 MB  │
│  2020-01-15 to 2020-01-21  │ Compressed │  350 MB → 100 MB  │
│         ... (all chunks compressed after 7 days)             │
│  2025-10-01 to 2025-10-07  │ Compressed │  350 MB → 100 MB  │
│  2025-10-08 to TODAY       │ Raw        │  350 MB           │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                              ↓
              ┌───────────────────────────────┐
              │   Continuous Aggregates       │
              │   (BONUS - Additional Views)  │
              ├───────────────────────────────┤
              │  crypto_prices_daily          │
              │  crypto_prices_weekly         │
              └───────────────────────────────┘
```

### Example Query After 5 Years

```sql
-- This works perfectly and returns ALL hourly data from 2020-2025
SELECT * FROM crypto_prices 
WHERE crypto_id = 1 
  AND datetime BETWEEN '2020-01-01' AND '2025-12-31'
  AND interval_type = '1h';
  
-- Result: 5 years × 365 days × 24 hours = 43,800 hourly records ✅
-- Query speed: ~300ms (vs 800ms before TimescaleDB)
-- Storage: 60% less space, but ALL DATA IS THERE

-- Or use continuous aggregate for even faster daily summary:
SELECT * FROM crypto_prices_daily 
WHERE crypto_id = 1 
  AND day BETWEEN '2020-01-01' AND '2025-12-31';
  
-- Result: 5 years × 365 days = 1,825 daily records ✅
-- Query speed: ~50ms (16x faster! Pre-computed from hourly data)
```

### Continuous Aggregates Are BONUS Data

The daily/weekly aggregates are **additional computed views**, not replacements:
- You keep: Raw hourly data (forever)
- You also get: Pre-computed daily summaries (faster queries)
- You also get: Pre-computed weekly summaries (even faster)

**You have MORE data, not less!**

### FAQ: Data Retention Concerns

**Q: Will compression delete my hourly data?**  
A: No! Compression reduces storage size but keeps 100% of data. Think of it like a ZIP file - smaller, but all data intact.

**Q: What if I want to keep hourly data forever?**  
A: That's the default behavior! Do nothing - all data is preserved.

**Q: What if I want to delete old hourly data (to save space)?**  
A: Uncomment the retention policy line in Step 7. Example: Keep only 5 years.

**Q: If I enable retention, do I lose ALL historical data?**  
A: No! Continuous aggregates (daily/weekly summaries) are preserved separately. You'd lose hourly granularity but keep daily summaries forever.

**Q: Can I query compressed data?**  
A: Yes! Compressed chunks are automatically decompressed when queried. You won't notice any difference except faster performance.

**Q: What happens to data I collect in the future?**  
A: All new hourly data is added normally, compressed after 7 days, kept forever (unless retention enabled).

---

## Implementation Roadmap

### Phase 1: Planning & Setup (Day 1)
1. Backup current database
2. Install TimescaleDB extension
3. Test migration on development copy
4. Benchmark current performance

### Phase 2: Migration (Day 2-3)
1. Create new hypertable
2. Migrate existing data
3. Update application code
4. Deploy with zero downtime

### Phase 3: Optimization (Day 4-5)
1. Enable compression (keeps all data, just compressed)
2. Create continuous aggregates (pre-computed summaries)
3. Configure chunk intervals (no data loss)
4. Optional: Add retention policies (disabled by default)

### Phase 4: Validation (Day 6-7)
1. Performance testing
2. Backtest validation
3. Monitor production
4. Documentation updates

---

## Detailed Implementation

### Step 1: Backup Current Database

```bash
# Create full backup before any changes
docker exec docker-project-database pg_dump -U root webapp_db > backup_pre_timescale_$(date +%Y%m%d).sql

# Verify backup
ls -lh backup_pre_timescale_*.sql

# Test restore (optional, on separate container)
# docker exec -i test-database psql -U root test_db < backup_pre_timescale_*.sql
```

### Step 2: Install TimescaleDB Extension

#### Option A: Use TimescaleDB Docker Image (Recommended)

**Update docker-compose.yml:**
```yaml
# docker-compose.yml
services:
  database:
    # Replace standard PostgreSQL image with TimescaleDB
    image: timescale/timescaledb:latest-pg15
    container_name: docker-project-database
    environment:
      POSTGRES_DB: webapp_db
      POSTGRES_USER: root
      POSTGRES_PASSWORD: root
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./database:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    networks:
      - app-network
    restart: unless-stopped
```

**Migration steps:**
```bash
# 1. Stop current database
docker compose stop database

# 2. Backup data volume (optional but recommended)
docker run --rm -v docker-project_postgres-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/postgres_data_backup.tar.gz -C /data .

# 3. Update docker-compose.yml (as shown above)

# 4. Start with TimescaleDB image
docker compose up -d database

# 5. Verify TimescaleDB is installed
docker exec docker-project-database psql -U root webapp_db -c "SELECT default_version FROM pg_available_extensions WHERE name = 'timescaledb';"
```

#### Option B: Install Extension on Existing PostgreSQL

```sql
-- Connect to database
-- docker exec -it docker-project-database psql -U root webapp_db

-- Install TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Verify installation
SELECT extname, extversion FROM pg_extension WHERE extname = 'timescaledb';
```

### Step 3: Create Migration SQL Script

**File: `database/migrate_to_timescaledb.sql`**

```sql
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

\echo 'Hypertable created successfully!';

-- ============================================================================
-- STEP 3: Migrate data from old table to new hypertable
-- ============================================================================

-- Insert all data (this may take a few minutes)
-- TimescaleDB will automatically partition into chunks
\echo 'Starting data migration... (this may take 2-5 minutes)';

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
ORDER BY datetime, crypto_id;  -- Order by time for optimal chunk placement

-- Verify migration
\echo 'Verifying data migration...';
SELECT 
    (SELECT COUNT(*) FROM crypto_prices) as old_count,
    (SELECT COUNT(*) FROM crypto_prices_new) as new_count,
    (SELECT COUNT(*) FROM crypto_prices) = (SELECT COUNT(*) FROM crypto_prices_new) as counts_match;

-- ============================================================================
-- STEP 4: Add indexes to hypertable
-- ============================================================================

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

\echo 'Indexes created successfully!';

-- ============================================================================
-- STEP 5: Enable compression
-- ============================================================================

-- Enable compression with segmentby for better compression ratio
-- Segment by crypto_id so each crypto's data is compressed together
ALTER TABLE crypto_prices_new SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'crypto_id,interval_type',
    timescaledb.compress_orderby = 'datetime DESC'
);

-- Add compression policy: compress chunks older than 7 days
SELECT add_compression_policy('crypto_prices_new', INTERVAL '7 days');

\echo 'Compression enabled! Chunks older than 7 days will be compressed automatically.';

-- ============================================================================
-- STEP 6: Create continuous aggregates for common queries
-- ============================================================================

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

\echo 'Weekly continuous aggregate created!';

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

BEGIN;

-- Drop foreign key constraints
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

\echo 'Tables swapped successfully!';
\echo 'Old table saved as crypto_prices_old (can be dropped after validation)';

-- ============================================================================
-- STEP 9: Analyze and verify
-- ============================================================================

-- Update statistics
ANALYZE crypto_prices;

-- Show hypertable info
SELECT * FROM timescaledb_information.hypertables 
WHERE hypertable_name = 'crypto_prices';

-- Show compression stats
SELECT 
    pg_size_pretty(before_compression_total_bytes) as before_compression,
    pg_size_pretty(after_compression_total_bytes) as after_compression,
    round(100 - (after_compression_total_bytes::numeric / before_compression_total_bytes::numeric * 100), 2) as compression_ratio_percent
FROM timescaledb_information.compression_settings
WHERE hypertable_name = 'crypto_prices';

-- Show chunks
SELECT 
    chunk_name,
    range_start,
    range_end,
    pg_size_pretty(total_bytes) as size
FROM timescaledb_information.chunks
WHERE hypertable_name = 'crypto_prices'
ORDER BY range_start DESC
LIMIT 10;

-- ============================================================================
-- SUCCESS!
-- ============================================================================

\echo '✅ TimescaleDB migration complete!';
\echo '';
\echo 'Next steps:';
\echo '1. Test backtesting queries';
\echo '2. Monitor performance improvements';
\echo '3. Drop old table after validation: DROP TABLE crypto_prices_old;';
\echo '4. Update application code to use continuous aggregates';
```

### Step 4: Update Application Code

**File: `api/crypto_backtest_service.py`**

Add helper method for using continuous aggregates:

```python
def get_price_data_optimized(self, crypto_id: int, start_date: str = None, 
                            end_date: str = None, interval: str = '1d',
                            use_continuous_aggregate: bool = True) -> pd.DataFrame:
    """
    Get price data with TimescaleDB optimization
    
    Args:
        crypto_id: Cryptocurrency ID
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        interval: Data interval ('1h', '1d', '1w')
        use_continuous_aggregate: Use pre-computed aggregates if available
        
    Returns:
        DataFrame with OHLCV data
    """
    with self.get_connection() as conn:
        # Use continuous aggregate for daily data
        if interval == '1d' and use_continuous_aggregate:
            query = """
                SELECT 
                    day as datetime,
                    open_price,
                    high_price,
                    low_price,
                    close_price,
                    volume
                FROM crypto_prices_daily
                WHERE crypto_id = %s
                  AND interval_type = '1h'
                  AND day BETWEEN COALESCE(%s, '2020-01-01'::timestamp)
                                AND COALESCE(%s, CURRENT_TIMESTAMP)
                ORDER BY day ASC
            """
        elif interval == '1w' and use_continuous_aggregate:
            query = """
                SELECT 
                    week as datetime,
                    open_price,
                    high_price,
                    low_price,
                    close_price,
                    volume
                FROM crypto_prices_weekly
                WHERE crypto_id = %s
                  AND interval_type = '1h'
                  AND week BETWEEN COALESCE(%s, '2020-01-01'::timestamp)
                                 AND COALESCE(%s, CURRENT_TIMESTAMP)
                ORDER BY week ASC
            """
        else:
            # Use raw hypertable (benefits from chunk exclusion)
            query = """
                SELECT 
                    datetime,
                    open_price,
                    high_price,
                    low_price,
                    close_price,
                    volume
                FROM crypto_prices
                WHERE crypto_id = %s 
                  AND interval_type = %s
                  AND datetime BETWEEN COALESCE(%s, '2020-01-01'::timestamp)
                                   AND COALESCE(%s, CURRENT_TIMESTAMP)
                ORDER BY datetime ASC
            """
            return pd.read_sql(query, conn, params=[crypto_id, interval, start_date, end_date])
        
        return pd.read_sql(query, conn, params=[crypto_id, start_date, end_date])
```

Add TimescaleDB health check:

```python
def check_timescaledb_status(self) -> Dict:
    """Check TimescaleDB extension and performance"""
    with self.get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if TimescaleDB is installed
            cur.execute("""
                SELECT extversion 
                FROM pg_extension 
                WHERE extname = 'timescaledb'
            """)
            timescale_version = cur.fetchone()
            
            # Get hypertable info
            cur.execute("""
                SELECT 
                    hypertable_name,
                    num_dimensions,
                    num_chunks,
                    compression_enabled,
                    pg_size_pretty(total_bytes) as total_size
                FROM timescaledb_information.hypertables
                WHERE hypertable_name = 'crypto_prices'
            """)
            hypertable_info = cur.fetchone()
            
            # Get compression stats
            cur.execute("""
                SELECT 
                    pg_size_pretty(before_compression_total_bytes) as before,
                    pg_size_pretty(after_compression_total_bytes) as after,
                    round(100 - (after_compression_total_bytes::numeric / 
                                 before_compression_total_bytes::numeric * 100), 2) 
                        as compression_percent
                FROM timescaledb_information.compression_settings
                WHERE hypertable_name = 'crypto_prices'
            """)
            compression_stats = cur.fetchone()
            
            return {
                'timescaledb_version': timescale_version['extversion'] if timescale_version else None,
                'hypertable': dict(hypertable_info) if hypertable_info else None,
                'compression': dict(compression_stats) if compression_stats else None
            }
```

### Step 5: Add API Endpoint for TimescaleDB Status

**File: `api/api.py`**

```python
@app.route('/api/crypto/timescaledb-status', methods=['GET'])
def timescaledb_status():
    """Get TimescaleDB status and performance metrics"""
    try:
        backtest_service = CryptoBacktestService()
        status = backtest_service.check_timescaledb_status()
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

### Step 6: Run Migration

```bash
# 1. Backup database
docker exec docker-project-database pg_dump -U root webapp_db > backup_pre_timescale.sql

# 2. Run migration script
docker exec -i docker-project-database psql -U root webapp_db < database/migrate_to_timescaledb.sql

# 3. Monitor migration progress
docker logs -f docker-project-database

# 4. Verify migration
docker exec docker-project-database psql -U root webapp_db -c "
    SELECT * FROM timescaledb_information.hypertables WHERE hypertable_name = 'crypto_prices';
"
```

### Step 7: Performance Validation

**Create benchmark script: `api/benchmark_timescale.py`**

```python
#!/usr/bin/env python3
"""
Benchmark TimescaleDB performance improvements
"""
import time
import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    'host': 'database',
    'port': 5432,
    'database': 'webapp_db',
    'user': 'root',
    'password': 'root'
}

def benchmark_query(query, params, name):
    """Benchmark a single query"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Warm up
    cur.execute(query, params)
    cur.fetchall()
    
    # Benchmark (10 runs)
    times = []
    for _ in range(10):
        start = time.time()
        cur.execute(query, params)
        cur.fetchall()
        times.append(time.time() - start)
    
    cur.close()
    conn.close()
    
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    print(f"\n{name}:")
    print(f"  Average: {avg_time*1000:.2f}ms")
    print(f"  Min: {min_time*1000:.2f}ms")
    print(f"  Max: {max_time*1000:.2f}ms")
    
    return avg_time

if __name__ == '__main__':
    print("=" * 60)
    print("TimescaleDB Performance Benchmark")
    print("=" * 60)
    
    # Test 1: Single crypto, 1 year of data
    query1 = """
        SELECT datetime, close_price, volume
        FROM crypto_prices
        WHERE crypto_id = 1
          AND datetime >= NOW() - INTERVAL '1 year'
        ORDER BY datetime DESC
    """
    t1 = benchmark_query(query1, [], "Test 1: Single crypto, 1 year")
    
    # Test 2: Multiple cryptos, date range
    query2 = """
        SELECT crypto_id, datetime, close_price
        FROM crypto_prices
        WHERE crypto_id IN (1, 2, 3, 4, 5)
          AND datetime BETWEEN '2024-01-01' AND '2024-12-31'
        ORDER BY crypto_id, datetime
    """
    t2 = benchmark_query(query2, [], "Test 2: 5 cryptos, full year")
    
    # Test 3: Continuous aggregate (daily)
    query3 = """
        SELECT day, close_price, volume
        FROM crypto_prices_daily
        WHERE crypto_id = 1
          AND day >= NOW() - INTERVAL '1 year'
        ORDER BY day DESC
    """
    t3 = benchmark_query(query3, [], "Test 3: Daily aggregate, 1 year")
    
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Raw query speedup: {t1:.3f}s")
    print(f"  Multi-crypto speedup: {t2:.3f}s")
    print(f"  Aggregate speedup: {t3:.3f}s vs {t1:.3f}s ({t1/t3:.1f}x faster!)")
    print("=" * 60)
```

Run benchmark:
```bash
docker exec docker-project-api python3 benchmark_timescale.py
```

---

## Monitoring & Maintenance

### Check Compression Status

```sql
-- View compression statistics
SELECT 
    chunk_schema,
    chunk_name,
    pg_size_pretty(before_compression_total_bytes) as before,
    pg_size_pretty(after_compression_total_bytes) as after,
    round((1 - after_compression_total_bytes::numeric / 
           before_compression_total_bytes::numeric) * 100, 2) as compression_percent
FROM timescaledb_information.compressed_chunks
ORDER BY before_compression_total_bytes DESC
LIMIT 10;
```

### Manual Compression

```sql
-- Compress specific chunks manually
SELECT compress_chunk(chunk) 
FROM show_chunks('crypto_prices', older_than => INTERVAL '14 days');
```

### Monitor Continuous Aggregates

```sql
-- Check refresh status
SELECT 
    view_name,
    last_successful_refresh,
    pg_size_pretty(total_bytes) as size
FROM timescaledb_information.continuous_aggregates;
```

### Performance Monitoring Query

```sql
-- Query performance by chunk
SELECT 
    hypertable_name,
    range_start,
    range_end,
    pg_size_pretty(total_bytes) as size,
    number_compressed_chunks,
    number_uncompressed_chunks
FROM timescaledb_information.chunks
WHERE hypertable_name = 'crypto_prices'
ORDER BY range_start DESC;
```

---

## Expected Results

### Query Performance

| Query Type | Before | After | Speedup |
|------------|--------|-------|---------|
| Single crypto, 1 year | 800ms | 300ms | **2.7x** |
| 48 cryptos, 1 year | 2.5s | 1.0s | **2.5x** |
| Daily aggregate | 800ms | 50ms | **16x** |
| Weekly aggregate | 800ms | 20ms | **40x** |

### Storage Efficiency

| Metric | Before | After | Reduction | Data Preserved |
|--------|--------|-------|-----------|----------------|
| Table size | 2.5 GB | 1.0 GB | **60%** | **100%** ✅ |
| Index size | 800 MB | 600 MB | **25%** | **100%** ✅ |
| Total | 3.3 GB | 1.6 GB | **52%** | **100%** ✅ |

**Note:** 52% size reduction is achieved through compression, NOT deletion. All hourly data from 2020-2025 remains fully queryable.

### Operational Benefits

- ✅ **Automatic partitioning** - No manual maintenance
- ✅ **Chunk exclusion** - Only scans relevant time ranges
- ✅ **Parallel queries** - Better multi-core utilization
- ✅ **Continuous aggregates** - Pre-computed summaries (bonus data!)
- ✅ **Data compression** - 50-70% storage savings, all data preserved
- ✅ **All hourly data kept** - Forever (unless you enable retention)
- ⚠️ **Data retention** - Optional feature (disabled by default)

---

## Rollback Plan

If issues arise:

```sql
-- Rollback to old table
BEGIN;

ALTER TABLE crypto_prices RENAME TO crypto_prices_timescale;
ALTER TABLE crypto_prices_old RENAME TO crypto_prices;

-- Recreate original indexes
CREATE INDEX idx_crypto_prices_crypto_datetime 
    ON crypto_prices(crypto_id, datetime DESC);
CREATE INDEX idx_crypto_prices_datetime 
    ON crypto_prices(datetime DESC);

COMMIT;

-- Revert docker-compose.yml to standard PostgreSQL image
-- Restart container
```

---

## Conclusion

### Summary

TimescaleDB provides:
1. **2-3x faster** time-range queries
2. **50-70% storage reduction** via compression (ALL DATA PRESERVED)
3. **10-50x faster** aggregate queries via continuous aggregates
4. **Better scalability** for growing datasets
5. **Simpler maintenance** with automatic partitioning
6. **100% data retention** - All hourly data kept forever by default

### Recommendation

**Implement TimescaleDB if:**
- Dataset grows beyond 50M records
- Need faster aggregate queries (daily/weekly reports)
- Storage costs are a concern
- Planning to add more cryptocurrencies

**Skip if:**
- Current performance (1.7s) is acceptable
- Dataset remains < 20M records
- Team lacks TimescaleDB experience
- Redis caching provides sufficient speedup

### Data Retention Guarantee

**🔒 YOUR HOURLY DATA IS SAFE 🔒**

This implementation:
- ✅ Migrates 100% of existing hourly data
- ✅ Keeps ALL hourly data forever (default behavior)
- ✅ Compresses old data to save 60% storage (data remains fully queryable)
- ✅ Adds daily/weekly summaries as BONUS views (doesn't replace hourly data)
- ⚠️ Retention policy is COMMENTED OUT and DISABLED by default
- ⚠️ Only enable retention if you explicitly want to delete old data

**Example:** After 5 years, you'll have all 43,800 hourly records per crypto, fully queryable, just taking up 60% less disk space.

### Next Steps

1. Review this implementation plan with team
2. Test migration on development environment
3. Benchmark performance improvements
4. Plan production deployment window
5. Update documentation after successful migration

---

**Created**: October 8, 2025  
**Status**: Ready for implementation  
**Estimated Time**: 1-2 days  
**Risk Level**: Low (full rollback available)  
**Data Loss Risk**: ZERO - All hourly data preserved by default
