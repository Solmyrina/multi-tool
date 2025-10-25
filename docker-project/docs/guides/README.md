# Getting Started Guides

Quick-start documentation for common tasks.

## 📖 Available Guides

- **[BACKTESTING.md](./BACKTESTING.md)** - How to run backtests, strategies, and interpret results
- **[DATABASE.md](./DATABASE.md)** - Database access, pgAdmin setup, connection strings
- **[SYSTEM_STATUS.md](./SYSTEM_STATUS.md)** - Health monitoring, performance dashboard, system status

## 🎯 Quick Start Paths

### I want to run a backtest
1. Use the Flask API endpoint: `/api/crypto/backtest/stream`
2. See [BACKTESTING.md](./BACKTESTING.md) for API usage
3. Use [QUICK_REFERENCE.md](../reference/QUICK_REFERENCE.md) for code examples

### I want to access the database
1. Use pgAdmin (https://localhost/pgadmin/) or SSH tunnel
2. [Read the Database Guide](./DATABASE.md)

### I want to check if things are working
1. Open the Performance Dashboard (https://localhost/performance)
2. Check API health: `curl https://localhost/api/health`
3. [Check the System Status Guide](./SYSTEM_STATUS.md)

---

## 📊 System Status

- **Status**: ✅ All services operational
- **Database**: PostgreSQL 17 + TimescaleDB
- **API**: Flask REST API (Python)
- **Frontend**: Flask Web App (Python)
- **Cache**: Redis 7 operational
