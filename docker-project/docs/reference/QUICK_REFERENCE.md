# Quick Reference Guide

**Common commands, API calls, and code snippets for the cryptocurrency backtesting system**

---

## API Endpoints

### Backtesting

#### Run Single Backtest
```bash
curl -X POST http://localhost:5002/backtest \
  -H "Content-Type: application/json" \
  -d '{
    "cryptoId": 1,
    "strategyId": 1,
    "startDate": "2024-01-01T00:00:00",
    "endDate": "2024-12-31T23:59:59",
    "initialInvestment": 10000,
    "interval": "1h",
    "parameters": {
      "rsi_period": 14,
      "rsi_oversold": 30,
      "rsi_overbought": 70
    }
  }'
```

#### Run Strategy Against All Cryptos (Streaming)
```bash
curl -N http://localhost:8000/api/crypto/backtest/stream \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_id": 1,
    "parameters": {
      "rsi_period": 14,
      "rsi_oversold": 30,
      "rsi_overbought": 70
    }
  }'
```

#### Get Cryptocurrencies
```bash
curl http://localhost:8000/api/cryptocurrencies
```

#### Get Strategies
```bash
curl http://localhost:8000/api/strategies
```

---

## Database Queries

### Check Available Data

```sql
-- Data volume by interval
SELECT 
    interval_type,
    COUNT(*) as record_count,
    MIN(datetime) as earliest,
    MAX(datetime) as latest,
    ROUND(pg_total_relation_size('crypto_prices') / 1024.0 / 1024.0, 2) as size_mb
FROM crypto_prices
GROUP BY interval_type
ORDER BY interval_type;
```

### Cryptos with Price Data

```sql
-- Find cryptocurrencies with available price data
SELECT 
    c.id,
    c.symbol,
    c.name,
    COUNT(cp.id) as price_count,
    MIN(cp.datetime) as earliest_data,
    MAX(cp.datetime) as latest_data
FROM cryptocurrencies c
LEFT JOIN crypto_prices cp ON c.id = cp.crypto_id
WHERE c.is_active = true AND cp.crypto_id IS NOT NULL
GROUP BY c.id, c.symbol, c.name
ORDER BY price_count DESC;
```

### Latest Prices

```sql
-- Get latest price for each cryptocurrency
SELECT 
    c.id,
    c.symbol,
    cp.open_price,
    cp.close_price,
    cp.high_price,
    cp.low_price,
    cp.volume,
    cp.datetime
FROM cryptocurrencies c
LEFT JOIN crypto_prices cp ON c.id = cp.crypto_id
WHERE cp.datetime = (
    SELECT MAX(datetime) FROM crypto_prices WHERE crypto_id = c.id
)
AND c.is_active = true
ORDER BY c.symbol;
```

### Specific Date Range

```sql
-- Get hourly data for Bitcoin in January 2024
SELECT 
    datetime,
    open_price,
    high_price,
    low_price,
    close_price,
    volume
FROM crypto_prices
WHERE crypto_id = 1  -- Bitcoin
    AND interval_type = '1h'
    AND datetime BETWEEN '2024-01-01' AND '2024-01-31'
ORDER BY datetime;
```

### Missing Data Detection

```sql
-- Find gaps in price data
SELECT 
    c.symbol,
    (d.dte || ' to ' || LEAD(d.dte) OVER (PARTITION BY c.id ORDER BY d.dte)) as gap
FROM (
    SELECT DISTINCT DATE(datetime) as dte, crypto_id
    FROM crypto_prices
    WHERE interval_type = '1h'
) d
JOIN cryptocurrencies c ON d.crypto_id = c.id
WHERE DATE(d.dte + INTERVAL '1 day') < 
      LEAD(d.dte) OVER (PARTITION BY d.crypto_id ORDER BY d.dte)
ORDER BY c.symbol, d.dte;
```

---

## Docker Commands

### Service Management

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# View service logs
docker compose logs -f api

# Restart specific service
docker compose restart api

# View running containers
docker ps

# View all containers (including stopped)
docker ps -a
```

### Database Access

```bash
# Connect to PostgreSQL CLI
docker exec -it docker-project-database psql -U root -d webapp_db

# Backup database
docker exec docker-project-database pg_dump -U root webapp_db > backup.sql

# Restore database
docker exec -i docker-project-database psql -U root -d webapp_db < backup.sql

