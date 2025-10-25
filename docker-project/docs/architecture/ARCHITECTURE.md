# System Architecture

**High-level system design and service interactions.**

## 🏗️ Overall Architecture

### Multi-Tier Distributed System

```
┌─────────────────────────────────────────────────────────────┐
│                     Users (Web Browser)                     │
└──────────────────┬──────────────────────────────────────────┘
                   │ HTTPS/SSL
                   ↓
┌─────────────────────────────────────────────────────────────┐
│                    Nginx Reverse Proxy                      │
│           (Routing, SSL Termination, Security)             │
└──────────────────┬──────────────────────────────────────────┘
         ┌─────────┼─────────┬─────────┐
         ↓         ↓         ↓         ↓
    ┌────────┐ ┌────────┐ ┌─────────┐ ┌────────┐
    │ Flask  │ │ Flask  │ │ pgAdmin │ │ Static │
    │ Web App│ │  API   │ │  Admin  │ │ Assets │
    │  5000  │ │  8000  │ │   80    │ │  443   │
    └────┬───┘ └───┬────┘ └────┬────┘ └────────┘
         │         │            │
         └─────────┼────────────┘
                   │
    ┌──────────────┴─────────────────┐
    │  Shared Services Layer         │
    ├────────────────────────────────┤
    │  • Backtesting Engine          │
    │  • Crypto/Stock Data Services  │
    │  • Weather Data Collection     │
    │  • Caching & Optimization      │
    └──────────────────┬─────────────┘
                       │
         ┌─────────────┼──────────────┐
         ↓             ↓              ↓
    ┌─────────┐  ┌─────────┐    ┌──────────┐
    │Database │  │  Cache  │    │ Scheduled│
    │  PG17   │  │  Redis  │    │  Jobs    │
    │TimescaleDB         │
    └─────────┘  └─────────┘    └──────────┘
```

## 🔄 Service Components

### 1. Nginx (Port 443 - HTTPS)
- **Role**: Reverse proxy, SSL/TLS termination, security headers
- **Features**:
  - HTTPS/SSL encryption for all traffic
  - Automatic HTTP → HTTPS redirects
  - Security headers (HSTS, CSP, X-Frame-Options)
  - Server-Sent Events (SSE) support for streaming
  - Path-based routing to backend services

### 2. Flask Web App (Port 5000)
- **Technology**: Python Flask + Jinja2 + Bootstrap 5
- **Framework**: Flask-Login, bcrypt authentication
- **Features**:
  - User authentication & session management
  - Dashboard and data visualization
  - Admin panel (user management, database tools)
  - Security monitoring and event logging
  - Performance monitoring
  - Container management interface
- **Key Pages**:
  - Dashboard - System overview
  - Stocks - Stock data visualization
  - Weather - Weather data dashboard
  - Performance - System performance metrics
  - Admin - User and database management

### 3. Flask REST API (Port 8000)
- **Technology**: Python Flask-RESTful + psycopg3
- **Framework**: Flask-RESTful Resource classes
- **Features**:
  - REST endpoints for all operations
  - Crypto backtesting with SSE streaming
  - Stock data services (NASDAQ, Helsinki)
  - Weather data collection (current & historic)
  - Redis caching for performance
  - ThreadPoolExecutor for parallel execution
- **Services**:
  - StockDataService - Stock market data
  - CryptoDataService - Cryptocurrency data
  - CryptoBacktestService - Batch backtesting
  - StreamingBacktestService - Real-time SSE backtesting

### 4. PostgreSQL 17 + TimescaleDB
- **Role**: Primary data store
- **Optimization**: Time-series data compression
- **Data**: Cryptocurrencies, price data, backtests, users
- **Size**: 2M+ hourly price records
- **Performance**: Indexed queries, optimized for time-series

### 5. Redis
- **Role**: Caching layer
- **Purpose**: Query result caching, session data
- **Performance**: 3-5x speedup for repeated queries
- **Configuration**: 256MB max memory, LRU eviction, AOF persistence

### 6. pgAdmin4
- **Role**: Database administration UI
- **Access**: Web-based database browser and query tool via /pgadmin/
- **Pre-configured**: Connected to PostgreSQL

## 📊 Data Flow

### Stock Data Flow

```
1. User Opens Stocks Dashboard
   ↓
2. Web App Requests Data
   - API: GET /api/stocks/*
   - Returns: Stock prices, statistics
   ↓
3. API Service Layer
   - StockDataService fetches from DB
   - Redis cache checked first
   - Data returned to webapp
   ↓
4. Webapp Renders Dashboard
   - Displays stock charts
   - Shows statistics
   - Real-time updates
```

### Crypto Backtest Flow (SSE Streaming)

