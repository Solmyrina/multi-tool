# Performance Dashboard Guide

## Overview
The enhanced Performance Dashboard provides comprehensive monitoring of your system, database, and crypto/stock data health.

## Access
**URL:** `http://localhost/performance` (or your domain)

**Authentication:** Login required

---

## Dashboard Sections

### 1. 🖥️ System Performance
Real-time monitoring of host system resources:
- **CPU Usage** - Current CPU utilization percentage
- **Memory Usage** - RAM consumption
- **Disk I/O** - Disk read/write activity
- **Network I/O** - Network traffic
- **Historical Chart** - 24-hour trend view

### 2. 💾 Database Performance
Core database metrics:
- **Active Connections** - Current database connections
- **Queries/Second** - Transaction rate
- **Avg Query Time** - Query execution performance
- **Database Size** - Total database size
- **Cache Hit Ratio** - Buffer cache efficiency (>95% is excellent)
- **Historical Chart** - Database activity over time

### 3. 📊 Crypto Data Health
Cryptocurrency data monitoring:
- **Total Cryptocurrencies** - Number of tracked crypto assets
- **Total Price Records** - Historical price data points (2M+)
- **Latest Price Data** - Timestamp of most recent price update
- **Prices (Last 24h)** - Recent price updates
- **Cryptos with Indicators** - Assets with technical analysis
- **Technical Indicators** - Total indicator records (1.3M+)
- **Indicators (Last 24h)** - Recent indicator calculations

**Health Indicators:**
- ✅ Green: All data up-to-date
- ⚠️ Yellow: Data older than 1 hour
- ❌ Red: Data older than 24 hours

### 4. 📈 Stock & Weather Data
Additional data source monitoring:
- **Total Stocks** - Number of tracked stock symbols
- **Stock Price Records** - Historical stock prices (748K+)
- **Latest Stock Data** - Most recent stock update
- **Historic Weather Records** - Historical weather data (123K+)
- **Weather Locations** - Number of monitored locations
- **Current Weather Records** - Recent weather observations
- **Weather (Last 1h)** - Fresh weather updates

### 5. 🧹 Table Health & Dead Tuples
PostgreSQL table maintenance status:
- **Live Tuples** - Active data rows
- **Dead Tuples** - Rows pending cleanup
- **Dead %** - Percentage of dead tuples
  - <5% = Good (green)
  - 5-10% = Monitor (yellow)
  - >10% = Vacuum needed (red)
- **Total Size** - Table size including indexes
- **Last Vacuum** - Manual vacuum timestamp
- **Last Autovacuum** - Automatic vacuum timestamp

**Action Items:**
- If dead % > 10%: Table needs VACUUM
- If Last Autovacuum is old: Check autovacuum settings

### 6. 📋 Index Usage Statistics
Index performance and utilization:
- **Index Scans** - How many times index was used
  - 0 scans = Unused index (consider dropping)
  - <100 scans = Low usage (yellow)
  - >100 scans = Good usage (green)
- **Tuples Read** - Rows read from index
- **Tuples Fetched** - Rows returned to queries
- **Index Size** - Disk space used by index

**Optimization Tips:**
- Unused indexes (0 scans) waste space and slow down writes
- Low-usage indexes may not justify their maintenance cost

### 7. ⚡ Query Performance Metrics
Database-level statistics:
- **Cache Hit Ratio** - Percentage of queries served from cache
  - >99% = Excellent
  - 95-99% = Good
  - <95% = Need more memory or optimization
- **Total Commits** - Successful transactions
- **Total Rollbacks** - Failed/aborted transactions
  - High rollback rate may indicate application issues
- **Blocks Hit (Cache)** - Number of cache hits

### 8. 🐳 Container Status
Docker container health:
- Container name and status
- CPU/Memory usage per container
- Restart count
- Uptime

---

## Features

### Auto-Refresh
- **Default:** Enabled (30-second intervals)
- **Toggle:** Use checkbox to enable/disable
- **Manual Refresh:** Click "Refresh Data" button

### Time Range Selection
View historical data for different periods:
- Last Hour
- Last 6 Hours
- **Last 24 Hours** (default)
- Last Week

### Color Coding
- 🟢 **Green** - Healthy/Good performance
- 🟡 **Yellow** - Warning/Monitor
- 🔴 **Red** - Critical/Action needed

---

## Performance Baselines

### Excellent Performance
- Cache Hit Ratio: >99%
- Dead Tuple Ratio: <2%
- CPU Usage: <50%
- Memory Usage: <70%
- All data updated within last hour

### Good Performance
- Cache Hit Ratio: 95-99%
- Dead Tuple Ratio: 2-5%
- CPU Usage: 50-70%
- Memory Usage: 70-85%
- Data updated within last 6 hours

### Needs Attention
- Cache Hit Ratio: <95%
- Dead Tuple Ratio: >10%
- CPU Usage: >80%
- Memory Usage: >85%
- Data older than 24 hours

---

## Troubleshooting

### Issue: Cache Hit Ratio < 95%
**Possible Causes:**
- Insufficient shared_buffers
- Working set larger than available cache
- Inefficient queries causing sequential scans

**Solutions:**
1. Increase `shared_buffers` in PostgreSQL config
2. Add appropriate indexes
3. Optimize queries with EXPLAIN ANALYZE

### Issue: High Dead Tuple Ratio (>10%)
**Possible Causes:**
- Autovacuum not running frequently enough
- High update/delete activity
- Long-running transactions blocking cleanup

**Solutions:**
1. Run manual VACUUM: `VACUUM ANALYZE table_name;`
2. Check autovacuum settings
3. Review long-running transactions

### Issue: Unused Indexes (0 scans)
**Possible Causes:**
- Index not matching query patterns
- Better indexes exist
- Table too small for index to be useful

**Solutions:**
1. Review queries with EXPLAIN
2. Consider dropping unused indexes
3. Monitor after dropping to confirm no regression

### Issue: Data Not Updating
**Check:**
1. Background jobs running: `docker ps`
2. Cron schedules: `docker exec docker-project-api crontab -l`
3. Service logs: `docker logs docker-project-api`
4. API connectivity: Test `/api/performance/test`

---

## API Endpoints

The dashboard uses these REST endpoints:

```
GET /api/performance/system/current       - Current system metrics
GET /api/performance/system/history       - Historical system data
GET /api/performance/database/current     - Current DB metrics
GET /api/performance/database/history     - Historical DB data
GET /api/performance/database/health      - Detailed DB health (NEW)
GET /api/performance/containers/current   - Container status
GET /api/performance/alerts               - Performance alerts
GET /api/performance/slow-queries         - Slow query log
```

All endpoints require authentication and return JSON.

---

## Updates (October 8, 2025)

### New in PostgreSQL 17 Upgrade
- ✅ Enhanced performance monitoring
- ✅ Detailed dead tuple tracking
- ✅ Index usage statistics
- ✅ Crypto data health metrics
- ✅ Query performance breakdown
- ✅ Real-time cache hit ratios

### Added Sections
1. Crypto Data Health panel
2. Stock & Weather Data panel
3. Table Health & Dead Tuples table
4. Index Usage Statistics table
5. Query Performance Metrics cards

---

## Next Steps

For production deployments, consider:

1. **Alerting** - Set up alerts for critical thresholds
2. **Historical Retention** - Configure data retention policies
3. **Export** - Add CSV/JSON export functionality
4. **Mobile** - Responsive design for mobile monitoring
5. **Grafana** - Integrate with Grafana for advanced dashboards

For questions or issues, check the logs:
```bash
docker logs docker-project-webapp
docker logs docker-project-database
```
