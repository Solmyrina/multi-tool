# Crypto Backtest Platform - Quick Reference

## 🚀 Phase 3 Complete!

Blazor UI successfully deployed with full backtest management interface.

## Quick Access

### Web Interfaces
```
Main Dashboard:     https://your-domain/crypto-backtest/
API Documentation:  https://your-domain/dotnet-api/swagger
Main Flask App:     https://your-domain/
Database Admin:     https://your-domain/pgadmin/
```

### Direct Container Access
```
Blazor UI:          http://localhost:5003
.NET Data API:      http://localhost:5002
```

## Container Management

### View Status
```bash
docker ps | grep -E "blazor-ui|dotnet-data-api"
```

### View Logs
```bash
# Blazor UI
docker logs blazor-ui -f

# Data API
docker logs dotnet-data-api -f
```

### Restart Services
```bash
# Restart Blazor UI
docker compose restart blazor-ui

# Restart Data API
docker compose restart dotnet-data-api

# Restart nginx
docker compose restart nginx
```

### Rebuild from Source
```bash
# Rebuild Blazor UI
cd /home/one_control/docker-project
docker compose build blazor-ui
docker compose up -d blazor-ui

# Rebuild Data API
docker compose build dotnet-data-api
docker compose up -d dotnet-data-api
```

## Testing

### Run Unit Tests
```bash
cd /home/one_control/docker-project/dotnet-data-api-tests
/home/one_control/.dotnet/dotnet test --logger "console;verbosity=minimal"
```

### Test API Endpoints
```bash
# Health check
curl http://localhost:5002/health

# List cryptocurrencies
curl http://localhost:5002/cryptocurrencies

# List strategies
curl http://localhost:5002/strategies
```

## Features Available

### 📊 Dashboard (`/`)
- Total backtest statistics
- Average return & Sharpe ratio
- Best/worst backtest highlights
- Recent backtests table

### 💰 Cryptocurrencies (`/cryptocurrencies`)
- Browse available crypto assets
- Search by symbol or name
- View data coverage
- Quick backtest execution

### 🧠 Strategies (`/strategies`)
- RSI (Relative Strength Index)
- MA Crossover (Moving Average Crossover)
- Bollinger Bands
- View default parameters

### ⚡ New Backtest (`/backtest/new`)
- Select cryptocurrency
- Choose strategy
- Configure parameters dynamically
- Set date range and initial capital
- Execute backtest

### 📈 Backtest List (`/backtest`)
- Server-side pagination
- Sort by multiple columns
- Filter by crypto/strategy/dates
- View detailed results
- Delete backtests

## API Endpoints Summary

### Cryptocurrencies
- `GET /cryptocurrencies` - List all
- `GET /cryptocurrencies/{id}` - Get details
- `GET /cryptocurrencies/{id}/prices` - Historical prices

### Strategies
- `GET /strategies` - List all strategies
- `GET /strategies/{id}` - Get strategy details

### Backtests
- `POST /backtest` - Create new backtest
- `GET /backtest` - List with pagination/filters
- `GET /backtest/{id}` - Get detailed results
- `DELETE /backtest/{id}` - Delete backtest
- `GET /backtest/stats` - Aggregate statistics
- `POST /backtest/compare` - Compare multiple backtests

### Indicators
- `GET /indicators` - Calculate technical indicators

Full API documentation: https://your-domain/dotnet-api/swagger

## Testing

## Testing

**Status:**
- Unit Tests: 37/37 ✅ (100%)
- Integration Tests: 30/30 ✅ (100%)
- Total: 67/67 tests passing
- API Issues: All resolved ✅

**Run Tests:**

### Test Coverage
- Cryptocurrency endpoints (7 tests)
- Strategy endpoints (5 tests)
- Indicator endpoints (8 tests)
- Backtest endpoints (9 tests)

See: [INTEGRATION_TEST_FINAL_SUMMARY.md](./INTEGRATION_TEST_FINAL_SUMMARY.md)

## Architecture

```
User Browser
     ↓
Nginx (HTTPS)
     ↓
Blazor UI (5003)
     ↓
.NET Data API (5002)
     ↓
PostgreSQL + TimescaleDB
```

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Frontend | Blazor Server | .NET 9.0 |
| UI Framework | MudBlazor | 8.13.0 |
| Backend API | ASP.NET Core | 9.0 |
| Database | PostgreSQL | 17 |
| Time-series | TimescaleDB | 2.22.1 |
| Cache | Redis | 7-alpine |
| Proxy | Nginx | alpine |

## File Locations

### Source Code
```
/home/one_control/docker-project/blazor-ui/           # Blazor UI
/home/one_control/docker-project/dotnet-data-api/     # Data API
/home/one_control/docker-project/dotnet-data-api-tests/ # Tests
```