# Check database size
docker exec docker-project-database psql -U root -d webapp_db -c "SELECT pg_size_pretty(pg_database_size('webapp_db'));"
```

### Redis Cache

```bash
# Connect to Redis CLI
docker exec -it docker-project-redis redis-cli

# Check memory usage (in Redis CLI)
INFO memory

# Clear all cache
FLUSHDB

# Get specific key
GET "crypto_prices:1:2024-01-01:2024-01-31"

# Monitor live commands
MONITOR
```

### pgAdmin

```bash
# Access pgAdmin
http://localhost:5050

# Default credentials
Email: admin@admin.com
Password: root

# Register server:
Host: database
Port: 5432
Username: root
Password: root
```

---

## Trading Strategies

### RSI Strategy

```python
from pandas_ta import rsi

def rsi_strategy(prices: pd.Series, period: int = 14, 
                 oversold: int = 30, overbought: int = 70):
    """RSI-based trading strategy"""
    rsi_values = rsi(prices, length=period)
    
    signals = []
    for i, value in enumerate(rsi_values):
        if value < oversold:
            signals.append('BUY')
        elif value > overbought:
            signals.append('SELL')
        else:
            signals.append('HOLD')
    
    return signals, rsi_values
```

### Moving Average Crossover

```python
def ma_crossover_strategy(prices: pd.Series, fast_period: int = 10, 
                          slow_period: int = 20):
    """Moving Average Crossover strategy"""
    fast_ma = prices.rolling(window=fast_period).mean()
    slow_ma = prices.rolling(window=slow_period).mean()
    
    signals = []
    for i in range(1, len(prices)):
        if fast_ma.iloc[i-1] <= slow_ma.iloc[i-1] and fast_ma.iloc[i] > slow_ma.iloc[i]:
            signals.append('BUY')
        elif fast_ma.iloc[i-1] >= slow_ma.iloc[i-1] and fast_ma.iloc[i] < slow_ma.iloc[i]:
            signals.append('SELL')
        else:
            signals.append('HOLD')
    
    return signals, fast_ma, slow_ma
```

### Bollinger Bands

```python
def bollinger_bands_strategy(prices: pd.Series, period: int = 20, 
                             std_dev: float = 2):
    """Bollinger Bands strategy"""
    middle_band = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper_band = middle_band + (std * std_dev)
    lower_band = middle_band - (std * std_dev)
    
    signals = []
    for i, price in enumerate(prices):
        if price < lower_band.iloc[i]:
            signals.append('BUY')
        elif price > upper_band.iloc[i]:
            signals.append('SELL')
        else:
            signals.append('HOLD')
    
    return signals, upper_band, middle_band, lower_band
```

---

## Common CLI Operations

### System Health Check

```bash
# Check if all services are running
docker compose ps

# View resource usage
docker stats

# Check API health
curl http://localhost:8000/health

# Check UI health
curl http://localhost:8080/

# Check Nginx status
curl http://localhost/health || curl http://localhost
```

### Performance Monitoring

```bash
# Real-time performance metrics
docker compose exec database psql -U root -d webapp_db -c \
  "SELECT query, calls, mean_time, total_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# Table sizes
docker compose exec database psql -U root -d webapp_db -c \
  "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) FROM pg_tables ORDER BY pg_total_relation_size DESC;"

# Index effectiveness
docker compose exec database psql -U root -d webapp_db -c \
  "SELECT indexname, idx_scan, idx_tup_read, idx_tup_fetch FROM pg_stat_user_indexes ORDER BY idx_scan DESC;"
```

### Data Collection

```bash
# Collect current weather
docker compose exec api python collect_current_weather.py

# Collect historic weather (if applicable)
docker compose exec api python collect_historic_weather.py

# Update cryptocurrency list
docker compose exec api python add_popular_nasdaq_stocks.py

# Check weather data collection status
docker compose exec api python weather_status.py
```

---

## Troubleshooting Commands

### Service Issues

```bash
# View service logs (last 50 lines)
docker compose logs --tail=50 api

# View logs in real-time
docker compose logs -f webapp

# Check service startup logs
docker compose logs database | grep -i error

# Restart and view logs
docker compose restart api && docker compose logs -f api
```

### Database Issues

```bash
# Check database connection
docker compose exec database psql -U root -d webapp_db -c "SELECT 1;"

# View active connections
docker compose exec database psql -U root -d webapp_db -c \
  "SELECT datname, usename, state FROM pg_stat_activity;"

