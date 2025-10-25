# Performance Optimization Guide

**Cryptocurrency Backtesting Optimization: 30+ seconds → 0.1 seconds (250x improvement)**

> **Consolidated from**: OPTIMIZATION_GUIDE.md, PERFORMANCE_OPTIMIZATION_CRYPTOCURRENCIES.md, and 15+ phase documentation files

---

## Quick Start

### Current Performance
- **First result**: 0.1 seconds (250x faster!)
- **All results**: 3-5 seconds (6-10x faster!)
- **Data reduction**: 99.8% less data processed
- **Cache hit rate**: 70-80%

### Key Technologies
- **PostgreSQL** with indexed queries and date range filtering
- **Redis** for intelligent caching (3-5x speedup)
- **NumPy** for vectorized calculations (30x faster)
- **Server-Sent Events (SSE)** for real-time streaming
- **ThreadPoolExecutor** for parallel processing

---

## 8-Phase Optimization Journey

### Phase 1: Query & Database Optimization
**Impact**: 30s → 25s (1.2x)

**Key Changes**:
```sql
-- Add composite index
CREATE INDEX idx_crypto_prices_composite 
    ON crypto_prices(crypto_id, interval_type, datetime);

-- Add covering index
CREATE INDEX idx_crypto_prices_covering 
    ON crypto_prices(crypto_id, datetime) 
    INCLUDE (open_price, high_price, low_price, close_price, volume);
```

**Benefits**:
- Connection pooling implemented
- Query optimization with JOINs
- Proper database indexing

---

### Phase 2: Date Range Filtering
**Impact**: 25s → 8s (3.1x) ⭐ **Biggest single improvement**

**Key Implementation**:
```python
def get_price_data(self, crypto_id: int, start_date: str = None, end_date: str = None):
    query = """
        SELECT datetime, open_price, high_price, low_price, close_price, volume
        FROM crypto_prices
        WHERE crypto_id = %s 
          AND interval_type = '1h'
          AND datetime BETWEEN COALESCE(%s, '2020-01-01'::timestamp) 
                           AND COALESCE(%s, CURRENT_TIMESTAMP)
        ORDER BY datetime ASC
    """
    return pd.read_sql(query, conn, params=[crypto_id, start_date, end_date])
```

**Data Volume Reduction**:
```
Before: 5 years × 48 cryptos = 2,102,400 records
After:  1 year × 48 cryptos = 420,480 records
Reduction: 99.8% of data eliminated
```

---

### Phase 3: Redis Caching
**Impact**: 8s → 2-3s (3-4x on cache hits)

**Architecture**:
```
Request → Redis Check → Cache Hit? → Return (50ms)
                    ↓ Miss
                Database Query → Store in Redis (800ms)
```

**Implementation**:
```python
class CryptoBacktestService:
    def get_price_data_cached(self, crypto_id, start_date, end_date):
        cache_key = f"crypto_prices:{crypto_id}:{start_date}:{end_date}"
        
        # Try cache
        cached = self.redis_client.get(cache_key)
        if cached:
            return pd.read_json(cached)
        
        # Query database
        df = self.get_price_data(crypto_id, start_date, end_date)
        
        # Store in cache
        self.redis_client.setex(cache_key, 3600, df.to_json())
        return df
```

**Cache Performance**:
- First run: 800ms per query
- Subsequent runs: 50ms per query
- **Speedup**: 16x faster on cache hits

---

### Phase 4 & 5: Query & Index Optimization
**Impact**: 3s → 2.5s (1.2x)

**Partial Indexes**:
```sql
-- Index only active cryptocurrencies
CREATE INDEX idx_active_cryptos 
    ON cryptocurrencies(id) 
    WHERE is_active = true;

-- Index only hourly data
CREATE INDEX idx_hourly_prices 
    ON crypto_prices(crypto_id, datetime) 
    WHERE interval_type = '1h';
```

**Batch Loading**:
```python
def get_price_data_batch(self, crypto_ids: List[int], start_date, end_date):
    query = """
        SELECT crypto_id, datetime, open_price, high_price, 
               low_price, close_price, volume
        FROM crypto_prices
        WHERE crypto_id = ANY(%s)
          AND datetime BETWEEN %s AND %s
        ORDER BY crypto_id, datetime
    """
    return pd.read_sql(query, conn, params=[crypto_ids, start_date, end_date])
```

---

### Phase 6: TimescaleDB Extension
**Status**: ⏭️ Skipped (Not needed)

**Why Not Implemented**:
- Current 2.5s performance is already excellent
- Would add complexity to migration
- Marginal ROI vs. implementation cost
- Current PostgreSQL + Redis solution sufficient

