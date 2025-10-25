# Phase 3: Blazor UI - Crypto Backtest Platform

## Overview
Phase 3 delivers a modern, interactive web UI for the Crypto Backtest Platform using **Blazor Server** with **MudBlazor** components. The UI provides a complete interface for managing cryptocurrency backtests, strategies, and analyzing trading performance.

## Architecture

### Technology Stack
- **Framework**: ASP.NET Core 9.0 Blazor Server
- **UI Library**: MudBlazor 8.13.0
- **Component Model**: Interactive Server-side rendering
- **HTTP Client**: Microsoft.Extensions.Http 9.0.9
- **Backend API**: .NET Data API (from Phase 2)

### Project Structure
```
blazor-ui/
├── Components/
│   ├── Layout/
│   │   ├── MainLayout.razor          # Primary layout with drawer navigation
│   │   └── NavMenu.razor             # Navigation menu
│   ├── Pages/
│   │   ├── Dashboard.razor           # Main dashboard with statistics
│   │   ├── Cryptocurrencies.razor    # Cryptocurrency list/browser
│   │   ├── Strategies.razor          # Available trading strategies
│   │   └── Backtest/
│   │       ├── NewBacktest.razor     # Backtest creation form
│   │       └── BacktestList.razor    # Paginated backtest results
│   ├── App.razor                     # Root component
│   ├── Routes.razor                  # Routing configuration
│   └── _Imports.razor                # Global using directives
├── Models/
│   └── ApiModels.cs                  # Data models (DTOs)
├── Services/
│   └── CryptoBacktestApiService.cs   # API client service
├── wwwroot/                          # Static assets
├── Program.cs                        # Application entry point
├── Dockerfile                        # Container configuration
└── appsettings.json                  # Configuration

```

## Features Implemented

### 1. Dashboard Page (`/`)
**Purpose**: Provides high-level overview of backtest performance

**Features**:
- **Statistics Cards**:
  - Total number of backtests
  - Average return percentage
  - Average Sharpe ratio
  - Total trades executed
  
- **Best/Worst Backtest Highlights**:
  - Strategy and cryptocurrency used
  - Return percentage
  - Sharpe ratio
  - Win rate
  - Direct links to detailed views
  
- **Recent Backtests Table**:
  - Last 5 backtests with key metrics
  - Color-coded returns (green for profit, red for loss)
  - Quick access to individual backtest details

### 2. Cryptocurrencies Page (`/cryptocurrencies`)
**Purpose**: Browse available cryptocurrencies for backtesting

**Features**:
- Searchable table (by symbol or name)
- Data coverage information (first/last price dates)
- Total data points available
- Quick "Run Backtest" action for each crypto
- Real-time filtering

### 3. Strategies Page (`/strategies`)
**Purpose**: View available trading strategies

**Features**:
- Card-based layout for each strategy
- Strategy description
- Default parameter display (RSI periods, MA lengths, etc.)
- "Use Strategy" quick action
- Three strategies implemented:
  - RSI (Relative Strength Index)
  - MA Crossover (Moving Average Crossover)
  - Bollinger Bands

### 4. New Backtest Page (`/backtest/new`)
**Purpose**: Create and execute new backtests

**Features**:
- **Cryptocurrency Selection**: Dropdown with all available cryptos
- **Strategy Selection**: Dynamic parameter inputs based on strategy
- **Date Range**: Start and end date pickers
- **Initial Capital**: Configurable starting capital
- **Dynamic Strategy Parameters**:
  - **RSI**: Period, Oversold threshold, Overbought threshold
  - **MA Crossover**: Short period, Long period
  - **Bollinger Bands**: Period, Standard deviation multiplier
- Real-time validation
- Progress indicator during execution
- Automatic navigation to results on completion

### 5. Backtest List Page (`/backtest`)
**Purpose**: Browse, filter, and manage all backtests

**Features**:
- **Server-side Pagination**: Handle large datasets efficiently
- **Column Sorting**: Sort by crypto, strategy, dates, returns, Sharpe ratio, win rate
- **Advanced Filters** (collapsible):
  - Filter by cryptocurrency
  - Filter by strategy
  - Filter by date range
- **Actions**:
  - View detailed results
  - Delete backtests (with confirmation)
- Color-coded returns
- Responsive table layout

### 6. Layout & Navigation
**Features**:
- **Responsive Drawer Navigation**: Collapsible sidebar
- **Theme Support**: Light/dark theme configuration
- **MudBlazor Components**: Material Design UI
- **Navigation Groups**: Organized menu structure
- **App Bar**: Quick access to key functions

## API Integration

### CryptoBacktestApiService
Centralized service for all API communication:

