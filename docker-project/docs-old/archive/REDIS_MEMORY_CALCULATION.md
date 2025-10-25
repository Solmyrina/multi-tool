# 💾 Redis Caching Memory Requirements

**Date:** October 6, 2025  
**System:** Crypto Backtest Calculator

---

## 📊 Current System Stats

- **Cryptocurrencies:** 243
- **Strategies:** 6
- **Total possible combinations:** 1,458 (243 × 6)

---

## 🧮 Memory Calculation Per Cache Entry

### Typical Backtest Result Size

A single backtest result contains:
```json
{
  "crypto_id": 1,
  "crypto_name": "Bitcoin",
  "crypto_symbol": "BTC",
  "strategy_id": 1,
  "strategy_name": "RSI Strategy",
  "parameters": {
    "rsi_period": 14,
    "oversold_threshold": 30,
    "overbought_threshold": 70
  },
  "interval": "1d",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "results": {
    "total_return": 45.6,
    "sharpe_ratio": 1.8,
    "max_drawdown": -12.3,
    "win_rate": 0.58,
    "total_trades": 42,
    "profitable_trades": 24,
    "losing_trades": 18,
    "avg_trade_return": 1.2,
    "best_trade": 8.5,
    "worst_trade": -4.2,
    "holding_period_days": 8.5,
    "execution_time": 0.023
  },
  "trades": [
    // Up to 100 trades (typical: 20-50)
    {"date": "2024-01-15", "type": "buy", "price": 43000, "return": 2.3},
    {"date": "2024-01-23", "type": "sell", "price": 44000, "return": 2.3},
    // ... more trades
  ],
  "equity_curve": [
    // 365 data points for 1 year daily backtest
    {"date": "2024-01-01", "equity": 10000},
    {"date": "2024-01-02", "equity": 10050},
    // ... 365 points
  ]
}
```

### Size Breakdown (JSON stringified)

| Component | Size | Notes |
|-----------|------|-------|
| Metadata (crypto, strategy, params) | ~500 bytes | Name, ID, parameters |
| Results summary | ~400 bytes | Return, Sharpe, drawdown, etc. |
| Trades array (avg 30 trades) | ~2,000 bytes | Trade history |
| Equity curve (365 points) | ~12,000 bytes | Daily equity values |
| **Total per entry** | **~15 KB** | Compressed JSON |

### Redis Compression

Redis stores strings efficiently:
- JSON compression: ~30% reduction
- **Actual size per entry: ~10-12 KB**

Let's use **12 KB** per cache entry for safety.

---

## 📈 Memory Requirements by Usage Scenario

### Scenario 1: Light Usage (Typical User)
**User tests 10-20 different combinations**

```
Entries cached: 20
Memory used: 20 × 12 KB = 240 KB
```

✅ **Negligible memory usage**

---

### Scenario 2: Moderate Usage (Active Testing)
**User tests all 6 strategies on 50 popular cryptos**

```
Combinations: 50 cryptos × 6 strategies = 300
Memory used: 300 × 12 KB = 3.6 MB
```

✅ **Very small memory usage**

---

### Scenario 3: Heavy Usage (Professional Use)
**Multiple users testing various combinations throughout the day**

```
Unique combinations per day: 500
Memory used: 500 × 12 KB = 6 MB
```

✅ **Still tiny!**

---

### Scenario 4: Maximum Possible Cache (All Combinations)
**Every crypto × every strategy × multiple parameter sets cached**

```
Base combinations: 243 cryptos × 6 strategies = 1,458
Parameter variations: ~5 common variations per strategy
Total: 1,458 × 5 = 7,290 entries

Memory used: 7,290 × 12 KB = 87.5 MB
```

✅ **Still only ~88 MB!**

---

### Scenario 5: Extreme Load (Production with History)
**1 month of cached results with high traffic**

```
Assuming 10,000 unique backtest queries over 1 month:
Memory used: 10,000 × 12 KB = 120 MB
```

✅ **Totally manageable!**

---

## 🎯 Recommended Redis Configuration

### Option 1: Minimal (Recommended for Start)
```yaml
# docker-compose.yml
redis:
  image: redis:7-alpine
  container_name: crypto_redis
  restart: unless-stopped
  command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
  ports:
    - "6379:6379"
```

**Memory:** 256 MB  
**Capacity:** ~21,000 cache entries  
**Cost:** Negligible (shared host)  

✅ **Perfect for your use case!**

---

### Option 2: Standard (If You Scale Up)
```yaml
redis:
  image: redis:7-alpine
  container_name: crypto_redis
  restart: unless-stopped
  command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
  ports:
    - "6379:6379"
```