```
1. User Initiates Backtest
   ↓
2. Web App or Direct API Call
   - POST /api/crypto/backtest/stream
   - Body: strategy, parameters, date range
   ↓
3. Backend StreamingBacktestService
   - Validates inputs
   - Fetches crypto price data
   - Loads strategy implementation
   - Executes backtest calculations
   - Yields SSE events progressively
   ↓
4. Returns Results via SSE
   - Real-time progress updates
   - Individual backtest results
   - Final summary
   ↓
5. UI Displays Results
   - Shows metrics as they arrive
   - Progressive loading
   - Complete when stream ends
```

### Data Sources

| Source | Type | Update Frequency |
|--------|------|------------------|
| **Binance API** | Crypto price data | Hourly (automated) |
| **NASDAQ APIs** | Stock price data | Daily (automated) |
| **OpenWeather** | Weather data | Hourly (automated) |
| **User Input** | Manual data entry | On demand |
| **Cache (Redis)** | Query results | 1 hour TTL |
| **Database** | Historical data | Continuous |

## 🔌 API Layer Design

### Flask REST API Endpoints

```
├── /health - Health check endpoint
│
├── /crypto/backtest/
│   ├── POST /stream - SSE streaming backtest
│   ├── POST /run - Single backtest execution
│   ├── POST /batch - Batch backtest execution
│   └── GET /strategies - List available strategies
│
├── /stocks/
│   ├── GET /data - Stock data fetch
│   ├── GET /multi - Multiple stock data
│   ├── GET /prices - Historical prices
│   ├── GET /latest - Latest prices
│   └── GET /stats - Stock statistics
│
├── /weather/
│   ├── GET /current - Current weather data
│   └── GET /historic - Historical weather data
│
└── /user/
    ├── GET /stats - User statistics
    └── GET /database/info - Database information
```

### Flask Web App Routes

```
├── / - Home/Dashboard
├── /login - User authentication
├── /register - User registration
├── /logout - User logout
│
├── /stocks - Stock data visualization
├── /weather - Weather dashboard
├── /performance - Performance monitoring
├── /containers - Docker container management
│
└── /admin/
    ├── /users - User management
    ├── /database - Database tools
    ├── /users/add - Add new user
    └── /users/<id>/edit - Edit user
```

### Authentication

- **Method**: Flask-Login with session-based cookies
- **Password Hashing**: bcrypt
- **Role-Based Access**: user, admin levels
- **Session Store**: Server-side sessions
- **Activity Logging**: All user actions logged to database

## 💾 Database Schema

### Core Tables

```
users
├── id (PK)
├── username
├── email
├── password_hash (bcrypt)
├── user_level (integer - role)
├── created_at
└── last_login

stocks
├── id (PK)
├── symbol (AAPL, GOOGL, etc)
├── name
├── exchange (NASDAQ, OMXH)
└── is_active

stock_prices (TimescaleDB hypertable)
├── stock_id (FK)
├── datetime (time-series)
├── open_price
├── high_price
├── low_price
├── close_price
└── volume

cryptocurrencies
├── id (PK)
├── symbol (BTC, ETH, etc)
├── name
├── binance_symbol
└── is_active

crypto_prices (TimescaleDB hypertable)
├── crypto_id (FK)
├── datetime (time-series)
├── interval_type (1h, 4h, 1d)
├── open_price
├── high_price
├── low_price
├── close_price
└── volume

weather_current
├── id (PK)
├── location
├── datetime
├── temperature
├── humidity
├── pressure
└── description

weather_historic (TimescaleDB hypertable)
├── location
├── datetime (time-series)
├── temperature
├── humidity
├── pressure
└── weather_data (JSONB)

user_activity_log
├── id (PK)
├── user_id (FK)
├── action
├── ip_address
├── user_agent
└── timestamp

security_events
├── id (PK)
├── event_type
├── user_id (FK nullable)
├── ip_address
├── details (JSONB)
└── timestamp

performance_metrics
├── id (PK)
├── endpoint
├── response_time_ms
├── status_code
└── timestamp
```

### Indexes

```
crypto_prices:
- (crypto_id, interval_type, datetime DESC) - Primary lookup
- (datetime) - Time-series queries

stock_prices:
- (stock_id, datetime DESC) - Primary lookup
- (datetime) - Time-series queries

weather_historic:
- (location, datetime DESC) - Location queries
- (datetime) - Time-series queries

users:
- (username) - Login lookup
- (email) - Email uniqueness

user_activity_log:
- (user_id, timestamp DESC) - User activity
- (timestamp DESC) - Recent activity
```

## ⚡ Performance Optimizations

### Query Optimization
- **250x improvement** achieved through optimization phases
- Date range filtering (targeted queries vs full table scans)
- Composite indexes on frequently queried columns
- TimescaleDB hypertables for time-series data