```csharp
// Cryptocurrency operations
GetCryptocurrenciesAsync()
GetCryptocurrencyAsync(int id)
GetPricesAsync(int cryptoId, DateTime? start, DateTime? end, string? interval)

// Strategy operations
GetStrategiesAsync()
GetStrategyAsync(int id)

// Backtest operations
CreateBacktestAsync(BacktestRequest request)
GetBacktestsAsync(offset, limit, sortBy, filters...)
GetBacktestDetailsAsync(int id)
DeleteBacktestAsync(int id)
GetBacktestStatsAsync(int? cryptoId, int? strategyId)
CompareBacktestsAsync(List<int> ids)

// Indicator operations
GetIndicatorAsync(TechnicalIndicatorRequest request)
```

### Configuration
API base URL configured in `appsettings.json`:
```json
{
  "ApiSettings": {
    "BaseUrl": "http://dotnet-data-api:5002"
  }
}
```

## Deployment

### Docker Configuration
**Dockerfile** (Multi-stage build):
```dockerfile
# Build stage - SDK 9.0
FROM mcr.microsoft.com/dotnet/sdk:9.0 AS build
WORKDIR /src
COPY *.csproj ./
RUN dotnet restore
COPY . ./
RUN dotnet publish -c Release -o /app/publish

# Runtime stage - ASP.NET 9.0
FROM mcr.microsoft.com/dotnet/aspnet:9.0 AS runtime
WORKDIR /app
COPY --from=build /app/publish .
EXPOSE 5003
ENV ASPNETCORE_URLS=http://+:5003
ENTRYPOINT ["dotnet", "CryptoBacktestUI.dll"]
```

### Docker Compose Integration
```yaml
blazor-ui:
  build:
    context: ./blazor-ui
    dockerfile: Dockerfile
  container_name: blazor-ui
  ports:
    - "5003:5003"
  environment:
    - ASPNETCORE_ENVIRONMENT=Production
    - ASPNETCORE_URLS=http://+:5003
    - ApiSettings__BaseUrl=http://dotnet-data-api:5002
  depends_on:
    dotnet-data-api:
      condition: service_healthy
  networks:
    - app-network
  restart: unless-stopped
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:5003/"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s
```

### Nginx Routing
```nginx
# Crypto Backtest Blazor UI (with SignalR/WebSocket support)
location /crypto-backtest/ {
    proxy_pass http://blazor-ui/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_cache_bypass $http_upgrade;
    proxy_read_timeout 86400;
    
    add_header X-Frame-Options DENY always;
}
```

## Access URLs

### Local Development (inside Docker network)
- Blazor UI: `http://blazor-ui:5003`

### External Access (through nginx)
- HTTPS: `https://your-domain/crypto-backtest/`
- HTTP: `http://your-domain/crypto-backtest/` (redirects to HTTPS)

### Direct Container Access
- `http://localhost:5003` (if not using nginx proxy)

## Build & Run

### Build the Blazor UI
```bash
cd /home/one_control/docker-project
docker compose build blazor-ui
```

### Start the Service
```bash
docker compose up -d blazor-ui
```

### Restart nginx (after configuration changes)
```bash
docker compose restart nginx
```

### View Logs
```bash
docker logs blazor-ui -f
```

### Stop the Service
```bash
docker compose stop blazor-ui
```

## Data Models

### Key DTOs
```csharp
// Cryptocurrency information
public class Cryptocurrency
{
    public int Id { get; set; }
    public string Symbol { get; set; }
    public string Name { get; set; }
    public DateTime FirstPriceDate { get; set; }
    public DateTime LastPriceDate { get; set; }
    public int TotalDataPoints { get; set; }
}

// Trading strategy configuration
public class Strategy
{
    public int Id { get; set; }
    public string Name { get; set; }
    public string Description { get; set; }
    public Dictionary<string, object>? Parameters { get; set; }
}

// Backtest execution result
public class BacktestResult
{
    public int Id { get; set; }
    public int CryptocurrencyId { get; set; }
    public string CryptocurrencySymbol { get; set; }
    public int StrategyId { get; set; }
    public string StrategyName { get; set; }
    public DateTime StartDate { get; set; }
    public DateTime EndDate { get; set; }
    public decimal InitialCapital { get; set; }
    public decimal FinalCapital { get; set; }
    public decimal TotalReturn { get; set; }
    public decimal ReturnPercentage { get; set; }
    public int TotalTrades { get; set; }
    public int WinningTrades { get; set; }
    public int LosingTrades { get; set; }
    public decimal WinRate { get; set; }
    public decimal MaxDrawdown { get; set; }
    public decimal SharpeRatio { get; set; }
    public DateTime CreatedAt { get; set; }
    public Dictionary<string, object>? Parameters { get; set; }
}

// Backtest creation request
public class BacktestRequest
{
    public int CryptocurrencyId { get; set; }
    public int StrategyId { get; set; }
    public DateTime StartDate { get; set; }
    public DateTime EndDate { get; set; }
    public decimal InitialCapital { get; set; } = 10000m;
    public Dictionary<string, object>? Parameters { get; set; }
}

// Aggregate statistics
public class BacktestStats
{
    public int TotalBacktests { get; set; }
    public decimal AverageReturn { get; set; }
    public decimal AverageSharpeRatio { get; set; }
    public int TotalTrades { get; set; }
    public decimal AverageWinRate { get; set; }
    public BacktestResult? BestBacktest { get; set; }
    public BacktestResult? WorstBacktest { get; set; }
}
```

