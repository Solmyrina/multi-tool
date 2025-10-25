# .NET 10 Crypto Backtester - Documentation Index

## 📚 Documentation Overview

Welcome to the .NET 10 Crypto Backtester documentation. This project adds high-performance .NET containers alongside the existing Python stack.

---

## 📖 Documentation Structure

### **Getting Started**
1. [**README.md**](./README.md) - Project overview and quick start
2. [**ARCHITECTURE.md**](./ARCHITECTURE.md) - System architecture and design
3. [**SETUP.md**](./SETUP.md) - Installation and configuration guide

### **Development**
4. [**API_REFERENCE.md**](./API_REFERENCE.md) - REST API endpoint documentation
5. [**BLAZOR_COMPONENTS.md**](./BLAZOR_COMPONENTS.md) - Blazor component guide
6. [**DATABASE_SCHEMA.md**](./DATABASE_SCHEMA.md) - Database tables and queries
7. [**DEVELOPMENT_GUIDE.md**](./DEVELOPMENT_GUIDE.md) - Developer workflow

### **Implementation**
8. [**STRATEGIES.md**](./STRATEGIES.md) - Trading strategies implementation
9. [**PERFORMANCE.md**](./PERFORMANCE.md) - Performance tuning and benchmarks
10. [**INTEGRATION_TEST_FINAL_SUMMARY.md**](./INTEGRATION_TEST_FINAL_SUMMARY.md) - ✅ Integration test results (30/30 passing)
11. [**API_FIXES_SUMMARY.md**](./API_FIXES_SUMMARY.md) - ✅ API issues resolved (Oct 9, 2025)

### **Operations**
11. [**DEPLOYMENT.md**](./DEPLOYMENT.md) - Deployment procedures
12. [**MONITORING.md**](./MONITORING.md) - Monitoring and logging
13. [**TROUBLESHOOTING.md**](./TROUBLESHOOTING.md) - Common issues and solutions

### **Reference**
14. [**COMPARISON.md**](./COMPARISON.md) - .NET vs Python comparison
15. [**FAQ.md**](./FAQ.md) - Frequently asked questions
16. [**GLOSSARY.md**](./GLOSSARY.md) - Terms and definitions

---

## 🚀 Quick Links

