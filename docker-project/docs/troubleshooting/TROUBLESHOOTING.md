# Troubleshooting Guide

**Common issues, errors, and their solutions**

---

## Quick Troubleshooting Matrix

| Issue | Error | Cause | Solution |
|-------|-------|-------|----------|
| Backtest returns 500 | "Response status code does not indicate success: 500" | API model mismatch | [See Backtest Errors](#backtest-errors) |
| Can't login | "Too many failed attempts" | Rate limit exceeded | [See Login Issues](#login-issues) |
| Dashboard empty | No data appears | Route not registered | [See Performance Dashboard](#performance-dashboard-not-loading) |
| Slow queries | DB takes 14+ seconds | Missing indexes or wrong query | [See Slow Queries](#slow-queries) |
| Cache stale | Old data shows | Cache not invalidating | [See Cache Issues](#cache-issues) |

---

## Backtest Errors

### Error: 500 Internal Server Error

**Symptom**:
```
Error creating backtest: Response status code does not indicate success: 500 (Internal Server Error).
```

**API Log Shows**:
```
Backtest requested: Strategy 1, Crypto 0
Error executing backtest
System.InvalidOperationException: Insufficient price data: 0 data points. Need at least 50.
```

**Root Cause**: API model property mismatch

The Blazor UI sends `CryptocurrencyId` but the API expects `cryptoId`. When the property name doesn't match, it defaults to 0 (no cryptocurrency selected).

**Solution**:

Check if `[JsonPropertyName]` attributes are present in `/blazor-ui/Models/ApiModels.cs`:

```csharp
using System.Text.Json.Serialization;

public class BacktestRequest
{
    [JsonPropertyName("cryptoId")]
    public int CryptocurrencyId { get; set; }
    
    [JsonPropertyName("strategyId")]
    public int StrategyId { get; set; }
    
    [JsonPropertyName("startDate")]
    public DateTime StartDate { get; set; }
    
    [JsonPropertyName("endDate")]
    public DateTime EndDate { get; set; }
    
    [JsonPropertyName("initialInvestment")]
    public decimal InitialCapital { get; set; } = 10000m;
    
    [JsonPropertyName("parameters")]
    public Dictionary<string, object>? Parameters { get; set; }
}
```

**Verify**:
```bash
# Check API logs
docker logs docker-project-api --tail 50 | grep -i "crypto"

# Should see: "Crypto 1" (not "Crypto 0")
```

---

### Error: "Insufficient price data: 0 data points"

**Symptom**: Backtest fails with "Need at least 50" data points

**Causes**:
1. **Wrong cryptocurrency selected** (sends ID 0)
2. **Selected interval has no data** (only 1h available currently)
3. **Date range outside available data** (before 2020 or future dates)
4. **Cryptocurrency marked inactive**

**Solutions**:

**1. Check available data**:
```sql
docker exec docker-project-database psql -U root webapp_db -c "
SELECT 
    c.symbol,
    COUNT(*) as record_count,
    MIN(datetime) as earliest,
    MAX(datetime) as latest,
    CASE WHEN COUNT(*) >= 50 THEN '✓ OK' ELSE '✗ No data' END as status
FROM cryptocurrencies c
LEFT JOIN crypto_prices cp ON c.id = cp.crypto_id
WHERE c.is_active = true
GROUP BY c.symbol
HAVING COUNT(*) > 0
ORDER BY record_count DESC;"
```

**2. For your backtest**:
```sql
-- Check if selected crypto has data for date range
docker exec docker-project-database psql -U root webapp_db -c "
SELECT COUNT(*) as price_count
FROM crypto_prices
WHERE crypto_id = 1  -- Replace with your crypto ID
    AND interval_type = '1h'  -- Replace with selected interval
    AND datetime BETWEEN '2024-01-01' AND '2024-01-31';"
```

**3. Select different parameters**:
- ✓ Use existing cryptos (Bitcoin, Ethereum, etc.)
- ✓ Use 1h interval (only one with data)
- ✓ Use date range between 2020-01-01 and today
- ✗ Avoid 4h and 1d intervals (no data yet)

---

### Error: "Invalid interval: 2h"

**Symptom**: Cannot use custom interval

**Cause**: Only 1h, 4h, 1d are supported

**Solution**: Change interval to one of the three supported values:
```bash
# Valid intervals
"1h"  ✓ Supported, has data
"4h"  ✓ Supported, no data
"1d"  ✓ Supported, no data

# Invalid intervals
"2h"  ✗ Not supported
"15m" ✗ Not supported
"1w"  ✗ Not supported
```

---

## Login Issues

### Error: "Too many failed attempts. Please try again in 15 minutes"

**Symptom**: Cannot login after several failed attempts

**Cause**: Rate limiting after 20 failed attempts within 15 minutes

**Current Settings**:
- **Max attempts**: 20 failed attempts (was 5)
- **Time window**: 15 minutes
- **Lockout duration**: 15 minutes

**Solutions**:

**Option 1: Wait 15 minutes** (Easiest)
- The lockout automatically expires after 15 minutes
- Try logging in again

**Option 2: Clear login attempts** (If urgent)

```bash
# Clear for specific user
docker exec docker-project-database psql -U root webapp_db -c "
DELETE FROM login_attempts WHERE username='admin';"

# Clear for specific IP
docker exec docker-project-database psql -U root webapp_db -c "
DELETE FROM login_attempts WHERE ip_address='YOUR.IP.ADDRESS';"

# Clear all (nuclear option)
docker exec docker-project-database psql -U root webapp_db -c "
DELETE FROM login_attempts;"
```

**Option 3: Check account status**

```bash
# Is user active?
docker exec docker-project-database psql -U root webapp_db -c "
SELECT username, is_active FROM users WHERE username='admin';"

# If not active, activate:
docker exec docker-project-database psql -U root webapp_db -c "
UPDATE users SET is_active = TRUE WHERE username='admin';"
```

**Option 4: Check IP restrictions** (if any)

```bash
# See login history
docker exec docker-project-database psql -U root webapp_db -c "
SELECT username, success, ip_address, attempted_at
FROM login_attempts
WHERE username='admin'
ORDER BY attempted_at DESC
LIMIT 20;"
```

---

### Error: "Invalid credentials"

**Symptom**: Username or password is wrong, even though you entered it correctly

**Causes**:
1. **Caps lock on** (passwords are case-sensitive)
2. **Wrong username** (case-sensitive)
3. **Spaces in password** (pasted from notes)
4. **User doesn't exist**
5. **User is inactive**

**Solutions**:

```bash
# 1. Check if user exists
docker exec docker-project-database psql -U root webapp_db -c "
SELECT username, is_active FROM users WHERE username='admin';"

# 2. Reset password (get hash)
python3 -c "import bcrypt; print(bcrypt.hashpw(b'newpassword123', bcrypt.gensalt()).decode())"

# 3. Update password in database
docker exec docker-project-database psql -U root webapp_db -c "
UPDATE users 
SET password_hash = 'PASTE_HASH_HERE'
WHERE username='admin';"

# 4. Try logging in with new password
```

---

## Performance Dashboard Not Loading

### Issue: Performance dashboard shows no data

**Symptom**:
- Page loads but all metric sections are empty
- No "Table Health", "Database Stats", or "Query Performance" data
- Console shows network errors

**Root Cause**: Flask route not registered (defined after app startup code)

**Solution**: Verify the endpoint is registered

```bash
# Test endpoint
curl http://localhost:8080/api/performance/database/health

# Should return JSON with metrics, not 404
```

If returns 404:
```bash
# Restart webapp
docker compose restart webapp

# Check logs
docker logs docker-project-webapp | tail -50 | grep health

# Should see no errors loading health endpoint
```

**File Fix**: `/webapp/app.py` line ~4650

Ensure route is defined **BEFORE** `if __name__ == '__main__':`:

```python
# ✓ CORRECT (before main block)
@app.route('/api/performance/database/health')
def get_performance_health():
    ...

if __name__ == '__main__':
    # Flask app startup
    ...

# ✗ WRONG (after main block - never registered!)
@app.route('/api/performance/database/health')
def duplicate_route():
    ...
```

---

## Slow Queries

### Issue: `/cryptocurrencies` endpoint takes 14-17 seconds

**Symptom**: Response hangs for 14+ seconds with 200 cryptocurrencies

**Root Cause**: Inefficient `EXISTS` subquery against TimescaleDB hypertable

**Problem Query**:
```sql
SELECT * FROM cryptocurrencies c 
WHERE c.is_active = true 
AND EXISTS (SELECT 1 FROM crypto_prices WHERE crypto_id = c.id)
```

**Issue**: 
- Hypertable has 1,052+ compressed chunks
- `EXISTS` decompresses chunks for each of 263 cryptocurrencies
- Severe decompression overhead = 14-17 seconds

**Solution**: Use denormalized flag instead

```sql
-- Add boolean column
ALTER TABLE cryptocurrencies 
ADD COLUMN has_price_data BOOLEAN DEFAULT false;

-- Populate with current data
UPDATE cryptocurrencies c
SET has_price_data = true
WHERE EXISTS (SELECT 1 FROM crypto_prices WHERE crypto_id = c.id);

-- Add index
CREATE INDEX idx_cryptocurrencies_has_price_data 
ON cryptocurrencies(is_active, has_price_data) 
WHERE is_active = true AND has_price_data = true;

-- Add trigger to maintain flag
CREATE FUNCTION update_crypto_has_price_data()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE cryptocurrencies 
    SET has_price_data = true 
    WHERE id = NEW.crypto_id AND has_price_data = false;
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
WHERE is_active = true AND has_price_data = true
ORDER BY symbol;
```

**Result**: **14-17 seconds → 50ms** (280x faster!)

---

### Issue: Database queries getting slower over time

**Symptom**: Queries that were fast (50ms) now take 500ms

**Causes**:
1. **Table bloat** from updates (dead tuples)
2. **Stale statistics** (query planner uses wrong estimates)
3. **Missing indexes** for new query patterns
4. **Cache eviction** due to memory pressure

**Solutions**:

```bash
# 1. VACUUM to remove dead tuples
docker exec docker-project-database psql -U root webapp_db -c "VACUUM ANALYZE crypto_prices;"

# 2. REINDEX to rebuild indexes
docker exec docker-project-database psql -U root webapp_db -c "REINDEX TABLE crypto_prices;"

# 3. Analyze table statistics
docker exec docker-project-database psql -U root webapp_db -c "ANALYZE cryptocurrencies;"

# 4. Check table and index sizes
docker exec docker-project-database psql -U root webapp_db -c "
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"

# 5. View current index usage
docker exec docker-project-database psql -U root webapp_db -c "
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as uses,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;"
```

**Maintenance Schedule**:
```bash
# Run weekly
docker exec docker-project-database psql -U root webapp_db -c "
VACUUM ANALYZE crypto_prices;
ANALYZE cryptocurrencies;
REINDEX TABLE crypto_prices;"
```

---

### Issue: High memory usage

**Symptom**: Docker container memory creeping up

**Causes**:
1. **Cache size growing** (Redis or app cache)
2. **Dead connections** holding memory
3. **Memory leak** in application code

**Solutions**:

```bash
# 1. Check Redis memory
docker exec docker-project-redis redis-cli INFO memory

# 2. Clear Redis if needed
docker exec docker-project-redis redis-cli FLUSHDB

# 3. Check database connections
docker exec docker-project-database psql -U root webapp_db -c "
SELECT 
    datname,
    usename,
    state,
    COUNT(*) as connection_count
FROM pg_stat_activity
GROUP BY datname, usename, state;"

# 4. Kill idle connections
docker exec docker-project-database psql -U root webapp_db -c "
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'idle' 
  AND query_start < NOW() - INTERVAL '1 hour';"

# 5. Restart service if needed
docker compose restart redis
docker compose restart database
```

---

## Cache Issues

### Issue: Stale data showing in backtest results

**Symptom**: Results show old data even after price updates

**Root Cause**: Redis cache not invalidating when new data arrives

**Solutions**:

```bash
# 1. View cached keys
docker exec docker-project-redis redis-cli KEYS "crypto_prices:*" | head -20

# 2. Clear specific cache pattern
docker exec docker-project-redis redis-cli EVAL "
return redis.call('del', unpack(redis.call('keys', ARGV[1])))
" 0 'crypto_prices:*'

# 3. Clear ALL cache (nuclear option)
docker exec docker-project-redis redis-cli FLUSHDB

# 4. Check cache TTL
docker exec docker-project-redis redis-cli TTL "crypto_prices:1:2024-01-01:2024-01-31"
# Should return positive number (seconds remaining)
```

**To Prevent**:

Ensure trigger on `crypto_prices` table invalidates cache:

```sql
-- Verify trigger exists
docker exec docker-project-database psql -U root webapp_db -c "
SELECT tgname FROM pg_trigger 
WHERE tgrelid = 'crypto_prices'::regclass;"

-- Should show: invalidate_crypto_cache or similar

-- If missing, create it:
CREATE FUNCTION invalidate_crypto_cache()
RETURNS TRIGGER AS $$
BEGIN
    -- Application code should handle cache invalidation
    -- For now, just log the change
    RAISE NOTICE 'Cache invalidation for crypto % at %', NEW.crypto_id, NEW.datetime;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER invalidate_cache_on_price_insert
AFTER INSERT ON crypto_prices
FOR EACH ROW
EXECUTE FUNCTION invalidate_crypto_cache();
```

---

## Network & Connectivity

### Error: "Cannot connect to database"

**Symptom**: API or web app can't reach PostgreSQL

**Causes**:
1. Database container not running
2. Network not connected
3. Connection string wrong
4. Password wrong
5. Firewall blocking

**Solutions**:

```bash
# 1. Check if database is running
docker ps | grep database

# 2. Check if it's actually healthy
docker exec docker-project-database psql -U root -d webapp_db -c "SELECT 1;"

# 3. Check network
docker network ls | grep docker-project

# 4. Check connection string in app config
docker compose config | grep DATABASE

# 5. Test from another container
docker exec docker-project-api psql -h database -U root -d webapp_db -c "SELECT 1;"

# 6. If network issue, restart services
docker compose restart
```

### Error: "Cannot connect to Redis"

**Symptom**: Caching errors or SSE streaming failures

**Solutions**:

```bash
# 1. Check Redis is running
docker exec docker-project-redis redis-cli ping
# Should return: PONG

# 2. Check connection
docker exec docker-project-api redis-cli -h redis ping

# 3. Check for network connectivity
docker network inspect docker-project_default | grep redis

# 4. Check Redis logs
docker logs docker-project-redis | tail -50

# 5. Restart if needed
docker compose restart redis
```

---

## API Endpoint Issues

### Error: Endpoint returns 404

**Symptom**: "Not Found" when calling API endpoint

**Causes**:
1. **Wrong URL path**
2. **Route not registered**
3. **App restart needed**
4. **Typo in route decorator**

**Solutions**:

```bash
# 1. Verify endpoint exists in code
grep -r "/api/crypto/backtest/stream" /home/one_control/docker-project/api/

# 2. Check if route is registered
docker exec docker-project-api python3 -c "
from api import app
for rule in app.url_map.iter_rules():
    if 'backtest' in str(rule):
        print(rule)
"

# 3. Restart API
docker compose restart api

# 4. Test endpoint directly
curl -X POST http://localhost:8000/api/crypto/backtest/stream \
  -H "Content-Type: application/json" \
  -d '{"strategy_id": 1, "parameters": {}}'
```

---

## Docker Issues

### Error: "No such container"

**Symptom**: "docker exec docker-project-database: no such container"

**Solutions**:

```bash
# 1. List actual container names
docker ps

# 2. Use correct name
docker exec docker-project-database psql ...
# Or for Python:
docker exec docker-project-api python3 ...

# 3. Check docker-compose.yml for service names
grep "container_name:" docker-compose.yml

# 4. Recreate if needed
docker compose down
docker compose up -d
```

### Error: "Cannot connect to Docker daemon"

**Solutions**:

```bash
# 1. Check if Docker is running
systemctl status docker

# 2. Start Docker
sudo systemctl start docker

# 3. Add user to docker group
sudo usermod -aG docker $USER
# Log out and log back in

# 4. Check Docker permissions
docker ps
```

---

## Monitoring & Debugging

### View Real-Time Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api

# Tail last 100 lines
docker logs -f --tail 100 docker-project-api

# Filter by pattern
docker logs docker-project-api 2>&1 | grep -i error
```

### Check System Resources

```bash
# Container resource usage
docker stats

# Database cache hit ratio
docker exec docker-project-database psql -U root webapp_db -c "
SELECT 
    SUM(heap_blks_read) as disk_reads,
    SUM(heap_blks_hit) as cache_hits,
    ROUND(100.0 * SUM(heap_blks_hit) / (SUM(heap_blks_hit) + SUM(heap_blks_read)), 2) as cache_hit_ratio
FROM pg_statio_user_tables;"

# Database connections
docker exec docker-project-database psql -U root webapp_db -c "
SELECT count(*) FROM pg_stat_activity;"

# Disk usage
docker compose exec database du -sh /var/lib/postgresql/data
```

---

## Advanced Troubleshooting

### Enable Debug Logging

```bash
# Python API
docker compose exec api python3 -c "
import logging
logging.basicConfig(level=logging.DEBUG)
"

# Check logs with debug output
docker compose logs -f api | grep -i debug
```

### Database Query Analysis

```bash
# Slow query log
docker exec docker-project-database psql -U root webapp_db -c "
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;"

# Full query plan
docker exec docker-project-database psql -U root webapp_db -c "
EXPLAIN ANALYZE 
SELECT * FROM crypto_prices 
WHERE crypto_id = 1 AND interval_type = '1h' 
LIMIT 1000;"
```

---

## Getting Help

### Collect Debug Information

When reporting issues, gather:

```bash
# Environment info
docker compose version
docker --version
docker compose ps

# Recent logs (all services)
docker compose logs --tail 100 > debug-logs.txt

# Database status
docker exec docker-project-database psql -U root webapp_db -c "
SELECT version(); SELECT datname, numbackends FROM pg_stat_database;" > db-status.txt

# Container resource usage
docker stats --no-stream > resource-usage.txt

# Network status
docker network inspect docker-project_default > network-status.txt
```

---

## Contact & Support

**For persistent issues**:
1. Collect debug information (see above)
2. Check recent changes or deployments
3. Review related documentation
4. Contact development team with logs

---

**Last Updated**: October 25, 2025  
**Maintained By**: Development Team  
**Version**: 1.0