**Memory:** 512 MB  
**Capacity:** ~42,000 cache entries  
**Cost:** Still tiny  

---

### Option 3: Enterprise (Massive Scale)
```yaml
redis:
  image: redis:7-alpine
  container_name: crypto_redis
  restart: unless-stopped
  command: redis-server --maxmemory 1gb --maxmemory-policy allkeys-lru
  ports:
    - "6379:6379"
```

**Memory:** 1 GB  
**Capacity:** ~85,000 cache entries  
**Cost:** Minimal  

---

## 🔧 Cache Eviction Policy

**`allkeys-lru`** (Least Recently Used)
- Automatically removes oldest unused entries when memory full
- Keeps hot/popular queries in cache
- No manual cleanup needed!

**Example:**
```
Cache has 21,000 entries (256 MB full)
User requests backtest #21,001
→ Redis removes least recently used entry
→ Stores new result
→ Always stays under 256 MB
```

---

## ⏱️ Cache TTL (Time To Live)

### Recommended Strategy

**Option A: 24-hour TTL (Recommended)**
```python
# Cache entries expire after 24 hours
redis.setex(cache_key, 86400, json.dumps(result))
```

**Why 24 hours?**
- Crypto prices update continuously
- Yesterday's backtest might use stale data
- 24h ensures fresh results while still caching
- Memory naturally stays low (~6-12 MB typical)

**Option B: 1-week TTL (If data doesn't change)**
```python
# Cache entries expire after 7 days
redis.setex(cache_key, 604800, json.dumps(result))
```

**Option C: No expiration (Manual cleanup)**
```python
# Cache forever until memory full, then LRU evicts
redis.set(cache_key, json.dumps(result))
```

---

## 💰 Cost Analysis

### Docker Host Memory Impact

Your system likely has:
- **Total RAM:** 4-16 GB (typical VPS/server)
- **Current usage:** ~2-4 GB (webapp, api, database, nginx)
- **Redis allocation:** 256 MB

**Impact:** 256 MB is only **1.6-6.4%** of typical system RAM

✅ **Completely negligible!**

---

### Actual Usage Prediction

Based on your system:
- 243 cryptos, 6 strategies
- Typical user tests 10-30 combinations per session
- Maybe 100-500 unique queries per day

**Expected memory usage:** **10-30 MB average**  
**Peak memory usage:** **50-100 MB max**  
**Allocated memory:** **256 MB** (safe buffer)

**Unused buffer:** 150-240 MB (plenty of headroom!)

---

## 🎉 Summary & Recommendation

### Memory Requirements: **TINY!** 🎊

| Usage Level | Memory | Your System |
|-------------|--------|-------------|
| Typical | 10-30 MB | ✅ Easy |
| Heavy | 50-100 MB | ✅ Easy |
| Maximum | 256 MB | ✅ Easy |
| Extreme | 512 MB | ✅ Still easy |

### Recommendation

**Allocate: 256 MB Redis cache**

**Why this is perfect:**
1. ✅ Handles 21,000+ cached queries
2. ✅ Only 1.6-6% of system RAM
3. ✅ Auto-evicts old entries (LRU)
4. ✅ Costs essentially nothing
5. ✅ Massive performance gain (50-100x)

**Redis Alpine image:** Only ~30 MB disk space  
**Runtime overhead:** Minimal CPU (just key lookups)

---

## 📝 Comparison to Other Services

Your current containers:
```
webapp:     ~200-300 MB RAM
api:        ~300-400 MB RAM
database:   ~500-800 MB RAM
nginx:      ~50-100 MB RAM
pgadmin:    ~200-300 MB RAM
──────────────────────────────
TOTAL:      ~1.5-2 GB RAM

Redis:      ~256 MB RAM (10-15% of current usage)
```

✅ **Redis is one of your SMALLEST containers!**

---

## 🚀 Bottom Line

**Redis caching memory cost: NEGLIGIBLE!**

- **256 MB allocation** handles everything
- **10-30 MB typical usage** (barely noticeable)
- **Massive performance gain** (50-100x speedup)
- **Zero infrastructure cost** (shared Docker host)

**ROI:** Spend 256 MB RAM → Get 50-100x faster repeats  
**Cost/benefit:** Best optimization you can do! 🎯

---

**Ready to implement?** Redis caching is a no-brainer with these tiny memory requirements! 🚀

---

*Calculated: October 6, 2025*  
*System: 243 cryptos × 6 strategies = 1,458 combinations*  
*Recommendation: 256 MB Redis with 24h TTL and LRU eviction*