### **For Developers**
- [Setup Development Environment](./SETUP.md#development-environment)
- [Run Locally](./SETUP.md#local-development)
- [API Documentation](./API_REFERENCE.md)
- [Component Guide](./BLAZOR_COMPONENTS.md)
- [Integration Tests](./INTEGRATION_TEST_FINAL_SUMMARY.md) - ✅ 100% passing

### **For Operations**
- [Deploy to Production](./DEPLOYMENT.md)
- [Configure Monitoring](./MONITORING.md)
- [Troubleshoot Issues](./TROUBLESHOOTING.md)

### **For Users**
- [How to Use](./README.md#features)
- [Strategy Guide](./STRATEGIES.md)
- [Performance Tips](./PERFORMANCE.md#best-practices)

---

## 📊 Project Status

**Current Version:** 1.0.0  
**Status:** ✅ **Phase 3 Complete - Production Ready**  
**Last Updated:** October 9, 2025

### Completed Phases:
- ✅ **Phase 1:** ASP.NET Core Data API with 14 endpoints
- ✅ **Phase 2:** Unit Tests (37/37 passing - 100%)
- ✅ **Phase 3:** Blazor Server UI with 5 interactive pages
- ✅ **Integration Tests:** 29/29 passing (100%)

### Test Coverage:
- **Unit Tests:** 37/37 ✅ (100%) - Strategies, indicators, calculations
- **Integration Tests:** 30/30 ✅ (100%) - Full API validation
- **Total:** 67/67 tests passing (100%)

[📊 View Integration Test Results](./INTEGRATION_TEST_FINAL_SUMMARY.md)

### Recent Improvements:
- ✅ **October 9, 2025:** Fixed all 3 API issues (stats endpoint, sorting, HTTP status codes)
- ✅ Added new test for return percentage sorting
- ✅ All endpoints now fully REST-compliant

---

## 🎯 What's Included

### **Three Containers** (All Production Ready ✅)

**1. dotnet-data-api (Port 5002)**
- ASP.NET Core Minimal API
- 14 REST endpoints fully tested
- Backtest execution engine
- Technical indicator calculations
- 100% integration test coverage

**2. blazor-ui (Port 5003)**
- Blazor Server 9.0 with MudBlazor
- 5 interactive pages
- Real-time data updates
- Dashboard, strategies, backtests
- Material Design components

**3. dotnet-web (Port 5001)** [Legacy]
- Original Blazor implementation
- Being replaced by blazor-ui

### **Features**
- ✅ 6 trading strategies (RSI, MA Crossover, Bollinger Bands, MACD, Mean Reversion, Breakout)
- ✅ Real-time backtesting with 100+ cryptocurrencies
- ✅ Technical indicators (RSI, SMA, EMA, Bollinger Bands)
- ✅ Interactive Blazor UI with MudBlazor components
- ✅ Full test coverage (66/66 tests passing)
- ✅ REST API with 14 endpoints
- ✅ PostgreSQL + TimescaleDB integration

### **Technology Stack**
- .NET 9.0 (Current)
- Blazor Server 9.0
- ASP.NET Core Minimal APIs
- Npgsql 9.0 + Dapper 2.1
- MudBlazor 8.13.0
- xUnit 2.9 + FluentAssertions 8.7
- PostgreSQL 17 + TimescaleDB 2.22

---

## 📈 Performance Goals

| Metric | Python | .NET 10 | Target |
|--------|--------|---------|--------|
| API Response | 15-30ms | 3-8ms | **5x faster** |
| Backtest (1yr) | 500-1000ms | 80-200ms | **6x faster** |
| Memory Usage | 300-500MB | 80-150MB | **4x less** |
| Throughput | 1,000 req/s | 10,000 req/s | **10x more** |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Nginx Reverse Proxy (HTTPS)                            │
│    /crypto-backtest/* → blazor-ui (5003)                │
│    /api/*             → dotnet-data-api (5002)          │
└─────────────────────────────────────────────────────────┘
         │
         ├─> blazor-ui (Blazor Server 9.0) ✅
         │   ├─> Dashboard with statistics
         │   ├─> Cryptocurrency browser
         │   ├─> Strategy catalog
         │   ├─> Backtest creation form
         │   └─> Results table with pagination
         │
         ├─> dotnet-data-api (ASP.NET Core 9.0) ✅
         │   ├─> 14 REST endpoints (100% tested)
         │   ├─> Backtest execution engine
         │   ├─> 6 trading strategies
         │   ├─> Technical indicators (RSI, SMA, EMA, BB)
         │   └─> Dapper + Npgsql data access
         │
         └─> PostgreSQL 17 + TimescaleDB 2.22 (Shared)
             ├─> crypto_prices (hourly data)
             ├─> crypto_backtest_results
             ├─> crypto_strategies
             └─> cryptocurrencies (100+)
```

---

## 📦 Installation

Quick start:

```bash
# Clone repository
cd /home/one_control/docker-project

# Create .NET projects
./scripts/create-dotnet-projects.sh

# Build containers
docker-compose build dotnet-data-api dotnet-web

# Start services
docker-compose up -d dotnet-data-api dotnet-web

# Access application
open https://localhost/dotnet/
```

See [SETUP.md](./SETUP.md) for detailed instructions.

---

## 🎓 Learning Resources

### **For .NET Beginners**
- [.NET 10 Documentation](https://docs.microsoft.com/en-us/dotnet/)
- [Blazor Tutorial](https://docs.microsoft.com/en-us/aspnet/core/blazor/)
- [C# Guide](https://docs.microsoft.com/en-us/dotnet/csharp/)

### **For Python Developers**
- [Python to C# Guide](./COMPARISON.md#language-comparison)
- [Architecture Differences](./ARCHITECTURE.md#vs-python)
- [Performance Analysis](./PERFORMANCE.md#benchmarks)

### **API Development**
- [Minimal APIs Guide](https://docs.microsoft.com/en-us/aspnet/core/fundamentals/minimal-apis)
- [Dapper Documentation](https://github.com/DapperLib/Dapper)
- [Npgsql Guide](https://www.npgsql.org/doc/)

---

## 🤝 Contributing

This project is part of a hybrid Python/.NET architecture. When contributing:

1. Follow C# coding standards
2. Maintain feature parity with Python version
3. Write unit tests
4. Update documentation
5. Benchmark performance

See [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md) for details.

---

## 📞 Support

### **Issues**
- Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- Review [FAQ.md](./FAQ.md)
- Check logs: `docker logs dotnet-data-api`

### **Questions**
- Architecture questions → See [ARCHITECTURE.md](./ARCHITECTURE.md)
- API questions → See [API_REFERENCE.md](./API_REFERENCE.md)
- Development questions → See [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md)

---

## 📋 Implementation Status

### **Phase 1: Core API** ✅ COMPLETE
- [x] ASP.NET Core Minimal API
- [x] 14 REST endpoints
- [x] Backtest execution engine
- [x] 6 trading strategies
- [x] Technical indicators
- [x] Unit tests (37/37 passing)

### **Phase 2: Testing** ✅ COMPLETE
- [x] Unit test suite
- [x] Integration test suite (29/29 passing)
- [x] CustomWebApplicationFactory
- [x] Test documentation
- [x] 100% test coverage achieved

### **Phase 3: Blazor UI** ✅ COMPLETE
- [x] Blazor Server 9.0 application
- [x] MudBlazor component library
- [x] 5 interactive pages
- [x] Dashboard with statistics
- [x] Backtest creation and management
- [x] Docker deployment
- [x] Health checks and monitoring

### **Phase 4: Documentation** � IN PROGRESS
- [x] Integration test results
- [x] Project status documentation
- [x] Quick reference guide
- [ ] API reference (swagger available)
- [ ] Deployment guide
- [ ] Performance benchmarks

---

## 🔄 Recent Updates

**Latest Changes:**
- 2025-10-09: ✅ **API Issues Fixed** - All 3 documented issues resolved (67/67 tests passing)
- 2025-10-09: ✅ **Phase 3 Complete** - Blazor UI deployed and tested
- 2025-10-09: ✅ **All Integration Tests Passing** - 30/30 (100%)
- 2025-10-09: ✅ Fixed stats endpoint SQL query
- 2025-10-09: ✅ Fixed return percentage sorting
- 2025-10-09: ✅ POST /backtest now returns 201 Created
- 2025-10-09: ✅ Added new sorting validation test
- 2025-10-09: ✅ Comprehensive test documentation created
- 2025-10-09: Blazor Server UI with 5 pages deployed
- 2025-10-09: Integration test suite implemented
- 2025-10-09: Unit test suite completed (37/37 passing)

---

## 📄 License

This project is part of the Docker Crypto Finance project.

---

## 🚀 Quick Start

### For Users
1. **Access Blazor UI**: https://your-domain/crypto-backtest/
2. Browse cryptocurrencies and strategies
3. Create and run backtests
4. View results and statistics

### For Developers
1. **View Test Results**: [Integration Tests](./INTEGRATION_TEST_FINAL_SUMMARY.md)
2. **Run Tests**: 
   ```bash
   cd /home/one_control/docker-project/dotnet-data-api-tests
   dotnet test
   ```
3. **API Endpoints**: http://localhost:5002/swagger
4. **Blazor UI**: http://localhost:5003

### For Operations
1. **Check Status**: `docker ps | grep dotnet`
2. **View Logs**: `docker logs blazor-ui` or `docker logs dotnet-data-api`
3. **Health Check**: `curl http://localhost:5003/health`

---

**Ready to get started?** Begin with the [README](./README.md)!

---

**Documentation Version:** 1.0  
**Last Updated:** October 9, 2025  
**Maintained By:** Development Team
