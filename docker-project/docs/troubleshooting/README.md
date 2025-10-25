# Troubleshooting & Bug Fixes

Problems, solutions, and known issues with the cryptocurrency backtesting system.

## Available Resources

### 1. **TROUBLESHOOTING.md** ⭐ *Main Resource*
**Comprehensive troubleshooting guide**

Complete troubleshooting resource covering:
- **Quick troubleshooting matrix** - Issue → error → cause → solution
- **Backtest errors** (500 errors, insufficient data, invalid intervals)
- **Login issues** (rate limiting, credentials, account status)
- **Performance dashboard** (loading failures, missing data)
- **Slow queries** (14+ second database queries, optimization)
- **Cache issues** (stale data, invalidation)
- **Network & connectivity** (database, Redis connections)
- **API endpoint issues** (404, route registration)
- **Docker issues** (container problems, daemon errors)
- **Monitoring & debugging** (logs, resources, diagnostics)
- **Advanced troubleshooting** (debug logging, query analysis)

**When to use**: Something isn't working - start here!

### 2. **BUGFIXES.md** *(Consolidated Fixes)*
**Detailed bug fixes and solutions**

- Backtest request model mismatch (fixed)
- Circuit breaker termination (fixed)
- MudPopover provider location issues (fixed)
- Static input field problems (fixed)
- JSON strategy parsing errors (fixed)
- Strategy parameter field issues (fixed)

**When to use**: Need to understand what was fixed and why

### 3. **KNOWN_ISSUES.md** *(Coming Soon)*
**Known issues and workarounds**

- 4h and 1d intervals - feature ready, no data yet
- Performance dashboard takes 2-3s to load
- SSE stream timeout on very large datasets
- Redis memory management on long-running backtests

**When to use**: Want to know what's not working yet

## Quick Issue Reference

### Common Issues by Symptom

| Symptom | Issue | Solution |
|---------|-------|----------|
| Backtest returns 500 error | API model mismatch | [See Backtest Errors](TROUBLESHOOTING.md#backtest-errors) |
| "Crypto 0" in logs | CryptocurrencyId not mapped | Add [JsonPropertyName] |
| Can't login after 5 tries | Old rate limit | Increase to 20 or wait 15min |
| Dashboard shows no data | Route not registered | Restart webapp, check app.py line order |
| Queries take 14+ seconds | Inefficient EXISTS query | Use denormalized has_price_data flag |
| Cache showing old data | Cache not invalidating | Clear Redis cache with FLUSHDB |
| 404 on API endpoint | Route defined after main block | Move before if __name__ == '__main__': |

### By Component

**Backend (Dotnet API)**:
- [Backtest errors](TROUBLESHOOTING.md#backtest-errors)
- [500 internal server errors](TROUBLESHOOTING.md#error-500-internal-server-error)
- [Insufficient data errors](TROUBLESHOOTING.md#error-insufficient-price-data-0-data-points)

**Frontend (Blazor UI)**:
- [Login issues](TROUBLESHOOTING.md#login-issues)
- [Form validation](BUGFIXES.md#static-input-fields)
- [JSON deserialization](BUGFIXES.md#json-strategy-parsing)

**Database (PostgreSQL)**:
- [Slow queries](TROUBLESHOOTING.md#slow-queries)
- [Connection issues](TROUBLESHOOTING.md#error-cannot-connect-to-database)
- [Missing indexes](TROUBLESHOOTING.md#issue-database-queries-getting-slower-over-time)

**Cache (Redis)**:
- [Cache issues](TROUBLESHOOTING.md#cache-issues)
- [Connection problems](TROUBLESHOOTING.md#error-cannot-connect-to-redis)

**Infrastructure (Docker)**:
- [Container issues](TROUBLESHOOTING.md#error-no-such-container)
- [Network problems](TROUBLESHOOTING.md#error-cannot-connect-to-database)

## Troubleshooting Workflow

### Step 1: Identify the Problem
1. What's the **error message**?
2. **Where** does it appear (UI, API logs, database)?
3. **When** does it happen (on startup, during backtest, after deploy)?

### Step 2: Find the Solution
1. Search [Quick Issue Reference](#quick-issue-reference) table above
2. Or browse the [main Troubleshooting guide](TROUBLESHOOTING.md)
3. If recent bug, check [BUGFIXES.md](BUGFIXES.md)

### Step 3: Apply the Fix
1. Follow the solution steps
2. Verify with provided test commands
3. Check logs to confirm fix

### Step 4: Prevent Recurrence
1. Update relevant code if applicable
2. Add monitoring/alerting if needed
3. Document if it's a new issue

## Quick Diagnostic Commands

### Check System Health

```bash
# All containers running?
docker compose ps

# All services healthy?
docker compose logs --tail 5 | grep -i error

# Database responsive?
docker exec docker-project-database psql -U root -d webapp_db -c "SELECT 1;"

# Redis responsive?
docker exec docker-project-redis redis-cli ping

# API responding?
curl http://localhost:8000/health

# UI accessible?
curl http://localhost/
```

### Gather Diagnostics

```bash
# Last 100 errors
docker compose logs --tail 500 2>&1 | grep -i error > errors.txt

# Database performance metrics
docker exec docker-project-database psql -U root -d webapp_db -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY total_time DESC LIMIT 10;" > queries.txt

# Container resource usage
docker stats --no-stream > resources.txt
```

## When to Escalate

Contact the development team if:

- ❌ Issue persists after following troubleshooting steps
- ❌ Error message doesn't match any in guide
- ❌ Multiple services failing simultaneously
- ❌ Data corruption suspected
- ❌ Unable to gather diagnostics
- ❌ Need expert analysis

**Provide**: [Diagnostic output](#gather-diagnostics) from commands above

## Recent Fixes (October 2025)

✅ **Backtest Model Mapping** - Fixed CryptocurrencyId serialization  
✅ **Login Rate Limiting** - Increased from 5 to 20 attempts  
✅ **Performance Dashboard** - Fixed route registration  
✅ **Cryptocurrency Filtering** - 14s → 50ms with denormalized flag  
✅ **SSE Streaming** - Real-time progressive loading works  

## Related Documentation

- 📖 [Backtesting Guide](../guides/BACKTESTING.md) - How to run backtests
- 📖 [System Architecture](../architecture/ARCHITECTURE.md) - System design
- 📖 [Performance Optimization](../reference/OPTIMIZATION.md) - Speed improvements
- 📖 [Quick Reference](../reference/QUICK_REFERENCE.md) - Commands & examples

## Status

**Last Updated**: October 25, 2025  
**Known Issues**: 3 (4h/1d data, performance dashboard load time, SSE timeout)  
**Fixes Deployed**: 8 major fixes  
**Test Coverage**: 45+ test scenarios documented

---

**Need help?** Start with the [Troubleshooting guide](TROUBLESHOOTING.md) or check the [Quick Issue Reference](#quick-issue-reference) table above.