### Documentation
```
/home/one_control/docker-project/docs/dotnet/
├── INDEX.md                              # Documentation index
├── DEPLOYMENT_GUIDE.md                   # Setup instructions
├── API_ENDPOINTS.md                      # API reference (14 endpoints)
├── INTEGRATION_TEST_FINAL_SUMMARY.md     # ✅ Integration tests (29/29 passing)
├── PHASE3_BLAZOR_UI.md                   # Blazor UI documentation
├── PROJECT_STATUS.md                     # Overall project status
└── QUICK_REFERENCE.md                    # This file
```

### Configuration
```
/home/one_control/docker-project/docker-compose.yml   # Services
/home/one_control/docker-project/nginx/nginx.conf     # Routing
/home/one_control/docker-project/blazor-ui/appsettings.json
/home/one_control/docker-project/dotnet-data-api/appsettings.json
```

## Common Tasks

### Add New Blazor Page
1. Create `.razor` file in `blazor-ui/Components/Pages/`
2. Add `@page` directive with route
3. Add `@rendermode InteractiveServer`
4. Inject `CryptoBacktestApiService` if needed
5. Rebuild and restart: `docker compose build blazor-ui && docker compose up -d blazor-ui`

### Add New API Endpoint
1. Add method to `dotnet-data-api/Program.cs`
2. Add repository method if needed
3. Update Swagger documentation
4. Add corresponding method in `CryptoBacktestApiService.cs`
5. Rebuild: `docker compose build dotnet-data-api && docker compose up -d dotnet-data-api`

### Add New Test
1. Create test file in `dotnet-data-api-tests/`
2. Follow naming convention: `{Component}Tests.cs`
3. Use xUnit, FluentAssertions, Moq
4. Run: `/home/one_control/.dotnet/dotnet test`

## Troubleshooting

### Blazor UI Won't Start
```bash
# Check logs
docker logs blazor-ui

# Verify API is accessible
docker exec blazor-ui curl http://dotnet-data-api:5002/health

# Rebuild
docker compose build --no-cache blazor-ui
docker compose up -d blazor-ui
```

### API Returns 500 Error
```bash
# Check logs
docker logs dotnet-data-api

# Verify database connection
docker exec dotnet-data-api curl http://database:5432

# Check database is healthy
docker ps | grep database
```

### Cannot Access via Browser
```bash
# Check nginx
docker logs docker-project-nginx

# Verify routing
docker exec docker-project-nginx cat /etc/nginx/conf.d/default.conf | grep blazor-ui

# Restart nginx
docker compose restart nginx
```

## Performance Tips

1. **Enable Redis Caching**: Already configured
2. **Use Server-side Pagination**: Implemented in backtest list
3. **Optimize Database Queries**: Use indexes on date/crypto columns
4. **Connection Pooling**: Configured (5-100 connections)
5. **Asset Bundling**: MudBlazor handles this

## Security Checklist

- ✅ HTTPS enforced
- ✅ CORS configured
- ✅ XSS protection
- ✅ CSRF tokens
- ✅ SQL injection prevention (parameterized queries)
- ✅ Input validation
- ✅ Container isolation
- ✅ Database passwords
- ⚠️ User authentication (not yet implemented)

## Next Steps

### High Priority
1. Add backtest detail page with trade history
2. Implement chart visualizations (equity curves)
3. Build comparison page for multiple backtests
4. Add SignalR for real-time updates

### Medium Priority
1. User authentication (ASP.NET Identity)
2. Export functionality (CSV, Excel)
3. Custom strategy builder
4. Performance benchmarks

### Low Priority
1. Dark mode toggle in UI
2. Email notifications
3. Mobile app version
4. Multi-language support

## Support

### Documentation
- Documentation index: `docs/dotnet/INDEX.md`
- Full setup: `docs/dotnet/DEPLOYMENT_GUIDE.md`
- API reference: `docs/dotnet/API_ENDPOINTS.md`
- Integration tests: `docs/dotnet/INTEGRATION_TEST_FINAL_SUMMARY.md` ✅ 29/29 passing
- UI guide: `docs/dotnet/PHASE3_BLAZOR_UI.md`
- Status: `docs/dotnet/PROJECT_STATUS.md`

### Useful Commands
```bash
# View all containers
docker ps

# View all services
docker compose ps

# View container resource usage
docker stats

# Clean up stopped containers
docker container prune

# Clean up unused images
docker image prune

# Full system cleanup (careful!)
docker system prune -a
```

## Success Indicators

- ✅ Blazor UI accessible at `/crypto-backtest/`
- ✅ API Swagger docs at `/dotnet-api/swagger`
- ✅ All containers healthy
- ✅ 37 unit tests passing
- ✅ Can create backtests via UI
- ✅ Can view results in dashboard
- ✅ Responsive design works on mobile

## Project Status

**Phase 1**: ✅ Complete (Infrastructure)  
**Phase 2**: ✅ Complete (Backend API)  
**Phase 3**: ✅ Complete (Blazor UI)  
**Phase 4**: 🔜 Planned (Charts & Advanced Features)

---

**Last Updated**: October 9, 2025  
**Version**: 1.0.0  
**Status**: ✅ Production Ready (Phases 1-3)
