# System Status & Monitoring

Check system health, performance metrics, and real-time monitoring.

## 🟢 Current System Status

| Component | Status | Details |
|-----------|--------|---------|
| **API** | ✅ Operational | Flask REST API responding |
| **Database** | ✅ Operational | PostgreSQL 17 + TimescaleDB |
| **Cache** | ✅ Operational | Redis running |
| **Frontend** | ✅ Operational | Flask Web App responding |
| **SSL/HTTPS** | ✅ Configured | Nginx SSL termination |
| **Data** | ✅ Updated | Stock, crypto, weather data |

## 📊 Key Metrics

### Data Status
- **Cryptocurrencies**: 230 with price data
- **Price Records**: 2,054,215+ (hourly)
- **Date Range**: 2020-present
- **Last Update**: Hourly (automated)

### Performance
- **Avg Backtest Time**: 0.3-1 second per crypto
- **Cache Hit Rate**: ~60-70%
- **Query Performance**: 10-50ms (optimized)
- **API Response Time**: <100ms (p95)

### System Resources
- **Database Size**: ~5-10 GB
- **Cache Size**: 256 MB
- **Container Memory**: ~2 GB total
- **Disk Usage**: 20-30 GB

## 📈 Performance Dashboard

**Access**: https://localhost/performance

**Displays**:
- Real-time system metrics
- CPU and memory usage
- Database query performance
- Cache hit rates
- API response times
- Active connections

## 🔍 Health Checks

### API Health
```bash
curl http://localhost:5002/health
```

### Database Health
```bash
docker exec docker-project-database pg_isready
```

### Container Status
```bash
docker-compose ps
```

## 📊 Monitoring Queries

### API Response Time (Last 100 requests)
```sql
SELECT 
  endpoint,
  COUNT(*) as requests,
  AVG(response_time_ms) as avg_time,
  MAX(response_time_ms) as max_time,
  MIN(response_time_ms) as min_time
FROM api_performance_logs
ORDER BY requests DESC
LIMIT 10;
```

### Cache Performance
```sql
SELECT 
  cache_key_prefix,
  hits,
  misses,
  ROUND(100.0 * hits / (hits + misses), 2) as hit_rate
FROM cache_stats
ORDER BY hits DESC;
```

### Most Used Cryptocurrencies
```sql
SELECT 
  c.symbol,
  COUNT(br.id) as backtest_count,
  AVG(br.total_return_percentage) as avg_return
FROM backtest_results br
JOIN cryptocurrencies c ON br.crypto_id = c.id
GROUP BY c.id, c.symbol
ORDER BY backtest_count DESC
LIMIT 10;
```

## 🎯 Alerts & Warnings

### ⚠️ Warnings to Watch For

- **API Response Time > 1000ms** - Check database load
- **Cache Hit Rate < 30%** - Consider cache configuration
- **Disk Usage > 90%** - Clean up old backtest results
- **Database Connections > 20** - Check for connection leaks

### 🚨 Critical Issues

- **API Not Responding** - Restart container, check logs
- **Database Down** - Check PostgreSQL status
- **Cache Errors** - Restart Redis
- **Disk Full** - Archive/delete old data, increase volume

## 📅 Maintenance Schedule

| Task | Frequency | Command |
|------|-----------|---------|
| **Backup Database** | Daily | `docker-compose exec database pg_dump -U root webapp_db > backup.sql` |
| **Check Logs** | Daily | `docker-compose logs --tail 100` |
| **Verify Data Freshness** | Hourly | Database auto-update |
| **Clear Cache** | Weekly | `docker-compose exec redis redis-cli FLUSHALL` |
| **Optimize Indexes** | Monthly | `docker-compose exec database vacuumdb -U root webapp_db` |

## 🔧 Common Operations

### Restart All Services
```bash
docker-compose restart
```

### View Real-time Logs
```bash
docker-compose logs -f --tail 50
```

### Check Container Resource Usage
```bash
docker stats
```

### Clear Cache
```bash
docker-compose exec redis redis-cli FLUSHALL
```

## 📞 Getting Help

1. Check [TROUBLESHOOTING.md](../troubleshooting/README.md)
2. Review logs: `docker-compose logs`
3. Check database status: `docker-compose ps`
4. Review performance dashboard for bottlenecks

---

*Last Updated: October 25, 2025*  
*Dashboard: http://localhost:5003/performance-dashboard*