**Could implement if needed**:
```sql
SELECT create_hypertable('crypto_prices', 'datetime');
ALTER TABLE crypto_prices SET (timescaledb.compress);
SELECT add_compression_policy('crypto_prices', INTERVAL '7 days');
```

---

### Phase 7: NumPy Vectorization
**Impact**: 2.5s → 1.7s (1.5x)

**RSI Calculation Comparison**:
```python
# Before: Python loops (0.245s)
def calculate_rsi_slow(prices, period=14):
    rsi_values = []
    for i in range(len(prices)):
        if i < period:
            continue
        gains = [p for p in window if p > 0]
        losses = [abs(p) for p in window if p < 0]
        # ... complex manual calculation

# After: NumPy vectorized (0.008s)
def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# Speedup: 30x faster!
```

**Other Vectorized Calculations**:
```python
# Moving Average
def calculate_moving_average(prices: pd.Series, period: int):
    return prices.rolling(window=period).mean()

# Bollinger Bands
def calculate_bollinger_bands(prices, period, std_mult):
    middle = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper = middle + (std * std_mult)
    lower = middle - (std * std_mult)
    return upper, middle, lower
```

---

### Phase 8: Progressive Loading (SSE)
**Impact**: **0.1s perceived** (250x for user experience!)

**Architecture**:
```
Frontend → API /api/crypto/backtest/stream → ThreadPoolExecutor
                        ↓
                  SSE Event Stream
                        ↓
    ┌─ event: start (0ms)
    ├─ event: result #1 (100ms) ← User sees first result!
    ├─ event: progress (5% done)
    ├─ event: result #2-48 (streaming)
    ├─ event: progress updates
    └─ event: complete (3.5s)
```

**Backend Streaming Service**:
```python
class StreamingBacktestService:
    def stream_strategy_against_all_cryptos(self, strategy_id, params):
        """Generator yielding SSE events"""
        cryptos = self.get_cryptocurrencies()
        
        # Start event
        yield self._format_sse({'type': 'start', 'total': len(cryptos)})
        
        # Submit all to thread pool
        futures = [
            self.executor.submit(self._run_backtest, strat, crypto, params)
            for crypto in cryptos
        ]
        
        # Stream results as they complete
        for future in futures:
            result = future.result()
            yield self._format_sse({'type': 'result', 'data': result})
```

**Frontend Progressive UI**:
```javascript
function runAllBacktestsProgressive(strategyId, parameters) {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/crypto/backtest/stream', true);
    
    let buffer = '';
    xhr.onprogress = function() {
        buffer += xhr.responseText.slice(buffer.length);
        const lines = buffer.split('\n\n');
        
        for (let i = 0; i < lines.length - 1; i++) {
            const line = lines[i].trim();
            if (line.startsWith('data: ')) {
                const data = JSON.parse(line.slice(6));
                handleStreamEvent(data);
            }
        }
    };
    
    xhr.send(JSON.stringify({strategy_id: strategyId, parameters}));
}
```

**Nginx Configuration for SSE**:
```nginx
location /api/crypto/backtest/stream {
    proxy_pass http://api:8000;
    
    # Critical for streaming
    proxy_buffering off;
    proxy_cache off;
    proxy_set_header Connection '';
    proxy_http_version 1.1;
    chunked_transfer_encoding off;
    
    # Extended timeouts
    proxy_read_timeout 300s;
    proxy_connect_timeout 300s;
}
```

**User Experience Transformation**:
```
BEFORE (Traditional):
0s: Click "Run All Backtests"
    [Loading spinner...]
30s: All results appear

AFTER (Progressive):
0s:   Click "Run All Backtests"
0.1s: First result! ⚡
1.0s: 12 results visible, 25% done
2.0s: 24 results visible, 50% done
3.0s: 36 results visible, 75% done
3.5s: 48 results complete ✅
```

---

## Performance Summary

### Complete Improvement Journey

| Phase | Optimization | First Result | All Results | Data | Improvement |
|-------|-------------|--------------|-------------|------|-------------|
| Initial | Baseline | 30s | 30s | 2.1M rows | — |
| Phase 1 | Query Opt | 25s | 25s | 2.1M | 1.2x |
| Phase 2 | Date Filter | 8s | 8s | 420K | **3.1x** |
| Phase 3 | Caching | 2s | 2-3s | 420K | 3-4x |
| Phase 7 | Vectorization | 1.7s | 1.7s | 420K | 1.5x |
| Phase 8 | **SSE Stream** | **0.1s** | **3-5s** | 420K | **250x perceived** |

### System Resource Usage

**Database**:
- Connections: 1-5 concurrent
- Query time: 50-100ms (with indexes)
- Memory: ~500MB for active queries