# Kill hung queries
docker compose exec database psql -U root -d webapp_db -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'active' AND query_start < NOW() - INTERVAL '5 minutes';"

# Vacuum and analyze
docker compose exec database psql -U root -d webapp_db -c "VACUUM ANALYZE crypto_prices;"
```

### Redis Issues

```bash
# Test Redis connection
docker compose exec redis redis-cli ping

# Monitor Redis commands
docker compose exec redis redis-cli MONITOR

# Check memory
docker compose exec redis redis-cli INFO memory

# Flush cache
docker compose exec redis redis-cli FLUSHDB
```

### API Issues

```bash
# Check API logs
docker compose logs api | tail -100

# Test API endpoint
curl -v http://localhost:8000/api/cryptocurrencies

# Check API status
curl http://localhost:8000/health

# Restart API
docker compose restart api
```

---

## Configuration Reference

### Environment Variables

```bash
# Docker Compose .env file locations:
# /docker-project/.env

# Database
DATABASE_HOST=database
DATABASE_PORT=5432
DATABASE_USER=root
DATABASE_PASSWORD=root
DATABASE_NAME=webapp_db

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# API
API_PORT=8000
API_DEBUG=false

# UI
UI_PORT=8080
UI_API_URL=http://api:8000
```

### Database Connection Strings

```
PostgreSQL Direct:
postgresql://root:root@localhost:5432/webapp_db

Via SSH Tunnel:
ssh -L 5432:database:5432 user@server
postgresql://root:root@localhost:5432/webapp_db

Connection Pool:
postgresql://root:root@database:5432/webapp_db?pool_size=10
```

---

## Performance Benchmarks

### Expected Performance

| Operation | Time | Notes |
|-----------|------|-------|
| Single backtest (1h, 1 month) | 50-100ms | Includes data fetch + calculation |
| Strategy vs 48 cryptos (cached) | 3-5s | All in parallel |
| First result streaming | 0.1s | Progressive loading |
| Redis cache lookup | 50ms | Per 48 cryptos |
| Database query (1h data) | 50-100ms | With indexes |
| Cryptocurrency filtering | 50ms | With denormalized flag |

---

## Code Examples

### Python Client Library

```python
import requests
import json

class BacktestClient:
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
    
    def run_backtest(self, crypto_id, strategy_id, start_date, end_date, interval="1h"):
        """Run single backtest"""
        response = requests.post(
            f"{self.api_url}/api/crypto/backtest",
            json={
                "crypto_id": crypto_id,
                "strategy_id": strategy_id,
                "start_date": start_date,
                "end_date": end_date,
                "interval": interval,
                "parameters": {"rsi_period": 14}
            }
        )
        return response.json()
    
    def get_cryptos(self):
        """Get available cryptocurrencies"""
        response = requests.get(f"{self.api_url}/api/cryptocurrencies")
        return response.json()

# Usage
client = BacktestClient()
result = client.run_backtest(1, 1, "2024-01-01", "2024-01-31")
print(f"Total return: {result['total_return']}%")
```

### JavaScript/TypeScript Client

```typescript
interface BacktestRequest {
    crypto_id: number;
    strategy_id: number;
    start_date: string;
    end_date: string;
    interval: "1h" | "4h" | "1d";
    parameters: Record<string, any>;
}

class BacktestService {
    async runBacktest(request: BacktestRequest): Promise<any> {
        const response = await fetch('/api/crypto/backtest', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request)
        });
        return response.json();
    }
    
    async runStreamingBacktest(strategyId: number, params: any): Promise<void> {
        const response = await fetch('/api/crypto/backtest/stream', {
            method: 'POST',
            body: JSON.stringify({ strategy_id: strategyId, parameters: params })
        });
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const text = decoder.decode(value);
            const lines = text.split('\n');
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = JSON.parse(line.slice(6));
                    console.log(data);
                }
            }
        }
    }
}
```

---

## Related Documentation

- 📖 [Backtesting Guide](../guides/BACKTESTING.md) - Complete backtesting guide
- 📖 [Database Guide](../guides/DATABASE.md) - Database access and queries
- 📖 [API Reference](../architecture/API_ENDPOINTS.md) - Full API documentation
- 📖 [Troubleshooting](./TROUBLESHOOTING.md) - Common issues and fixes

---

**Last Updated**: October 25, 2025  
**Format**: Quick reference with copy-paste examples  
**Maintenance**: Updated with each API change
