# Redis Integration & Management Guide

**Complete guide to Redis caching in the cryptocurrency backtesting system**

> **Consolidated from**: REDIS_CACHE_IMPLEMENTATION.md, REDIS_COMMANDS.md, REDIS_TROUBLESHOOTING.md

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Implementation](#implementation)
4. [Redis Commands](#redis-commands)
5. [Cache Management](#cache-management)
6. [Troubleshooting](#troubleshooting)
7. [Performance Monitoring](#performance-monitoring)
8. [Best Practices](#best-practices)

---

## Overview

### Why Redis?

Redis provides:
- **3-5x query speedup** for cached data
- **70-80% cache hit rate** in production
- **Automatic expiration** (TTL-based)
- **Low memory footprint** (15-30MB typical)
- **Simple integration** with Python

### Performance Impact

| Scenario | Without Redis | With Redis | Improvement |
|----------|---------------|------------|-------------|
| First run (cold) | 8s | 8s | 1x (cache miss) |
| Second run (warm) | 8s | 2.5s | **3.2x** |
| Repeated queries | 8s | 0.5s | **16x** |

---

## Architecture

### System Integration

```
┌──────────────┐
│   Frontend   │
│  (Browser)   │
└──────┬───────┘
       │
       ↓
┌──────────────┐      ┌─────────────┐
│   Flask API  │─────→│   Redis     │ (Cache Layer)
│  (Python)    │←─────│  (Docker)   │
└──────┬───────┘      └─────────────┘
       │
       ↓
┌──────────────┐
│  PostgreSQL  │ (Primary Data Store)
│  (Database)  │
└──────────────┘
```

### Cache Flow

```
1. Request → Check Redis for cache key
             │
             ├─ Cache Hit → Return cached data (50ms)
             │
             └─ Cache Miss → Query PostgreSQL (800ms)
                            → Store in Redis (TTL: 1 hour)
                            → Return data
```

### Docker Configuration

```yaml
# docker-compose.yml
services:
  redis:
    image: redis:alpine
    container_name: docker-project-redis
    ports:
      - "6379:6379"
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis-data:/data
    networks:
      - app-network
    restart: unless-stopped

volumes:
  redis-data:
```

---

## Implementation

### Python Integration

#### Installation
```python
# requirements.txt
redis==5.0.1
```

#### Connection Setup
```python
# api/crypto_backtest_service.py
import redis
import json
import pandas as pd

class CryptoBacktestService:
    def __init__(self):
        # Initialize Redis client
        self.redis_client = redis.Redis(
            host='redis',  # Docker service name
            port=6379,
            decode_responses=True,  # Auto-decode bytes to strings
            socket_connect_timeout=5,
            socket_timeout=5
        )
        
        # Cache configuration
        self.cache_ttl = 3600  # 1 hour in seconds
        self.enable_cache = True
        
    def test_redis_connection(self):
        """Test if Redis is available"""
        try:
            self.redis_client.ping()
            return True
        except redis.ConnectionError:
            print("Warning: Redis not available, caching disabled")
            return False
```

### Caching Price Data

```python
def get_price_data_cached(self, crypto_id: int, start_date: str, end_date: str, interval: str = '1h'):
    """Get price data with Redis caching"""
    
    # Generate cache key
    cache_key = f"crypto_prices:{crypto_id}:{start_date}:{end_date}:{interval}"
    
    # Try cache first
    try:
        cached_data = self.redis_client.get(cache_key)
        if cached_data:
            # Cache hit - parse JSON and return DataFrame
            return pd.read_json(cached_data)
    except Exception as e:
        print(f"Redis get error: {e}")
    
    # Cache miss - query database
    df = self.get_price_data(crypto_id, start_date, end_date, interval)
    
    # Store in cache with expiration
    try:
        self.redis_client.setex(
            cache_key,
            self.cache_ttl,
            df.to_json(orient='split', date_format='iso')
        )
    except Exception as e:
        print(f"Redis set error: {e}")
    
    return df
```

### Cache Key Design

#### Key Patterns
```python
# Price data
"crypto_prices:{crypto_id}:{start_date}:{end_date}:{interval}"
# Example: "crypto_prices:1:2024-01-01:2024-12-31:1h"

# Cryptocurrency list
"crypto_list:active"
"crypto_list:all"

# Strategy results
"backtest:{strategy_id}:{crypto_id}:{param_hash}"

# Aggregated data
"crypto_daily:{crypto_id}:{start_date}:{end_date}"
```

#### Key Naming Best Practices
1. **Use colons** to separate namespaces
2. **Include all query parameters** in key
3. **Keep keys short** but descriptive
4. **Use consistent naming** across the app

---

## Redis Commands

### Essential Commands

#### Connection & Status
```bash
# Check if Redis is running
docker exec docker-project-redis redis-cli ping
# Expected output: PONG

# Get Redis info
docker exec docker-project-redis redis-cli INFO

# Get memory usage
docker exec docker-project-redis redis-cli INFO memory

# Get statistics
docker exec docker-project-redis redis-cli INFO stats
```

#### Key Management
```bash
# List all keys
docker exec docker-project-redis redis-cli KEYS '*'

# Count total keys
docker exec docker-project-redis redis-cli DBSIZE

# Find keys by pattern
docker exec docker-project-redis redis-cli --scan --pattern 'crypto_prices:*'

# Get key type
docker exec docker-project-redis redis-cli TYPE crypto_prices:1:2024-01-01:2024-12-31:1h

# Check if key exists
docker exec docker-project-redis redis-cli EXISTS crypto_prices:1:2024-01-01:2024-12-31:1h

# Get key TTL (time to live)
docker exec docker-project-redis redis-cli TTL crypto_prices:1:2024-01-01:2024-12-31:1h
```

#### Data Operations
```bash
# Get value by key
docker exec docker-project-redis redis-cli GET crypto_list:active

# Set value with expiration
docker exec docker-project-redis redis-cli SETEX mykey 3600 "myvalue"

# Delete single key
docker exec docker-project-redis redis-cli DEL crypto_prices:1:2024-01-01:2024-12-31:1h

# Delete keys by pattern
docker exec docker-project-redis redis-cli --scan --pattern 'crypto_prices:*' | xargs docker exec -i docker-project-redis redis-cli DEL
```

#### Cache Clearing
```bash
# Clear all cache (DANGER!)
docker exec docker-project-redis redis-cli FLUSHDB

# Clear only crypto prices
docker exec docker-project-redis redis-cli --scan --pattern 'crypto_prices:*' | \
    xargs docker exec -i docker-project-redis redis-cli DEL

# Clear specific crypto
docker exec docker-project-redis redis-cli --scan --pattern 'crypto_prices:1:*' | \
    xargs docker exec -i docker-project-redis redis-cli DEL
```

#### Monitoring
```bash
# Monitor all commands in real-time
docker exec -it docker-project-redis redis-cli MONITOR

# Get slow queries (>10ms)
docker exec docker-project-redis redis-cli SLOWLOG GET 10

# Reset slow log
docker exec docker-project-redis redis-cli SLOWLOG RESET
```

---

## Cache Management

### Cache Invalidation

#### Automatic Invalidation
```python
def invalidate_crypto_cache(self, crypto_id: int):
    """Invalidate all cache entries for a cryptocurrency"""
    pattern = f"crypto_prices:{crypto_id}:*"
    
    try:
        # Find all matching keys
        cursor = 0
        while True:
            cursor, keys = self.redis_client.scan(
                cursor=cursor,
                match=pattern,
                count=100
            )
            
            # Delete found keys
            if keys:
                self.redis_client.delete(*keys)
            
            # Break when scan completes
            if cursor == 0:
                break
                
        print(f"Invalidated cache for crypto {crypto_id}")
    except Exception as e:
        print(f"Cache invalidation error: {e}")
```

#### Update Trigger
```python
def update_crypto_prices(self, crypto_id: int, new_prices: pd.DataFrame):
    """Update prices and invalidate cache"""
    
    # Insert new prices into database
    with self.get_connection() as conn:
        new_prices.to_sql('crypto_prices', conn, if_exists='append', index=False)
    
    # Invalidate related cache
    self.invalidate_crypto_cache(crypto_id)
```

### Cache Warming

```python
def warm_cache_for_active_cryptos(self, start_date: str, end_date: str):
    """Pre-populate cache with frequently accessed data"""
    
    # Get active cryptocurrencies
    cryptos = self.get_cryptocurrencies_with_data()
    
    print(f"Warming cache for {len(cryptos)} cryptocurrencies...")
    
    for crypto in cryptos:
        # This will cache the data
        self.get_price_data_cached(
            crypto['id'],
            start_date,
            end_date
        )
        print(f"Cached: {crypto['symbol']}")
    
    print("Cache warming complete!")
```

### Cache Statistics

```python
def get_cache_stats(self):
    """Get Redis cache statistics"""
    info = self.redis_client.info()
    
    return {
        'used_memory': info['used_memory_human'],
        'total_keys': self.redis_client.dbsize(),
        'hits': info.get('keyspace_hits', 0),
        'misses': info.get('keyspace_misses', 0),
        'hit_rate': self._calculate_hit_rate(info),
        'evicted_keys': info.get('evicted_keys', 0)
    }

def _calculate_hit_rate(self, info):
    """Calculate cache hit rate percentage"""
    hits = info.get('keyspace_hits', 0)
    misses = info.get('keyspace_misses', 0)
    total = hits + misses
    
    if total == 0:
        return 0
    
    return round((hits / total) * 100, 2)
```

---

## Troubleshooting

### Common Issues

#### 1. Redis Connection Failed

**Symptoms:**
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Diagnosis:**
```bash
# Check if container is running
docker ps | grep redis

# Check container logs
docker logs docker-project-redis

# Test network connectivity
docker exec docker-project-api ping redis
```

**Solutions:**
```bash
# Restart Redis
docker compose restart redis

# Check if port is available
netstat -tulpn | grep 6379

# Rebuild if needed
docker compose up -d --build redis
```

#### 2. Out of Memory

**Symptoms:**
```
OOM command not allowed when used memory > 'maxmemory'
```

**Diagnosis:**
```bash
# Check memory usage
docker exec docker-project-redis redis-cli INFO memory

# Check maxmemory setting
docker exec docker-project-redis redis-cli CONFIG GET maxmemory
```

**Solutions:**
```yaml
# Increase maxmemory in docker-compose.yml
redis:
  command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru

# Or clear old data
docker exec docker-project-redis redis-cli FLUSHDB
```

#### 3. Slow Cache Operations

**Symptoms:**
- Slow response times
- High CPU usage

**Diagnosis:**
```bash
# Check slow queries
docker exec docker-project-redis redis-cli SLOWLOG GET 10

# Monitor commands in real-time
docker exec -it docker-project-redis redis-cli MONITOR
```

**Solutions:**
```python
# Use connection pooling
from redis import ConnectionPool

pool = ConnectionPool(
    host='redis',
    port=6379,
    max_connections=10,
    decode_responses=True
)

redis_client = redis.Redis(connection_pool=pool)
```

#### 4. Stale Data

**Symptoms:**
- Old data showing after updates
- Cache not reflecting changes

**Solutions:**
```bash
# Clear specific cache
docker exec docker-project-redis redis-cli DEL crypto_prices:1:2024-01-01:2024-12-31:1h

# Clear all crypto price cache
docker exec docker-project-redis redis-cli --scan --pattern 'crypto_prices:*' | \
    xargs docker exec -i docker-project-redis redis-cli DEL

# Or implement automatic invalidation (see Cache Invalidation section)
```

#### 5. High Memory Usage

**Diagnosis:**
```bash
# Get memory details
docker exec docker-project-redis redis-cli INFO memory

# Get key sample with sizes
docker exec docker-project-redis redis-cli --bigkeys
```

**Solutions:**
```bash
# Enable compression (if using JSON)
# Reduce TTL
docker exec docker-project-redis redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Monitor evictions
docker exec docker-project-redis redis-cli INFO stats | grep evicted
```

---

## Performance Monitoring

### Metrics Dashboard

```python
def get_redis_dashboard():
    """Get comprehensive Redis metrics"""
    info = redis_client.info()
    
    return {
        'memory': {
            'used': info['used_memory_human'],
            'peak': info['used_memory_peak_human'],
            'limit': info.get('maxmemory_human', 'unlimited'),
            'fragmentation_ratio': info.get('mem_fragmentation_ratio', 0)
        },
        'stats': {
            'total_keys': redis_client.dbsize(),
            'hits': info.get('keyspace_hits', 0),
            'misses': info.get('keyspace_misses', 0),
            'hit_rate': calculate_hit_rate(info),
            'evicted': info.get('evicted_keys', 0),
            'expired': info.get('expired_keys', 0)
        },
        'connections': {
            'connected_clients': info.get('connected_clients', 0),
            'blocked_clients': info.get('blocked_clients', 0),
            'total_commands': info.get('total_commands_processed', 0)
        },
        'persistence': {
            'last_save': info.get('rdb_last_save_time', 0),
            'changes_since_save': info.get('rdb_changes_since_last_save', 0)
        }
    }
```

### Performance Benchmarks

```bash
# Benchmark Redis performance
docker exec docker-project-redis redis-benchmark -t set,get -n 100000 -q

# Results (typical):
# SET: ~50,000 requests per second
# GET: ~80,000 requests per second
```

---

## Best Practices

### 1. Cache Key Design
```python
✅ Good:
"crypto_prices:1:2024-01-01:2024-12-31:1h"  # Clear, includes all params

❌ Bad:
"cache_1_2024"  # Ambiguous, missing params
```

### 2. TTL Management
```python
# Different TTLs for different data types
PRICE_DATA_TTL = 3600        # 1 hour (frequent updates)
CRYPTO_LIST_TTL = 86400      # 24 hours (rarely changes)
BACKTEST_RESULT_TTL = 604800 # 1 week (stable results)
```

### 3. Error Handling
```python
def get_data_safe(self, key):
    """Always handle Redis errors gracefully"""
    try:
        return self.redis_client.get(key)
    except redis.ConnectionError:
        # Log error, continue without cache
        print("Redis unavailable, fetching from database")
        return None
    except Exception as e:
        print(f"Redis error: {e}")
        return None
```

### 4. Monitoring
```python
# Log cache performance
def get_with_metrics(self, key):
    start = time.time()
    result = self.redis_client.get(key)
    elapsed = time.time() - start
    
    if result:
        print(f"Cache hit: {key} ({elapsed:.3f}s)")
    else:
        print(f"Cache miss: {key}")
    
    return result
```

### 5. Connection Pooling
```python
# Use connection pool for better performance
from redis import ConnectionPool

pool = ConnectionPool(
    host='redis',
    port=6379,
    max_connections=10,
    decode_responses=True
)

redis_client = redis.Redis(connection_pool=pool)
```

---

## Conclusion

Redis provides significant performance improvements with minimal complexity:

- ✅ **3-5x faster** queries on cache hit
- ✅ **70-80% hit rate** in production
- ✅ **Simple integration** with Python
- ✅ **Automatic expiration** via TTL
- ✅ **Low memory footprint** (15-30MB)

**Result**: A robust caching layer that dramatically improves user experience!

---

**Last Updated**: October 8, 2025  
**Consolidated From**: 3 Redis documentation files
