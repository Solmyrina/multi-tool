# Reference Documentation

Quick references, APIs, technical specifications, and troubleshooting for the cryptocurrency backtesting system.

## Available References

### 1. **OPTIMIZATION.md** 
**Performance optimization guide (30s → 0.1s)**

Complete optimization journey with:
- 8-phase optimization timeline
- Query optimization with indexes
- Date range filtering (3.1x improvement)
- Redis caching implementation
- NumPy vectorization
- Server-Sent Events streaming
- Performance benchmarks and troubleshooting

**When to use**: Understand performance improvements, implement caching, optimize slow queries

### 2. **QUICK_REFERENCE.md**
**Copy-paste examples and common commands**

Quick reference with:
- API endpoints and curl examples
- Database queries (data volume, latest prices, gaps)
- Docker commands (services, database, Redis, pgAdmin)
- Trading strategy implementations
- CLI operations and monitoring
- Performance benchmarks
- Python/JavaScript client libraries

**When to use**: Need quick syntax examples, API calls, or Docker commands

### 3. **TROUBLESHOOTING.md**
**Common issues and solutions**

Comprehensive troubleshooting for:
- Backtest errors (500, insufficient data, invalid interval)
- Login issues (rate limiting, credentials)
- Performance dashboard not loading
- Slow queries (14-17 seconds)
- Cache issues (stale data)
- Network connectivity
- API endpoint issues
- Docker issues
- Monitoring and debugging

**When to use**: Something isn't working and you need a quick fix

### 4. **GLOSSARY.md** *(Coming Soon)*
Technical terms and definitions

## When to Use Reference Documentation

**Use these guides when you need**:
- ✅ Quick syntax examples or common commands
- ✅ Performance optimization tips
- ✅ Solutions to specific problems
- ✅ API call examples
- ✅ Database query templates
- ✅ Docker command reference
- ✅ Technical term definitions

## Quick Links by Task

### "How do I...?"

| Task | Reference |
|------|-----------|
| Speed up backtests? | [OPTIMIZATION.md](OPTIMIZATION.md) |
| Find a database query? | [QUICK_REFERENCE.md](QUICK_REFERENCE.md#database-queries) |
| Call the API? | [QUICK_REFERENCE.md](QUICK_REFERENCE.md#api-endpoints) |
| Fix an error? | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| Run a Docker command? | [QUICK_REFERENCE.md](QUICK_REFERENCE.md#docker-commands) |
| Understand a term? | GLOSSARY.md (coming soon) |

## Performance Reference Quick Stats

| Metric | Value | Source |
|--------|-------|--------|
| First backtest result | 0.1s | Phase 8: SSE Streaming |
| All 48 backtest results | 3-5s | With Redis caching |
| Single query with cache | 50ms | Phase 3: Redis |
| Cryptocurrency filtering | 50ms | Phase 2 optimization |
| Database query | 50-100ms | With proper indexes |

## Related Documentation

- 📖 [Backtesting Guide](../guides/BACKTESTING.md) - How to run backtests
- 📖 [Database Guide](../guides/DATABASE.md) - Database access
- 📖 [System Architecture](../architecture/ARCHITECTURE.md) - System design
- 🛠️ [Setup Guides](../setup/README.md) - Deployment guides