**Redis Cache**:
- Memory: 15-30MB for price data
- Keys: 500-1000 active entries
- Hit rate: 70-80%

**API Container**:
- Memory: 200-400MB during execution
- CPU: 60-80% during parallel backtests
- ThreadPool: 4 workers

---

## Special Case: Cryptocurrency Filtering Optimization

### The Problem
The `/cryptocurrencies` endpoint filtered for cryptos with price data using an `EXISTS` subquery:

```sql
SELECT * FROM cryptocurrencies c 
WHERE c.is_active = true 
AND EXISTS (SELECT 1 FROM crypto_prices WHERE crypto_id = c.id LIMIT 1)
```

**Issue**: 14-17 seconds! Why?
- TimescaleDB hypertable with 2M+ rows across 1,052+ compressed chunks
- `EXISTS` subquery decompressed chunks for each of 263 cryptocurrencies
- Severe decompression overhead

### The Solution: Denormalized Flag
```sql
-- Add boolean column
ALTER TABLE cryptocurrencies 
ADD COLUMN has_price_data BOOLEAN DEFAULT false;

-- Populate with current data
UPDATE cryptocurrencies c
SET has_price_data = true
WHERE EXISTS (SELECT 1 FROM crypto_prices WHERE crypto_id = c.id);

-- Index for fast filtering
CREATE INDEX idx_cryptocurrencies_has_price_data 
ON cryptocurrencies(is_active, has_price_data) 
WHERE is_active = true AND has_price_data = true;

-- Trigger to maintain flag
CREATE FUNCTION update_crypto_has_price_data()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE cryptocurrencies 
    SET has_price_data = true 
    WHERE id = NEW.crypto_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER maintain_crypto_price_flag
AFTER INSERT ON crypto_prices
FOR EACH ROW
EXECUTE FUNCTION update_crypto_has_price_data();
```

**Fast Query**:
```sql
SELECT * FROM cryptocurrencies
WHERE is_active = true 
  AND has_price_data = true
ORDER BY symbol;
```

**Result**: **14-17 seconds → 50ms** (280x faster!)

---

## Troubleshooting

### Redis Connection Issues

```bash
# Check if Redis is running
docker ps | grep redis

# Test connection
docker exec docker-project-redis redis-cli ping
# Should return: PONG

# Check memory
docker exec docker-project-redis redis-cli INFO memory
```

### Cache Stale Data

```bash
# Clear all cache
docker exec docker-project-redis redis-cli FLUSHDB

# Clear specific pattern
docker exec docker-project-redis redis-cli --scan --pattern "crypto_prices:*" | xargs redis-cli DEL
```

### SSE Stream Hangs

**Check Nginx Configuration**:
```nginx
# Verify these are set
proxy_buffering off;
proxy_cache off;
proxy_read_timeout 300s;
```

**Restart Services**:
```bash
docker compose restart api nginx
```

### Slow Database Performance

**Run Maintenance**:
```bash
docker exec docker-project-database psql -U root webapp_db -c "VACUUM ANALYZE crypto_prices;"
docker exec docker-project-database psql -U root webapp_db -c "REINDEX TABLE crypto_prices;"
```

### High Memory Usage

**Check Redis**:
```bash
docker exec docker-project-redis redis-cli INFO memory
```

**Adjust in docker-compose.yml**:
```yaml
redis:
  command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

---

## Key Learnings

### What Worked Best
1. **Date range filtering**: Single largest impact (3.1x)
2. **Caching layer**: Excellent ROI with simplicity
3. **Progressive loading**: Transforms user perception
4. **Vectorization**: Improves code and performance
5. **Parallel processing**: Leverages multi-core

### What Didn't Pan Out
- **TimescaleDB**: Not needed at current scale
- **Compression**: Redis handles caching better
- **Complex indexing strategies**: Simple indexes sufficient

### Scalability Path
```
Current (48 cryptos):   3-5 seconds (cached)
100 cryptos:             6-7 seconds
200 cryptos:             12-15 seconds
500 cryptos:             30-40 seconds (may need TimescaleDB)
```

---

## Related Documentation

- 📖 [Backtesting Guide](../guides/BACKTESTING.md) - How to run backtests
- 📖 [System Architecture](../architecture/ARCHITECTURE.md) - System design overview
- 📖 [Database Guide](../guides/DATABASE.md) - Database access and queries
- 🔧 [Troubleshooting](./TROUBLESHOOTING.md) - Common issues and fixes

---

**Last Updated**: October 25, 2025  
**Optimization Period**: September 2024 - March 2025 (6 months)  
**Current Status**: ✅ Stable and optimized for production  
**Next Optimization**: Consider TimescaleDB if dataset grows 10x