## MudBlazor Components Used

- **MudAppBar**: Top navigation bar
- **MudDrawer**: Side navigation drawer
- **MudMainContent**: Main content area
- **MudCard**: Card containers
- **MudTable**: Data tables with sorting/pagination
- **MudSelect**: Dropdown selections
- **MudDatePicker**: Date selection
- **MudNumericField**: Numeric inputs
- **MudTextField**: Text inputs
- **MudButton**: Action buttons
- **MudIconButton**: Icon-only buttons
- **MudChip**: Small status indicators
- **MudAlert**: Error/info messages
- **MudProgressLinear**: Loading indicators
- **MudExpansionPanel**: Collapsible sections
- **MudSnackbar**: Toast notifications
- **MudDialog**: Confirmation dialogs

## Current Status

### ✅ Completed
- Blazor Server project setup with .NET 9.0
- MudBlazor integration (8.13.0)
- API service layer with full CRUD operations
- Dashboard with statistics and recent results
- Cryptocurrency browser with search
- Strategy catalog
- New backtest creation form with dynamic parameters
- Backtest list with server-side pagination
- Advanced filtering and sorting
- Docker containerization
- Nginx proxy configuration
- Docker Compose integration
- Responsive layout and navigation

### 🔄 Not Yet Implemented (Future Enhancements)
- **Backtest Detail Page**: View individual backtest with trade history
- **Comparison Page**: Side-by-side comparison of multiple backtests
- **Chart Visualizations**: Price charts, equity curves, drawdown graphs
- **Indicators Page**: Visualize technical indicators (RSI, MA, BB)
- **Real-time Updates**: SignalR for live backtest progress
- **Export Functionality**: Export results to CSV/Excel
- **User Authentication**: Login/logout functionality
- **Dark Mode Toggle**: Theme switcher in UI
- **Performance Benchmarks**: Strategy performance analytics
- **Custom Strategy Builder**: UI for creating custom strategies

## Performance Considerations

- **Server-side Rendering**: Fast initial page loads
- **Server-side Pagination**: Efficient handling of large datasets
- **Lazy Loading**: Components load on demand
- **HTTP Client Pooling**: Reusable HTTP connections
- **Connection String Caching**: Minimized API calls

## Security Features

- **HTTPS Only**: Enforced via nginx
- **CORS Configuration**: Restricted to API endpoints
- **XSS Protection**: Blazor automatic encoding
- **CSRF Protection**: Built-in antiforgery tokens
- **Input Validation**: Required fields and type checking

## Troubleshooting

### Container Won't Start
```bash
# Check container status
docker ps -a | grep blazor-ui

# View full logs
docker logs blazor-ui

# Rebuild and restart
docker compose build blazor-ui
docker compose up -d blazor-ui
```

### API Connection Issues
```bash
# Check API is running
docker ps | grep dotnet-data-api

# Test API connectivity from blazor-ui container
docker exec blazor-ui curl http://dotnet-data-api:5002/health

# Verify network
docker network inspect docker-project-network
```

### Build Errors
```bash
# Clean build artifacts
cd blazor-ui
rm -rf obj/ bin/

# Rebuild with verbose output
docker compose build --no-cache --progress=plain blazor-ui
```

## Next Steps (Phase 4 Recommendations)

1. **Add Chart Visualizations**:
   - Integrate Plotly.NET or ApexCharts.Blazor
   - Create equity curve charts
   - Add candlestick price charts
   - Implement indicator overlays

2. **Implement SignalR Hub**:
   - Real-time backtest progress updates
   - Live trade notifications
   - Multi-user broadcast

3. **Build Comparison Page**:
   - Select multiple backtests
   - Side-by-side metric comparison
   - Visual performance charts
   - Export comparison reports

4. **Add Backtest Detail Page**:
   - Complete trade history table
   - Trade-by-trade analysis
   - Position sizing information
   - Portfolio value timeline

5. **Implement Authentication**:
   - ASP.NET Core Identity
   - User registration/login
   - Role-based access control
   - Protected routes

## Resources

- **MudBlazor Documentation**: https://mudblazor.com/
- **Blazor Documentation**: https://learn.microsoft.com/aspnet/core/blazor/
- **ASP.NET Core 9.0**: https://learn.microsoft.com/aspnet/core/release-notes/aspnetcore-9.0
- **Docker Compose**: https://docs.docker.com/compose/

## Conclusion

Phase 3 delivers a fully functional, modern web UI for the Crypto Backtest Platform. The Blazor Server architecture provides excellent interactivity with server-side state management, while MudBlazor ensures a professional Material Design look and feel. The application is containerized, integrated into the existing Docker infrastructure, and ready for production deployment.
