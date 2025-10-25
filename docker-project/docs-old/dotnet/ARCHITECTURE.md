# .NET 10 Crypto Backtester - Architecture

Complete system architecture documentation for the .NET 10 integration.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Principles](#architecture-principles)
3. [Component Architecture](#component-architecture)
4. [Data Flow](#data-flow)
5. [Database Design](#database-design)
6. [API Design](#api-design)
7. [Frontend Architecture](#frontend-architecture)
8. [Communication Patterns](#communication-patterns)
9. [Security Architecture](#security-architecture)
10. [Performance Architecture](#performance-architecture)
11. [Deployment Architecture](#deployment-architecture)
12. [Integration Points](#integration-points)

---

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         NGINX (Port 80/443)                     │
│                     SSL Termination & Routing                    │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Python Flask   │  │  .NET Blazor    │  │  .NET Data API  │
│   Web App       │  │   Web App       │  │                 │
│   Port 5000     │  │   Port 5001     │  │   Port 5002     │
└─────────────────┘  └─────────────────┘  └─────────────────┘
          │                   │                   │
          │                   └─────────┬─────────┘
          │                             │
          └─────────────┬───────────────┘
                        │
          ┌─────────────┴───────────────┐
          │                             │
          ▼                             ▼
┌─────────────────────────┐   ┌──────────────────┐
│  PostgreSQL 17 +        │   │   Redis 7        │
│  TimescaleDB 2.22.1     │   │   Cache Layer    │
│  Port 5432              │   │   Port 6379      │
└─────────────────────────┘   └──────────────────┘
```

### Component Interaction

```
User Browser
     │
     ▼
┌─────────────────────────────────────┐
│  Blazor Server (dotnet-web)         │
│  ├─> SignalR Connection             │
│  ├─> Component Rendering            │
│  └─> Event Handling                 │
└─────────────────────────────────────┘
     │
     │ HTTP/JSON
     ▼
┌─────────────────────────────────────┐
│  Data API (dotnet-data-api)         │
│  ├─> RESTful Endpoints              │
│  ├─> Backtest Engine                │
│  ├─> Strategy Execution             │
│  └─> Technical Indicators           │
└─────────────────────────────────────┘
     │
     │ SQL/Binary Protocol
     ▼
┌─────────────────────────────────────┐
│  PostgreSQL Database                │
│  ├─> Crypto Prices (TimescaleDB)   │
│  ├─> Strategies                     │
│  ├─> Backtest Results               │
│  └─> Technical Indicators           │
└─────────────────────────────────────┘
```

---

## Architecture Principles

### 1. **Microservices Architecture**
- **Separation of Concerns**: Web UI and Data API are independent
- **Single Responsibility**: Each container has one primary function
- **Loose Coupling**: Communicate via HTTP/REST
- **Independent Deployment**: Can update API without touching UI

### 2. **Hybrid Stack Strategy**
- **Python**: Existing functionality, data collection, admin
- **.NET**: High-performance backtesting, real-time features
- **Shared Database**: No data duplication
- **Unified Experience**: Single domain, seamless routing

### 3. **Performance-First Design**
- **Async/Await**: Non-blocking I/O operations
- **Connection Pooling**: Reuse database connections
- **Caching**: Redis for frequently accessed data
- **Minimal Allocations**: Value types, span<T>, memory-efficient code

### 4. **Scalability Patterns**
- **Stateless Design**: No server-side session state
- **Horizontal Scaling**: Can run multiple instances
- **Load Balancing**: Nginx distributes requests
- **Database Connection Management**: Efficient pooling

### 5. **Security by Design**
- **HTTPS Only**: SSL/TLS encryption
- **Input Validation**: All user inputs validated
- **SQL Injection Prevention**: Parameterized queries
- **Rate Limiting**: Prevent abuse
- **CORS Policy**: Controlled cross-origin access

---

## Component Architecture

### dotnet-data-api Container

```
┌───────────────────────────────────────────────────────────────┐
│                      Program.cs (Entry Point)                 │
│  ├─> Configure Services (DI)                                  │
│  ├─> Configure Middleware                                     │
│  ├─> Map Endpoints                                            │
│  └─> Run Application                                          │
└───────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  Endpoints    │    │   Services    │    │    Models     │
│               │    │               │    │               │
│ Crypto        │───▶│ Database      │◀───│ Crypto        │
│ Strategy      │    │ Backtest      │    │ Strategy      │
│ Backtest      │    │ Indicator     │    │ BacktestRes   │
│ Health        │    │ Cache         │    │ Trade         │
└───────────────┘    └───────────────┘    └───────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
            ┌───────────────┐   ┌───────────────┐
            │  Strategies   │   │   Database    │
            │               │   │               │
            │ RSI           │   │ PostgreSQL    │
            │ MA Crossover  │   │ Connection    │
            │ Bollinger     │   │ Pooling       │
            │ Momentum      │   │               │
            │ Mean Rev.     │   │ Npgsql +      │
            │ Supp/Res      │   │ Dapper        │
            └───────────────┘   └───────────────┘
```

**Responsibilities:**
- ✅ RESTful API endpoints
- ✅ Backtest execution engine
- ✅ Strategy implementations (6 strategies)
- ✅ Technical indicator calculations
- ✅ Database operations (Npgsql + Dapper)
- ✅ Caching layer (Redis)
- ✅ Health checks and monitoring

**Technology Stack:**
- ASP.NET Core 10 Minimal APIs
- Npgsql 8.x (PostgreSQL driver)
- Dapper 2.x (micro-ORM)
- System.Text.Json (serialization)
- Microsoft.Extensions.Caching.Memory

### dotnet-web Container

```
┌───────────────────────────────────────────────────────────────┐
│                      Program.cs (Entry Point)                 │
│  ├─> Configure Blazor Server                                  │
│  ├─> Configure SignalR                                        │
│  ├─> Add Services                                             │
│  └─> Run Application                                          │
└───────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│    Pages      │    │  Components   │    │   Services    │
│               │    │               │    │               │
│ Index         │───▶│ Strategy      │◀───│ CryptoData    │
│ Backtest      │    │  Selector     │    │ Backtest      │
│ Compare       │    │ Parameter     │    │ Chart         │
│               │    │  Editor       │    │ ApiClient     │
│               │    │ Results       │    │               │
│               │    │  Display      │    │               │
│               │    │ Performance   │    │               │
│               │    │  Chart        │    │               │
│               │    │ Trade History │    │               │
└───────────────┘    └───────────────┘    └───────────────┘
        │                     │
        └─────────┬───────────┘
                  ▼
        ┌───────────────────┐
        │   SignalR Hub     │
        │                   │
        │ Real-time         │
        │ Progress Updates  │
        │ Live Charts       │
        └───────────────────┘
```

**Responsibilities:**
- ✅ Blazor Server UI rendering
- ✅ SignalR real-time communication
- ✅ Interactive components (MudBlazor)
- ✅ Chart visualizations (Radzen)
- ✅ API client service
- ✅ State management
- ✅ Form validation

**Technology Stack:**
- Blazor Server (ASP.NET Core 10)
- SignalR (WebSocket/Server-Sent Events)
- MudBlazor 7.x (UI components)
- Radzen Blazor (charts)
- HttpClient (API communication)

---

## Data Flow

### Backtest Execution Flow

```
┌──────────────┐
│ User Browser │
└──────┬───────┘
       │ 1. Submit backtest request
       ▼
┌─────────────────────────────────────┐
│  Blazor Page (Backtest.razor)       │
│  ├─> Validate form input            │
│  ├─> Show loading indicator         │
│  └─> Call BacktestService           │
└─────────────────────────────────────┘
       │ 2. HTTP POST
       ▼
┌─────────────────────────────────────┐
│  BacktestService (Client)           │
│  ├─> Serialize request              │
│  ├─> HTTP POST to API               │
│  └─> Handle response                │
└─────────────────────────────────────┘
       │ 3. HTTP POST /backtest
       ▼
┌─────────────────────────────────────┐
│  BacktestEndpoints (API)            │
│  ├─> Validate request               │
│  ├─> Check cache                    │
│  └─> Call BacktestEngine            │
└─────────────────────────────────────┘
       │ 4. Execute backtest
       ▼
┌─────────────────────────────────────┐
│  BacktestEngine                     │
│  ├─> Load price data                │
│  ├─> Load strategy                  │
│  ├─> Calculate indicators           │
│  ├─> Execute strategy               │
│  ├─> Generate signals               │
│  ├─> Simulate trades                │
│  ├─> Calculate metrics              │
│  └─> Store results                  │
└─────────────────────────────────────┘
       │ 5. Query database
       ▼
┌─────────────────────────────────────┐
│  DatabaseService                    │
│  ├─> Get crypto prices (Dapper)    │
│  ├─> Get strategy config            │
│  └─> Insert backtest result         │
└─────────────────────────────────────┘
       │ 6. SQL queries
       ▼
┌─────────────────────────────────────┐
│  PostgreSQL + TimescaleDB           │
│  ├─> crypto_prices table            │
│  ├─> crypto_strategies table        │
│  └─> crypto_backtest_results        │
└─────────────────────────────────────┘
       │ 7. Return results
       ▼
┌─────────────────────────────────────┐
│  BacktestEndpoints (API)            │
│  ├─> Cache results (Redis)          │
│  ├─> Serialize response             │
│  └─> Return JSON                    │
└─────────────────────────────────────┘
       │ 8. HTTP 200 + JSON
       ▼
┌─────────────────────────────────────┐
│  BacktestService (Client)           │
│  ├─> Deserialize response           │
│  └─> Update UI state                │
└─────────────────────────────────────┘
       │ 9. Render results
       ▼
┌─────────────────────────────────────┐
│  Blazor Page (Backtest.razor)       │
│  ├─> Display metrics                │
│  ├─> Render charts                  │
│  └─> Show trade history             │
└─────────────────────────────────────┘
       │ 10. SignalR updates
       ▼
┌──────────────┐
│ User Browser │
│ (Live Charts)│
└──────────────┘
```

### Real-Time Progress Updates

```
┌──────────────┐
│ User Browser │◀──────────────────┐
└──────┬───────┘                   │
       │                           │ SignalR
       │ Submit request            │ Progress
       ▼                           │ Events
┌─────────────────┐                │
│  Blazor Server  │                │
│  Hub Connection │────────────────┘
└─────────┬───────┘
          │ HTTP POST
          ▼
┌─────────────────┐
│  Data API       │
│  ├─> Start      │
│  ├─> Progress   │──▶ Notify hub (async)
│  │   20%        │
│  ├─> Progress   │──▶ Notify hub (async)
│  │   50%        │
│  ├─> Progress   │──▶ Notify hub (async)
│  │   80%        │
│  └─> Complete   │──▶ Notify hub (async)
└─────────────────┘
```

---

## Database Design

### Shared Schema Strategy

**Philosophy**: No schema changes required. .NET uses existing Python tables.

### Key Tables Used by .NET

#### cryptocurrencies
```sql
CREATE TABLE cryptocurrencies (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    name VARCHAR(100) NOT NULL,
    coingecko_id VARCHAR(50),
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### crypto_prices (TimescaleDB Hypertable)
```sql
CREATE TABLE crypto_prices (
    id SERIAL,
    crypto_id INTEGER REFERENCES cryptocurrencies(id),
    timestamp TIMESTAMP NOT NULL,
    price DECIMAL(20, 8) NOT NULL,
    volume DECIMAL(20, 2),
    market_cap DECIMAL(20, 2),
    PRIMARY KEY (timestamp, crypto_id)
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('crypto_prices', 'timestamp');
```

#### crypto_strategies
```sql
CREATE TABLE crypto_strategies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parameters JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### crypto_backtest_results
```sql
CREATE TABLE crypto_backtest_results (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER REFERENCES crypto_strategies(id),
    crypto_id INTEGER REFERENCES cryptocurrencies(id),
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    initial_investment DECIMAL(20, 2),
    final_value DECIMAL(20, 2),
    total_return DECIMAL(10, 4),
    total_trades INTEGER,
    winning_trades INTEGER,
    losing_trades INTEGER,
    max_drawdown DECIMAL(10, 4),
    sharpe_ratio DECIMAL(10, 4),
    execution_time_ms INTEGER,
    parameters JSONB,
    portfolio_values JSONB,
    trades JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    executed_by VARCHAR(50) DEFAULT 'dotnet'
);
```

#### crypto_technical_indicators
```sql
CREATE TABLE crypto_technical_indicators (
    id SERIAL PRIMARY KEY,
    crypto_id INTEGER REFERENCES cryptocurrencies(id),
    timestamp TIMESTAMP NOT NULL,
    indicator_name VARCHAR(50) NOT NULL,
    value DECIMAL(20, 8),
    parameters JSONB,
    UNIQUE(crypto_id, timestamp, indicator_name)
);
```

### Database Connection Management

**Connection Pooling Configuration:**
```csharp
// Npgsql connection string
"Host=database;Port=5432;Database=webapp_db;Username=root;Password=***;" +
"Pooling=true;" +
"Minimum Pool Size=5;" +
"Maximum Pool Size=100;" +
"Connection Idle Lifetime=300;" +
"Connection Pruning Interval=10"
```

**Benefits:**
- ✅ Reuse existing connections
- ✅ Handle 100+ concurrent requests
- ✅ Automatic connection cleanup
- ✅ Reduced connection overhead

---

## API Design

### RESTful Endpoint Structure

```
GET    /health                          # Health check
GET    /cryptocurrencies                # List all cryptos
GET    /cryptocurrencies/{id}           # Get single crypto
GET    /cryptocurrencies/{id}/prices    # Get price history
GET    /strategies                      # List all strategies
GET    /strategies/{id}                 # Get single strategy
POST   /backtest                        # Execute backtest
GET    /backtest/{id}                   # Get backtest result
GET    /backtest/{id}/trades            # Get trade history
DELETE /backtest/{id}                   # Delete backtest
GET    /indicators/{crypto_id}          # Get technical indicators
```

### Request/Response Models

**BacktestRequest:**
```csharp
public record BacktestRequest
{
    public int StrategyId { get; init; }
    public int CryptoId { get; init; }
    public DateTime StartDate { get; init; }
    public DateTime EndDate { get; init; }
    public decimal InitialInvestment { get; init; }
    public Dictionary<string, object> Parameters { get; init; }
}
```

**BacktestResponse:**
```csharp
public record BacktestResponse
{
    public int Id { get; init; }
    public string Status { get; init; }
    public BacktestMetrics Metrics { get; init; }
    public List<Trade> Trades { get; init; }
    public List<PortfolioSnapshot> PortfolioValues { get; init; }
    public int ExecutionTimeMs { get; init; }
}
```

### API Versioning

```
/v1/backtest    # Current version
/v2/backtest    # Future version (breaking changes)
```

---

## Frontend Architecture

### Blazor Component Hierarchy

```
App.razor (Root)
  └─> MainLayout.razor
       ├─> NavMenu.razor
       └─> @Body
            ├─> Index.razor (Home)
            ├─> Backtest.razor
            │    ├─> StrategySelector
            │    ├─> ParameterEditor
            │    ├─> BacktestResults
            │    │    ├─> MetricsCard (multiple)
            │    │    ├─> PerformanceChart
            │    │    └─> TradeHistory
            │    └─> LoadingSpinner
            └─> Compare.razor
                 ├─> SplitView
                 │    ├─> PythonBacktest
                 │    └─> DotnetBacktest
                 └─> ComparisonTable
```

### State Management

**Service Injection Pattern:**
```csharp
@inject CryptoDataService CryptoService
@inject BacktestService BacktestService
@inject NavigationManager Navigation
@inject ISnackbar Snackbar
```

**Component State:**
```csharp
public partial class Backtest
{
    private List<Cryptocurrency> cryptos = new();
    private List<Strategy> strategies = new();
    private BacktestRequest request = new();
    private BacktestResponse? result;
    private bool isLoading = false;
    private string errorMessage = "";
}
```

### SignalR Real-Time Updates

**Hub Definition:**
```csharp
public class BacktestHub : Hub
{
    public async Task JoinBacktestGroup(int backtestId)
    {
        await Groups.AddToGroupAsync(
            Context.ConnectionId, 
            $"backtest-{backtestId}"
        );
    }
    
    public async Task NotifyProgress(
        int backtestId, 
        int percentage, 
        string message
    )
    {
        await Clients.Group($"backtest-{backtestId}")
            .SendAsync("ProgressUpdate", percentage, message);
    }
}
```

**Client Connection:**
```csharp
hubConnection = new HubConnectionBuilder()
    .WithUrl(NavigationManager.ToAbsoluteUri("/backtest-hub"))
    .WithAutomaticReconnect()
    .Build();

hubConnection.On<int, string>("ProgressUpdate", 
    (percentage, message) =>
{
    progress = percentage;
    statusMessage = message;
    StateHasChanged();
});

await hubConnection.StartAsync();
```

---

## Communication Patterns

### 1. Request-Response (HTTP)
**Use Case**: Standard CRUD operations, backtest submission

```
Client ──HTTP POST──> API ──SQL──> Database
       <──JSON 200───     <──Data──
```

### 2. Real-Time Updates (SignalR)
**Use Case**: Progress updates, live charts

```
Client <══WebSocket══> Blazor Server
                            │
                            │ HTTP polling
                            ▼
                       Data API
```

### 3. Caching Layer (Redis)
**Use Case**: Frequently accessed data, backtest results

```
API ──Check Cache──> Redis
    │                  │
    │ Cache miss       │ Cache hit
    ▼                  ▼
Database ──Store──> Redis ──Return──> Client
```

### 4. Async Processing
**Use Case**: Long-running backtests

```
Client ──Submit Request──> API
       <──202 Accepted───
       
API ──Background Task──> Execute Backtest
                              │
                              ▼
                         Complete
                              │
                              ▼
                         SignalR Notify ──> Client
```

---

## Security Architecture

### 1. **Transport Security**
- ✅ HTTPS only (SSL/TLS 1.3)
- ✅ HSTS headers enabled
- ✅ Certificate management via nginx

### 2. **Input Validation**
```csharp
public static ValidationResult ValidateBacktestRequest(
    BacktestRequest request)
{
    if (request.InitialInvestment <= 0)
        return ValidationResult.Error("Investment must be positive");
    
    if (request.EndDate <= request.StartDate)
        return ValidationResult.Error("Invalid date range");
    
    if (request.StrategyId <= 0)
        return ValidationResult.Error("Invalid strategy");
    
    return ValidationResult.Success();
}
```

### 3. **SQL Injection Prevention**
```csharp
// ✅ Parameterized queries (Dapper)
var prices = await connection.QueryAsync<CryptoPrice>(
    "SELECT * FROM crypto_prices WHERE crypto_id = @CryptoId " +
    "AND timestamp BETWEEN @Start AND @End",
    new { CryptoId = cryptoId, Start = start, End = end }
);

// ❌ Never do this
var sql = $"SELECT * FROM crypto_prices WHERE crypto_id = {cryptoId}";
```

### 4. **Rate Limiting**
```csharp
builder.Services.AddRateLimiter(options =>
{
    options.AddFixedWindowLimiter("api", opt =>
    {
        opt.PermitLimit = 100;
        opt.Window = TimeSpan.FromMinutes(1);
    });
});
```

### 5. **CORS Policy**
```csharp
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowFrontend", policy =>
    {
        policy.WithOrigins("https://localhost")
              .AllowAnyMethod()
              .AllowAnyHeader()
              .AllowCredentials();
    });
});
```

---

## Performance Architecture

### 1. **Async/Await Pattern**
```csharp
// All I/O operations are async
public async Task<List<CryptoPrice>> GetPricesAsync(
    int cryptoId, DateTime start, DateTime end)
{
    using var connection = await GetConnectionAsync();
    return (await connection.QueryAsync<CryptoPrice>(sql, param))
        .ToList();
}
```

### 2. **Connection Pooling**
- Min Pool Size: 5 connections
- Max Pool Size: 100 connections
- Idle Lifetime: 5 minutes
- Automatic pruning every 10 seconds

### 3. **Caching Strategy**
```csharp
public async Task<List<Cryptocurrency>> GetCryptocurrenciesAsync()
{
    // Check memory cache first
    if (cache.TryGetValue("cryptos", out List<Cryptocurrency> cryptos))
        return cryptos;
    
    // Load from database
    cryptos = await database.GetAllCryptosAsync();
    
    // Cache for 10 minutes
    cache.Set("cryptos", cryptos, TimeSpan.FromMinutes(10));
    
    return cryptos;
}
```

### 4. **Memory Efficiency**
```csharp
// Use Span<T> for stack allocations
Span<double> prices = stackalloc double[100];

// Use ArrayPool for large arrays
var pool = ArrayPool<double>.Shared;
var array = pool.Rent(10000);
try
{
    // Use array
}
finally
{
    pool.Return(array);
}
```

### 5. **Parallel Processing**
```csharp
// Calculate multiple indicators in parallel
var tasks = new[]
{
    CalculateRSIAsync(prices),
    CalculateMACDAsync(prices),
    CalculateBollingerAsync(prices)
};

var results = await Task.WhenAll(tasks);
```

---

## Deployment Architecture

### Container Configuration

**docker-compose.yml addition:**
```yaml
services:
  dotnet-data-api:
    build:
      context: ./dotnet-data-api
      dockerfile: Dockerfile
    container_name: dotnet-data-api
    ports:
      - "5002:5002"
    environment:
      - ASPNETCORE_ENVIRONMENT=Production
      - ASPNETCORE_URLS=http://+:5002
    depends_on:
      - database
      - redis
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5002/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  dotnet-web:
    build:
      context: ./dotnet-web
      dockerfile: Dockerfile
    container_name: dotnet-web
    ports:
      - "5001:5001"
    environment:
      - ASPNETCORE_ENVIRONMENT=Production
      - ASPNETCORE_URLS=http://+:5001
      - ApiSettings__BaseUrl=http://dotnet-data-api:5002
    depends_on:
      - dotnet-data-api
    networks:
      - app-network
    restart: unless-stopped
```

### Nginx Routing

```nginx
# .NET Blazor Web
location /dotnet/ {
    proxy_pass http://dotnet-web:5001/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_cache_bypass $http_upgrade;
}

# .NET Data API
location /dotnet-api/ {
    proxy_pass http://dotnet-data-api:5002/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

---

## Integration Points

### Python ↔ .NET Coexistence

**Shared Resources:**
- ✅ PostgreSQL database (same schema)
- ✅ Redis cache (different key prefixes)
- ✅ Nginx reverse proxy
- ✅ SSL certificates

**Independent Resources:**
- ✅ Application code
- ✅ Dependencies
- ✅ Runtime environments
- ✅ Log files

**Data Consistency:**
- Both systems read same crypto_prices data
- Both systems write to crypto_backtest_results (with `executed_by` flag)
- No conflicts due to independent execution

**User Experience:**
- Seamless navigation between Python and .NET pages
- Consistent UI styling
- Shared authentication (future enhancement)

---

## Scalability Considerations

### Horizontal Scaling
```yaml
# Scale API to 3 instances
docker-compose up -d --scale dotnet-data-api=3

# Nginx load balancing
upstream dotnet_api {
    server dotnet-data-api:5002;
    server dotnet-data-api:5002;
    server dotnet-data-api:5002;
}
```

### Database Optimization
- TimescaleDB compression for old data
- Partitioning by time range
- Indexes on frequently queried columns
- Connection pooling

### Caching Strategy
- Redis for shared cache
- In-memory cache per container
- CDN for static assets (future)

---

## Monitoring & Observability

### Health Checks
```csharp
app.MapHealthChecks("/health", new HealthCheckOptions
{
    ResponseWriter = async (context, report) =>
    {
        context.Response.ContentType = "application/json";
        await context.Response.WriteAsJsonAsync(new
        {
            status = report.Status.ToString(),
            duration = report.TotalDuration,
            checks = report.Entries.Select(e => new
            {
                name = e.Key,
                status = e.Value.Status.ToString()
            })
        });
    }
});
```

### Logging
```csharp
builder.Logging.AddConsole();
builder.Logging.AddDebug();
builder.Logging.SetMinimumLevel(LogLevel.Information);
```

### Metrics
- Request count
- Response times
- Error rates
- Database connection pool usage
- Cache hit rates

---

## Future Enhancements

### Phase 2
- [ ] JWT authentication
- [ ] User-specific backtests
- [ ] WebSocket streaming prices
- [ ] Advanced charting

### Phase 3
- [ ] Kubernetes deployment
- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Distributed tracing

---

**Version:** 1.0.0  
**Last Updated:** October 9, 2025  
**Status:** 🟢 Ready for Implementation
