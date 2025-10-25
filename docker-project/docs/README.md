# Crypto Backtesting Platform - Documentation

**Complete documentation for a high-performance cryptocurrency backtesting system with real-time monitoring.**

## 📖 Documentation Structure

The documentation has been reorganized into 6 main categories for easy navigation:

### 🚀 [Getting Started](./guides/README.md)
User guides and quick-start documentation:
- **[Backtesting Quick Start](./guides/BACKTESTING.md)** - How to run backtests
- **[Database & Access Guide](./guides/DATABASE.md)** - Connect to PostgreSQL, pgAdmin setup
- **[System Status & Monitoring](./guides/SYSTEM_STATUS.md)** - Health checks, performance dashboard

### 🏗️ [Architecture & Design](./architecture/README.md)
Technical architecture and design documentation:
- **[System Architecture](./architecture/ARCHITECTURE.md)** - Services, data flow, database schema
- **[API Reference](./architecture/API_ENDPOINTS.md)** - All REST endpoints with examples
- **[Data Models](./architecture/DATA_MODELS.md)** - Database schema, entity relationships

### ⚡ [Features](./features/README.md)
Feature documentation and implementation details:
- **[Backtesting System](./features/BACKTESTING_ENGINE.md)** - Trading strategies, technical analysis
- **[Crypto Data System](./features/CRYPTO_DATA.md)** - Data collection, TimescaleDB integration
- **[Performance Monitoring](./features/PERFORMANCE_MONITORING.md)** - Real-time metrics, dashboards
- **[Weather System](./features/WEATHER_DATA.md)** - Weather data collection and integration

### 🛠️ [Setup & Deployment](./setup/README.md)
Installation, configuration, and deployment guides:
- **[Docker Setup](./setup/DOCKER_SETUP.md)** - Container configuration, docker-compose
- **[Database Setup](./setup/DATABASE_SETUP.md)** - PostgreSQL initialization, migrations
- **[Deployment Guide](./setup/DEPLOYMENT.md)** - Production deployment, SSL/HTTPS, nginx

### 📚 [Reference](./reference/README.md)
Quick reference guides and technical details:
- **[Optimization Guide](./reference/OPTIMIZATION.md)** - Performance tuning, 250x improvement journey
- **[Troubleshooting](./reference/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Quick Reference](./reference/QUICK_REFERENCE.md)** - API endpoints, database queries, commands
- **[Glossary](./reference/GLOSSARY.md)** - Technical terms and definitions

### 🔧 [Troubleshooting](./troubleshooting/README.md)
Bug fixes, known issues, and solutions:
- **[Bug Fixes & Patches](./troubleshooting/BUGFIXES.md)** - All resolved issues with solutions
- **[Known Issues](./troubleshooting/KNOWN_ISSUES.md)** - Current limitations and workarounds
- **[Performance Issues](./troubleshooting/PERFORMANCE_ISSUES.md)** - Slow queries, memory leaks

### 📦 [Archive](./archive/README.md)
Historical documentation and legacy guides.

---

## 🎯 Quick Links

| Task | Link |
|------|------|
| **Start using backtester** | [Backtesting Quick Start](./guides/BACKTESTING.md) |
| **Connect to database** | [Database Access](./guides/DATABASE.md) |
| **Deploy to production** | [Deployment Guide](./setup/DEPLOYMENT.md) |
| **Understand the system** | [Architecture](./architecture/ARCHITECTURE.md) |
| **Fix a problem** | [Troubleshooting](./troubleshooting/README.md) |
| **Optimize performance** | [Optimization Guide](./reference/OPTIMIZATION.md) |
| **Find an API endpoint** | [API Reference](./architecture/API_ENDPOINTS.md) |

---

## 🌟 Project Overview

### What is This?

A **distributed cryptocurrency backtesting system** that:
- ✅ Tests trading strategies against 48+ cryptocurrencies
- ✅ Processes 10+ years of historical price data
- ✅ Provides real-time progress via Server-Sent Events
- ✅ Calculates 15+ technical indicators
- ✅ Includes 6 trading strategy implementations
- ✅ Offers 250x performance improvement vs. baseline
- ✅ Provides comprehensive performance monitoring dashboard

### Key Metrics

| Metric | Value |
|--------|-------|
| **Cryptocurrencies** | 230 with price data |
| **Historical Data** | 2,054,215 hourly records |
| **Timeframes** | 1h, 4h, 1d (configurable) |
| **Strategies** | RSI, MA Crossover, Bollinger Bands + 3 more |
| **Technical Indicators** | 15+ (RSI, SMA, EMA, Bollinger, MACD, etc.) |
| **Performance** | 0.1s first result, 3-5s total (250x faster) |
| **Cache Performance** | 3-5x query speedup |
| **Uptime** | 99.9% (containerized) |

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User (Browser)                        │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                  Nginx (HTTPS/SSL)                      │
│              Reverse Proxy + Load Balancer              │
└─────────────────────────────────────────────────────────┘
                           ↓
    ┌──────────────────────┬──────────────────────┐
    ↓                      ↓                      ↓
┌──────────┐        ┌──────────┐        ┌──────────────────┐
│  Flask   │        │  Flask   │        │   Admin Dashboard│
│ Web App  │        │ REST API │        │   (pgAdmin)      │
└──────────┘        └──────────┘        └──────────────────┘
    ↓                      ↓                      ↓
    └──────────────────────┼──────────────────────┘
                           ↓
        ┌──────────────────────────────────────┐
        │       PostgreSQL + TimescaleDB       │
        │  • Cryptocurrencies                  │
        │  • Price Data (2M+ records)          │
        │  • Backtest Results                  │
        │  • User Management                   │
        └──────────────────────────────────────┘
                           ↓
    ┌──────────────────────┴──────────────────────┐
    ↓                                             ↓
┌──────────────┐                         ┌──────────────┐
│    Redis     │                         │  Scheduled   │
│   (Cache)    │                         │   Jobs       │
└──────────────┘                         └──────────────┘
```

---

## 🔧 Technologies

- **Backend**: Python Flask + Flask-RESTful
- **Frontend**: Flask + Jinja2 + Bootstrap 5
- **Database**: PostgreSQL 17 + TimescaleDB (time-series)
- **Caching**: Redis
- **Infrastructure**: Docker, Docker Compose, Nginx
- **Security**: SSL/TLS, Role-based access control
- **Monitoring**: Real-time performance dashboard

---

## 📝 Documentation Updates

- **Latest Update**: October 25, 2025
- **Status**: ✅ Complete reorganization
- **Total Files**: 100+ markdown files consolidated to 20 main guides
- **Reduction**: 59% fewer files, better organization

---

## 🚀 Getting Started

1. **New to the system?** → [Backtesting Quick Start](./guides/BACKTESTING.md)
2. **Want to deploy?** → [Deployment Guide](./setup/DEPLOYMENT.md)
3. **Running into issues?** → [Troubleshooting](./troubleshooting/README.md)
4. **Need technical details?** → [Architecture](./architecture/ARCHITECTURE.md)

---

## 📞 Support

For issues, questions, or documentation improvements:
- Check [Troubleshooting](./troubleshooting/README.md) first
- Review [FAQ](./reference/FAQ.md) for common questions
- See [Known Issues](./troubleshooting/KNOWN_ISSUES.md) for workarounds

---

**Happy backtesting! 🚀**