### Caching Strategy
- **Redis cache** for frequently accessed data (3-5x speedup)
- **Query result caching** with 1-hour TTL
- **Application-level caching** for static data
- Session data cached in Redis

### Computation
- **ThreadPoolExecutor** for parallel API requests (4 workers)
- **Server-Sent Events** for progressive loading
- **Batch processing** for bulk operations
- **Connection pooling** for database efficiency

### Database Optimizations
- PostgreSQL 17 with TimescaleDB extension
- 512MB shared_buffers
- JIT compilation enabled
- 200 max connections with pooling
- Automated VACUUM and ANALYZE

## 🔐 Security Architecture

### Layers

```
┌─────────────────────────────────────────┐
│ HTTPS/TLS (Nginx - TLS 1.2/1.3)       │
├─────────────────────────────────────────┤
│ Authentication (Flask-Login + bcrypt)   │
├─────────────────────────────────────────┤
│ Authorization (Role-Based Access)       │
├─────────────────────────────────────────┤
│ Data Validation (Input Sanitization)    │
├─────────────────────────────────────────┤
│ SQL Injection Prevention (psycopg3)     │
├─────────────────────────────────────────┤
│ Rate Limiting (Login attempts)          │
├─────────────────────────────────────────┤
│ Activity Logging (All user actions)     │
└─────────────────────────────────────────┘
```

### Features
- **SSL/TLS encryption** (nginx with strong ciphers)
- **HSTS headers** (force HTTPS, 1 year max-age)
- **X-Frame-Options** (prevent clickjacking, DENY)
- **CSP headers** (Content Security Policy)
- **Role-based access control** (user/admin levels)
- **Input validation** on all endpoints
- **Parameterized SQL queries** (psycopg3 - no injection)
- **Session security** (HTTP-only cookies, secure flag)
- **Rate limiting** (20 failed login attempts per 15 minutes)
- **Activity logging** (IP address, user agent, timestamps)
- **Security event monitoring** (failed logins, suspicious activity)

## 🚀 Deployment Architecture

### Docker Containers

```
docker-compose.yml:
├── nginx (ports 80, 443)
├── webapp (Flask frontend - port 5000)
├── api (Flask REST API - port 8000)
├── database (PostgreSQL 17 + TimescaleDB - port 5432)
├── redis (Redis 7 cache - port 6379)
└── pgadmin (Database admin UI - port 80)
```

### Networking

- **Bridge network**: `docker-project-network`
- **Service discovery**: By container name (webapp, api, database, redis)
- **External ports**: 80 (HTTP), 443 (HTTPS), 5432 (PostgreSQL), 6379 (Redis)
- **Internal ports**: Services communicate via bridge network

### Volume Mounts

- **PostgreSQL data**: `postgres_data:/var/lib/postgresql/data`
- **Redis data**: `redis_data:/data`
- **pgAdmin data**: `pgadmin_data:/var/lib/pgadmin`
- **SSL Certificates**: `./ssl/:/etc/ssl/` (mounted to nginx)
- **Configuration files**: nginx.conf, init.sql, servers.json

### Health Checks

```yaml
database:
  healthcheck: pg_isready -U root -d webapp_db
  interval: 30s
  
redis:
  healthcheck: redis-cli ping
  interval: 30s
```

## 📈 Scalability

### Current Capacity
- **Concurrent Users**: ~50-100 simultaneous users
- **API Requests**: 100+ per minute
- **Database Size**: ~5-10 GB (stock/crypto/weather data)
- **Cache Size**: 256 MB Redis (LRU eviction)
- **Response Times**: 
  - Cached queries: 5-50ms
  - Database queries: 50-200ms
  - SSE streaming: Progressive (real-time)

### Scaling Options
1. **Horizontal Scaling**: 
   - Multiple API instances behind nginx load balancer
   - Read replicas for PostgreSQL
   - Redis cluster for distributed caching

2. **Vertical Scaling**: 
   - Increase container resource limits (CPU, memory)
   - Larger database shared_buffers
   - More Redis memory

3. **Database Optimization**:
   - PostgreSQL replication (master-slave)
   - TimescaleDB compression for old data
   - Partitioning strategies

4. **Caching Strategy**:
   - CDN for static assets
   - Longer TTLs for stable data
   - Cache warming strategies

---

*Last Updated: October 25, 2025*  
*System now uses Flask-based architecture (Blazor/.NET components removed)*  
*For troubleshooting, see [TROUBLESHOOTING.md](../troubleshooting/TROUBLESHOOTING.md)*  
*For quick reference, see [QUICK_REFERENCE.md](../reference/QUICK_REFERENCE.md)*
