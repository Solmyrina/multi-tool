# Financial Data Platform with HTTPS

A comprehensive multi-container Docker application for collecting, storing, and analyzing financial and weather data. Features PostgreSQL database, Flask web application, REST API, cryptocurrency backtesting system with real-time progressive loading, weather data collection, stock market integration, performance monitoring, and HTTPS support via nginx reverse proxy.

## 🌟 Key Features

- **🔐 Secure HTTPS/SSL** - Full encryption with nginx reverse proxy and security headers
- **📊 Cryptocurrency Backtesting** - Test 6 trading strategies against 48+ cryptocurrencies with real-time SSE streaming
- **💹 Stock Market Data** - 20+ years of historical data from NASDAQ/NYSE via Yahoo Finance & Alpha Vantage
- **☁️ Weather Data System** - 10+ years historic data (18,255+ records) + hourly current weather updates
- **⚡ Performance Optimized** - Redis caching, NumPy vectorization, query optimization (250x speed improvement)
- **📈 Real-Time Monitoring** - Comprehensive performance dashboard with system metrics
- **👥 User Management** - Multi-level authentication system with role-based access control
- **🗄️ Database Administration** - pgAdmin4 integration for easy database management
- **🔄 Automated Data Collection** - Scheduled updates for crypto, stocks, and weather data

## 📋 Quick Reference for Developers

- **Architecture**: 6-container Docker application (database, webapp, api, redis, pgadmin, nginx)
- **Database**: PostgreSQL 15 with comprehensive schema for users, stocks, weather, crypto
- **Webapp**: Flask application (4,655+ lines) handling authentication and web interface
- **API**: Flask-RESTful (951+ lines) providing REST endpoints for all data services
- **Caching**: Redis for query optimization and backtest result caching
- **Data Sources**: Binance API (crypto), Yahoo Finance (stocks), yr.no & FMI (weather)
- **Security**: Role-based access control, session management, activity logging

## Project Structure

```
docker-project/
├── database/              # PostgreSQL container
│   ├── Dockerfile
│   ├── init.sql          # Main database initialization
│   ├── add_stock_tables.sql
│   ├── add_weather_tables.sql
│   ├── add_current_weather_tables.sql
│   ├── add_historic_weather_tables.sql
│   ├── add_performance_monitoring_tables.sql
│   ├── security_features_schema.sql
│   └── upgrade_user_levels.sql
├── webapp/               # Flask web application (4,655+ lines)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app.py           # Main application with authentication
│   ├── performance_monitor.py
│   ├── .env
│   ├── templates/       # HTML templates (40+ files)
│   │   ├── crypto_backtest.html  # Backtesting interface with SSE
│   │   ├── dashboard.html
│   │   ├── performance_dashboard.html
│   │   └── ...
│   └── static/          # CSS, JS, assets
├── api/                  # REST API container (951+ lines)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── api.py           # Main API with Flask-RESTful
│   ├── stock_service.py # Stock market data service
│   ├── crypto_backtest_service.py  # Backtesting engine
│   ├── streaming_backtest_service.py  # SSE streaming
│   ├── collect_crypto_data.py
│   ├── collect_current_weather.py
│   ├── collect_historic_weather.py
│   ├── fetch_historic_weather.py
│   ├── add_popular_nasdaq_stocks.py
│   ├── add_nasdaq_200_complete.py
│   └── .env
├── nginx/                # Nginx reverse proxy
│   └── nginx.conf       # SSL/HTTPS + SSE configuration
├── ssl/                  # SSL certificates
│   ├── server.crt       # SSL certificate
│   └── server.key       # SSL private key
├── pgadmin/             # pgAdmin4 configuration
│   └── servers.json     # Pre-configured database connection
├── docs/                # Documentation (33 files, 440KB)
│   ├── README.md        # This file
│   ├── INDEX.md         # Documentation index
│   ├── RECENT_UPDATES.md
│   └── ...
├── generate-ssl.sh      # SSL certificate generation script
├── docker-compose.yml   # Container orchestration
└── cookies.txt          # API authentication
```

### Key File Statistics:
- **webapp/app.py**: 4,655 lines - Main web application
- **api/api.py**: 951 lines - REST API service
- **Templates**: 40+ HTML files with interactive UI
- **Documentation**: 33 files totaling 440KB
- **Database Scripts**: 10+ SQL initialization/migration files

## Services

### 1. Nginx Reverse Proxy (HTTPS/SSL Termination)
- **HTTP Port**: 80 (redirects to HTTPS)
- **HTTPS Port**: 443
- **Features**:
  - SSL/TLS encryption for all traffic
  - Automatic HTTP to HTTPS redirects
  - Security headers (HSTS, X-Frame-Options, etc.)
  - Reverse proxy for all backend services
  - Server-Sent Events (SSE) support for real-time streaming
  - Self-signed SSL certificates for development

### 2. Database Container (PostgreSQL)
- **Internal Port**: 5432
- **User**: root
- **Password**: 530NWC0Gm3pt4O
- **Database**: webapp_db
- **Features**:
  - User authentication and multi-level access control
  - Cryptocurrency price data (48+ cryptocurrencies)
  - Historic and current weather data
  - Stock market data (NASDAQ)
  - Performance monitoring metrics
  - Optimized indexes for fast queries
  - Login attempt logging
  - Session management

### 3. Web Application Container (Flask)
- **Internal Port**: 5000 (proxied through nginx)
- **Features**:
  - **User Management**:
    - Registration and login system
    - Secure password hashing (bcrypt)
    - Session management with Flask-Login
    - Multi-level user access (Normal, Privileged, Admin)
    - Profile management and password reset
  - **Cryptocurrency Backtesting**:
    - 6 trading strategies (RSI, Moving Average, Price Momentum, Bollinger Bands, Mean Reversion, Support/Resistance)
    - Test against 48+ cryptocurrencies
    - Progressive loading with Server-Sent Events (SSE)
    - Real-time backtest results streaming
    - Interactive charts with buy/sell markers
    - Detailed performance metrics and comparisons
    - CSV export functionality
  - **Performance Monitoring**:
    - Real-time system metrics dashboard
    - Query performance tracking
    - Database statistics and health monitoring
  - **Weather Dashboard**:
    - Current and historic weather data visualization
    - Multiple location support

### 4. API Container (Flask-RESTful)
- **Internal Port**: 8000 (accessible via /api/ path)
- **Features**:
  - **Cryptocurrency API**:
    - `/api/crypto/` - List all cryptocurrencies
    - `/api/crypto/with-data` - Cryptocurrencies with sufficient data
    - `/api/crypto/strategies` - Available trading strategies
    - `/api/crypto/backtest/run` - Run single backtest
    - `/api/crypto/backtest/run-all` - Batch backtest execution
    - `/api/crypto/backtest/stream` - Real-time SSE streaming
  - **Weather API**:
    - Current weather data collection
    - Historic weather data fetching
    - Automated weather updates
  - **Stock Market API**:
    - NASDAQ stock data fetching
    - Real-time price updates
  - **Performance API**:
    - System metrics and statistics
    - Database performance monitoring
  - **Security API**:
    - User authentication endpoints
    - Session management
  - Health check endpoints
  - Database connectivity

### 5. Redis Container (Caching)
- **Internal Port**: 6379
- **Features**:
  - Query result caching
  - Cryptocurrency backtest caching
  - Automatic cache invalidation
  - Significant performance improvements (3-5x speedup)

### 6. pgAdmin4 Container (Database Administration)
- **Internal Port**: 80 (accessible via /pgadmin/ path)
- **Features**:
  - Full PostgreSQL database administration
  - Pre-configured connection to webapp database
  - Admin-only access through web interface
  - Query editor and visual database tools
  - User management and permissions

## �️ Database Schema

### Core Tables Overview:

#### User Management System:
- **users** - User accounts with authentication (bcrypt password hashing)
- **user_levels** - Role-based permission system (Normal, Privileged, Admin)
- **user_activity_logs** - Security monitoring and activity tracking
- **security_settings** - Per-user security configuration

#### Weather Data System:
- **weather_locations** - Geographic locations for weather data collection
- **current_weather** - Hourly weather updates from yr.no API
- **historic_weather** - 10+ years of daily historical weather (18,255+ records)
- **weather_data_sources** - API source tracking and rate limiting

#### Stock Market System:
- **stocks** - Stock symbols and company information
- **stock_prices** - Historical OHLCV data with multiple intervals (1m, 1h, 1d, 1w, 1M)
- **stock_data_sources** - Data source management (Yahoo Finance, Alpha Vantage)
- **stock_fetch_logs** - Collection monitoring and error tracking

#### Cryptocurrency System:
- **cryptocurrencies** - Cryptocurrency metadata (48+ coins)
- **crypto_prices** - 5+ years of historical price data from Binance API
- **crypto_data_sources** - API configuration and rate limiting
- **crypto_fetch_logs** - Collection monitoring and performance tracking
- **crypto_market_stats** - Market statistics and rankings

#### Performance & Monitoring:
- **performance_metrics** - System performance tracking and query optimization
- **system_logs** - Application-wide logging and error tracking

### Database Features:
- ✅ **Comprehensive Indexing** - Optimized for high-performance queries
- ✅ **Foreign Key Constraints** - Data integrity and referential consistency
- ✅ **Timestamp Tracking** - All data points include collection timestamps
- ✅ **Rate Limiting** - Built-in API quota management
- ✅ **Multi-Interval Support** - 1m, 1h, 1d, 1w, 1M data granularity

### Data Volume Statistics:
- **Weather Data**: 18,255+ historic records, hourly current updates
- **Cryptocurrency Data**: 5+ years of hourly OHLCV for 48+ coins
- **Stock Market Data**: 20+ years of historical data, multiple intervals
- **User Activity**: Comprehensive audit trail with all actions logged

## �📊 Cryptocurrency Backtesting System

Test trading strategies against 48+ cryptocurrencies with real historical data:

### Available Strategies:
1. **RSI Buy/Sell** - Relative Strength Index momentum indicator
2. **Moving Average Crossover** - Short/long MA trend following
3. **Price Momentum** - Percentage change threshold strategy
4. **Bollinger Bands** - Volatility-based trading bands
5. **Mean Reversion** - Statistical return to average pricing
6. **Support/Resistance** - Price level breakout detection

### Features:
- **Real-Time Streaming** - Progressive loading with SSE for instant feedback
- **Comprehensive Metrics**:
  - Total Return (strategy performance)
  - Buy & Hold comparison
  - Win/Loss trade ratios
  - Maximum drawdown analysis
  - Profit/loss tracking
  - Trade execution details
- **Interactive Visualization**:
  - Price charts with buy/sell markers
  - Portfolio value over time
  - Trade history timeline
- **Batch Testing** - Run strategy against all cryptos simultaneously
- **Export Results** - Download to CSV for external analysis

### Supported Cryptocurrencies:
Bitcoin, Ethereum, Cardano, Dogecoin, Litecoin, Bitcoin Cash, Chainlink, Polkadot, Stellar, VeChain, TRON, Cosmos, Tezos, Monero, EOS, Dash, Zcash, Ethereum Classic, NEO, Maker, Ontology, Filecoin, Axie Infinity, Elrond, Crypto.com Coin, THORChain, Algorand, Decentraland, The Sandbox, Zilliqa, Basic Attention Token, Enjin Coin, 0x Protocol, OMG Network, Sushi, 1inch, Curve DAO, Bancor, and more...

## Quick Start

1. **Generate SSL certificates**:
   ```bash
   ./generate-ssl.sh
   ```

2. **Build and start all containers**:
   ```bash
   docker-compose up --build -d
   ```

3. **Access the services** (HTTPS):
   - **Web Application**: https://localhost/ or https://your-server-ip/
   - **Crypto Backtesting**: https://localhost/crypto_backtest
   - **Performance Dashboard**: https://localhost/performance
   - **Weather Dashboard**: https://localhost/weather
   - **API**: https://localhost/api/
   - **pgAdmin4**: https://localhost/pgadmin/

4. **Default Login**:
   - **Web App**: Username: `admin`, Password: `admin123`
   - **pgAdmin4**: Email: `admin@dockerproject.com`, Password: `530NWC0Gm3pt4O`

5. **Test Backtesting**:
   - Login to web app
   - Navigate to "Crypto Backtesting"
   - Select a strategy (e.g., "Price Momentum")
   - Configure parameters
   - Click "Run All Backtests" to see real-time streaming results

## HTTPS Security Features

- **SSL/TLS Encryption**: All traffic encrypted with SSL certificates
- **HSTS**: HTTP Strict Transport Security headers
- **Security Headers**: X-Frame-Options, X-Content-Type-Options, X-XSS-Protection
- **HTTP Redirects**: Automatic redirect from HTTP to HTTPS
- **Modern Ciphers**: TLS 1.2 and 1.3 support with secure cipher suites
- **CSP Headers**: Content Security Policy for XSS protection

## API Endpoints

Access via HTTPS at `https://your-server/api/`:

### General Endpoints
- `GET /api/` - API information
- `GET /api/health` - Health check for all services
- `GET /api/stats/users` - User statistics
- `GET /api/info/database` - Database information

### Cryptocurrency Endpoints
- `GET /api/crypto/` - List all cryptocurrencies
- `GET /api/crypto/with-data` - Cryptocurrencies with sufficient historical data
- `GET /api/crypto/strategies` - List available trading strategies
- `POST /api/crypto/backtest/run` - Run backtest for single crypto
  - Body: `{"crypto_id": 1, "strategy_id": 1, "param1": value, ...}`
- `POST /api/crypto/backtest/run-all` - Run backtest against all cryptos
  - Body: `{"strategy_id": 1, "param1": value, ...}`
- `POST /api/crypto/backtest/stream` - Real-time streaming backtest (SSE)
  - Body: `{"strategy_id": 1, "param1": value, ...}`
  - Returns: Server-Sent Events stream with progressive results

### Weather Endpoints
- `GET /api/weather/current` - Current weather data
- `GET /api/weather/historic` - Historic weather data
- `POST /api/weather/collect` - Trigger weather data collection

### Performance Endpoints
- `GET /api/performance/metrics` - System performance metrics
- `GET /api/performance/database` - Database statistics

### Security Endpoints
- `POST /api/security/login` - User authentication
- `POST /api/security/logout` - Session termination
- `GET /api/security/session` - Session validation

## 🔄 Automated Data Collection Systems

### Weather Data Collection:

#### Historic Weather System:
- **Files**: `api/collect_historic_weather.py`, `api/fetch_historic_weather.py`
- **Purpose**: Collect 10+ years of daily weather data
- **Source**: FMI (Finnish Meteorological Institute)
- **Coverage**: Multiple Finnish cities (Helsinki, Tampere, Turku, Oulu, etc.)
- **Data Points**: Temperature, precipitation, wind speed, humidity
- **Status**: 18,255+ records collected and stored
- **Automation**: `setup_weather_automation.sh` for scheduled updates

#### Current Weather System:
- **Files**: `api/collect_current_weather.py`
- **Purpose**: Hourly weather updates for monitored locations
- **Source**: yr.no API (Norwegian Meteorological Institute)
- **Frequency**: Every hour via cron job
- **Data**: Real-time weather conditions, forecasts
- **Logging**: `current_weather.log` for monitoring

### Stock Market Data Collection:

#### Data Sources:
1. **Yahoo Finance API** (Primary)
   - 20+ years of historical stock data
   - Multiple intervals: 1m, 1h, 1d, 1w, 1M
   - Global stock market support (NASDAQ, NYSE, etc.)
   - Conservative rate limiting for API stability

2. **Alpha Vantage API** (Backup)
   - API key required for enhanced limits
   - Configuration via .env file: `ALPHA_VANTAGE_API_KEY`
   - Automatic fallback when Yahoo Finance fails

#### Collection Scripts:
- **`add_popular_nasdaq_stocks.py`** - Top 50 NASDAQ stocks by volume
- **`add_nasdaq_200_complete.py`** - Top 200 NASDAQ companies
- **`add_top_nasdaq_stocks.py`** - Complete NASDAQ collection
- **`fetch_real_nasdaq_data.py`** - NASDAQ Composite Index data

#### Features:
- ✅ **Scheduled Updates** - Daily market data refresh
- ✅ **Error Handling** - Robust retry logic with exponential backoff
- ✅ **Progress Tracking** - Resume interrupted collections
- ✅ **Data Validation** - Ensure data quality and completeness

### Cryptocurrency Data Collection:

#### Binance API Integration:
- **Primary Service**: `crypto_service.py`
- **Data Source**: Binance REST API (Public + Authenticated)
- **Coverage**: Top 200 cryptocurrencies by trading volume
- **Historical Data**: 5+ years of hourly OHLCV (Open, High, Low, Close, Volume)
- **Rate Limits**:
  - Public API: 1,200 requests/minute
  - With API key: 6,000 requests/minute (5x faster)

#### Collection Process:
- **Main Collection**: `api/collect_crypto_data.py`
  - Progress tracking and resume capability
  - Intelligent rate limiting and error handling
  - Automatic retry logic with exponential backoff
  - Status monitoring and comprehensive logging

- **Update Process**: Daily market data refresh
  - Latest price updates for all tracked cryptocurrencies
  - Market statistics and ranking updates
  - Volume and market cap calculations

#### Performance Optimization:
- ✅ **API Key Support** - 5x faster collection with Binance credentials
- ✅ **Rate Limiting** - Intelligent request spacing to avoid bans
- ✅ **Batch Processing** - Efficient bulk database insertions
- ✅ **Error Recovery** - Automatic retry with exponential backoff

### Automation & Scheduling:

```bash
# Weather Data - Hourly updates
0 * * * * /path/to/collect_current_weather.py

# Stock Market - Daily after market close
0 22 * * 1-5 /path/to/update_stock_data.sh

# Cryptocurrency - Continuous updates
*/15 * * * * /path/to/update_crypto_prices.py
```

## SSL Certificate Management

### Development (Self-Signed Certificates)
The included `generate-ssl.sh` script creates self-signed certificates for development:
```bash
./generate-ssl.sh
```

### Production (Proper SSL Certificates)
For production, replace the self-signed certificates with proper SSL certificates:

1. **Let's Encrypt (Free)**:
   ```bash
   # Install certbot
   sudo apt install certbot
   
   # Generate certificates
   sudo certbot certonly --standalone -d your-domain.com
   
   # Copy certificates
   sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ./ssl/server.crt
   sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ./ssl/server.key
   ```

2. **Commercial Certificate**:
   - Purchase SSL certificate from a CA
   - Copy certificate to `./ssl/server.crt`
   - Copy private key to `./ssl/server.key`

3. **Restart containers** after updating certificates:
   ```bash
   docker-compose restart nginx
   ```

## 🆕 What's New (October 2025)

### Progressive Loading (Phase 8)
- ✨ **Server-Sent Events (SSE)** - Real-time streaming of backtest results
- ✨ **250x Speed Improvement** - First result in 0.1s instead of 25s
- ✨ **Live Progress Tracking** - Real-time stats and completion percentage
- ✨ **Auto-Hide UI** - Progressive panel fades when complete

### UI/UX Enhancements
- 🎨 **Unified Colors** - Consistent green/red across all columns
- 🎨 **Win/Loss Display** - Clear trade success visualization
- 🎨 **Summary Metrics** - Total win/loss trades in backtest summary
- 🎨 **Better Formatting** - + signs for positive values, bold colors

### Performance Optimizations
- ⚡ **NumPy Vectorization** - 1.5x faster calculations
- ⚡ **Redis Caching** - 3-5x speedup with smart invalidation
- ⚡ **Query Optimization** - Database indexes and range filtering
- ⚡ **Parallel Processing** - ThreadPoolExecutor for concurrent execution

### Documentation
- 📚 **Organized Docs** - All documentation moved to `docs/` folder
- 📚 **Documentation Index** - Categorized guide with 32+ documents
- 📚 **User Guides** - Comprehensive backtesting and system documentation

## 🛠️ Technology Stack

### Backend
- **Python 3.11** - Core programming language
- **Flask** - Web framework and API
- **PostgreSQL** - Relational database
- **Redis** - In-memory caching
- **NumPy** - Numerical computations
- **Pandas** - Data analysis
- **psycopg2** - PostgreSQL adapter
- **Flask-Login** - User session management
- **bcrypt** - Password hashing

### Frontend
- **HTML5/CSS3** - Modern web standards
- **JavaScript (ES6+)** - Client-side interactivity
- **Bootstrap 5** - Responsive UI framework
- **Chart.js** - Interactive data visualization
- **Font Awesome** - Icon library
- **jQuery** - DOM manipulation

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Nginx** - Reverse proxy and SSL termination
- **SSL/TLS** - HTTPS encryption

### Data Sources
- **Binance API** - Cryptocurrency historical data
- **OpenWeather API** - Weather data collection
- **Yahoo Finance** - Stock market data

## Environment Variables

### Database
- `POSTGRES_USER`: root
- `POSTGRES_PASSWORD`: 530NWC0Gm3pt4O
- `POSTGRES_DB`: webapp_db

### Web Application
- `SECRET_KEY`: Flask secret key
- `DB_HOST`: database
- `DB_NAME`: webapp_db
- `DB_USER`: root
- `DB_PASSWORD`: 530NWC0Gm3pt4O
- `REDIS_HOST`: redis
- `REDIS_PORT`: 6379

### API
- `DB_HOST`: database
- `DB_NAME`: webapp_db
- `DB_USER`: root
- `DB_PASSWORD`: 530NWC0Gm3pt4O
- `REDIS_HOST`: redis
- `REDIS_PORT`: 6379
- `WEBAPP_HOST`: webapp
- `WEBAPP_PORT`: 5000

### Redis
- `REDIS_PASSWORD`: (optional)
- `MAXMEMORY`: 256mb
- `MAXMEMORY_POLICY`: allkeys-lru

### pgAdmin4
- `PGADMIN_DEFAULT_EMAIL`: admin@dockerproject.com
- `PGADMIN_DEFAULT_PASSWORD`: 530NWC0Gm3pt4O
- **Pre-configured server**: Docker Project Database

## 🚀 Performance Optimizations

The system has undergone extensive performance optimization, achieving **250x speed improvement**:

### Phase 1-2: Query & Database Optimization
- ✅ **Date Range Filtering** - Reduced data processing by 99.8%
- ✅ **Redis Caching** - 3-5x speedup with intelligent cache invalidation
- ✅ **Database Indexes** - Optimized queries with proper indexing
- ✅ **Query Optimization** - Reduced unnecessary data fetching

### Phase 3: Algorithm Optimization
- ✅ **NumPy Vectorization** - 1.5x faster calculations
- ✅ **Parallel Processing** - ThreadPoolExecutor for concurrent backtests

### Phase 4: Progressive Loading (SSE)
- ✅ **Server-Sent Events** - Real-time result streaming
- ✅ **250x Perceived Speed** - First result in 0.1s (was 25s)
- ✅ **Progressive UI** - Live updates, stats, and progress tracking
- ✅ **Parallel Execution** - 48 backtests complete in 3-5 seconds

### Results:
- **Before**: 25 seconds to start seeing results
- **After**: 0.1 seconds for first result, 3-5 seconds for all 48
- **Total Improvement**: 250x faster perceived performance

## 🎨 Recent UI/UX Improvements

- **Color-Coded Results** - Green/red for positive/negative returns across all columns
- **Win/Loss Display** - Clear visualization of profitable vs losing trades
- **Progressive Loading Panel** - Real-time streaming with auto-hide on completion
- **Sortable Tables** - Click headers to sort by any column
- **Export to CSV** - Download backtest results for further analysis
- **Responsive Design** - Works on desktop, tablet, and mobile
- **Interactive Charts** - Hover tooltips, buy/sell markers, portfolio value tracking

## 🔒 Security Features

- **SSL/TLS Encryption** - All traffic encrypted with HTTPS
- **Password Security** - Bcrypt hashing with salt
- **Login Monitoring** - Attempt logging and rate limiting
- **Session Management** - Secure Flask-Login sessions
- **Multi-Level Access** - Role-based permissions (Normal, Privileged, Admin)
- **CORS Protection** - Configured for API security
- **Database Security** - Connection pooling and prepared statements
- **Input Validation** - Sanitization and validation on all inputs
- **Security Headers** - HSTS, CSP, X-Frame-Options, etc.

## Development

To run in development mode with live reload:

```bash
# Start only the database
docker-compose up database

# Run web app locally
cd webapp
pip install -r requirements.txt
python app.py

# Run API locally  
cd api
pip install -r requirements.txt
python api.py
```

## 🚀 Production Deployment

### Pre-Deployment Checklist:

1. **Security Configuration**:
   ```bash
   # Change all default passwords
   # Update in docker-compose.yml and .env files
   - Database password
   - pgAdmin password
   - Flask secret key
   - Redis password (optional)
   ```

2. **SSL/TLS Certificates**:
   ```bash
   # Replace self-signed certificates with proper SSL
   # See SSL Certificate Management section
   ```

3. **Environment Configuration**:
   ```bash
   # Update production environment variables
   - Set DEBUG=False
   - Configure production database
   - Set proper CORS origins
   - Configure logging levels
   ```

4. **Resource Limits**:
   ```yaml
   # Add to docker-compose.yml
   services:
     database:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 4G
     redis:
       deploy:
         resources:
           limits:
             memory: 512M
   ```

5. **Monitoring & Logging**:
   ```bash
   # Set up log aggregation
   - Configure centralized logging
   - Set up alerting
   - Monitor resource usage
   ```

6. **Backups**:
   ```bash
   # Configure automated database backups
   docker-compose exec database pg_dump -U root webapp_db > backup.sql
   
   # Schedule with cron
   0 2 * * * /path/to/backup.sh
   ```

7. **Performance Tuning**:
   ```bash
   # Optimize PostgreSQL
   - Adjust shared_buffers
   - Configure work_mem
   - Tune connection pool
   
   # Optimize Redis
   - Set appropriate maxmemory
   - Configure eviction policy
   ```

## 🔮 Future Enhancements

### Planned Features:
- [ ] **TimescaleDB Integration** - Time-series optimization for crypto data
- [ ] **Machine Learning Models** - AI-powered trading strategy predictions
- [ ] **Real-Time Trading** - Live cryptocurrency trading integration
- [ ] **Portfolio Management** - Track multiple crypto portfolios
- [ ] **Alert System** - Price alerts and strategy notifications
- [ ] **Mobile App** - Native iOS/Android applications
- [ ] **WebSocket Support** - Real-time price updates
- [ ] **Multi-Exchange Support** - Binance, Coinbase, Kraken, etc.
- [ ] **Social Features** - Share strategies and results
- [ ] **Advanced Charting** - TradingView integration

### Optimization Opportunities:
- [ ] **Database Partitioning** - Partition crypto price tables by date
- [ ] **CDN Integration** - Static asset delivery optimization
- [ ] **GraphQL API** - More flexible API queries
- [ ] **Microservices** - Split services for better scalability
- [ ] **Kubernetes** - Container orchestration for production

## 📄 License

This project is proprietary software. All rights reserved.

## 🤝 Contributing

This is a private project. For questions or issues, contact the project maintainer.

## 📧 Support

For technical support or questions:
- Check the [documentation](docs/INDEX.md)
- Review [troubleshooting](#-troubleshooting) section
- Contact system administrator

## 🙏 Acknowledgments

- **Binance** - Cryptocurrency data API
- **OpenWeather** - Weather data API
- **Yahoo Finance** - Stock market data
- **Docker Community** - Containerization platform
- **Flask Community** - Web framework
- **PostgreSQL Team** - Database system
- **Redis Labs** - Caching solution

## �‍💻 Development Guidelines

### Adding New Data Sources:

#### Step 1: Database Schema
```sql
-- Create new tables in database/add_new_data_source.sql
CREATE TABLE new_data_source (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    api_endpoint VARCHAR(255),
    last_fetch TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes for performance
CREATE INDEX idx_new_data_source_status ON new_data_source(status);
CREATE INDEX idx_new_data_source_last_fetch ON new_data_source(last_fetch);
```

#### Step 2: Service Implementation
```python
# Create service file: api/new_data_service.py
class NewDataService:
    """Service for collecting and managing new data source"""
    
    def __init__(self, db_config=None):
        self.db_config = db_config or get_db_config()
        self.logger = setup_logger('new_data_service')
        
    def fetch_data(self, params):
        """Fetch data from external API"""
        try:
            # Implement API call with rate limiting
            response = self._make_api_call(params)
            return self._process_response(response)
        except Exception as e:
            self.logger.error(f"Error fetching data: {e}")
            raise
            
    def store_data(self, data):
        """Store data in database with validation"""
        conn = psycopg2.connect(**self.db_config)
        try:
            with conn.cursor() as cur:
                # Validate and insert data
                self._validate_data(data)
                cur.execute("""
                    INSERT INTO new_data_source (name, api_endpoint, status)
                    VALUES (%s, %s, %s)
                """, (data['name'], data['endpoint'], 'active'))
            conn.commit()
        finally:
            conn.close()
```

#### Step 3: API Endpoints
```python
# Add to api/api.py
from flask_restful import Resource
from new_data_service import NewDataService

class NewDataEndpoint(Resource):
    def __init__(self):
        self.service = NewDataService()
        
    def get(self):
        """Get data from new source"""
        try:
            data = self.service.fetch_data({})
            return {'success': True, 'data': data}
        except Exception as e:
            return {'error': str(e)}, 500
            
    def post(self):
        """Trigger data collection"""
        try:
            result = self.service.collect_and_store()
            return {'success': True, 'result': result}
        except Exception as e:
            return {'error': str(e)}, 500

# Register endpoint
api.add_resource(NewDataEndpoint, '/new-data', '/new-data/collect')
```

#### Step 4: Web Interface
```python
# Add route to webapp/app.py
@app.route('/new-data')
@login_required
@privilege_required('normal')  # Or 'privileged'/'admin'
def new_data_dashboard():
    """Display new data dashboard"""
    try:
        # Fetch data for display
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM new_data_source ORDER BY created_at DESC LIMIT 100")
        data = cur.fetchall()
        return render_template('new_data.html', data=data)
    except Exception as e:
        logger.error(f"Error in new data dashboard: {e}")
        flash('Error loading data', 'error')
        return redirect(url_for('dashboard'))
```

### Database Migration Best Practices:

#### Creating Migrations:
```bash
# 1. Create migration file with timestamp
touch database/migrate_$(date +%Y%m%d_%H%M%S)_add_new_feature.sql

# 2. Write forward migration
ALTER TABLE users ADD COLUMN new_field VARCHAR(100);
CREATE INDEX idx_users_new_field ON users(new_field);

# 3. Test in development
docker exec -it docker-project_database_1 psql -U root webapp_db -f /path/to/migration.sql

# 4. Backup before production
docker exec docker-project_database_1 pg_dump -U root webapp_db > backup_before_migration.sql
```

#### Rollback Strategy:
```sql
-- Always include rollback statements
-- ROLLBACK:
-- ALTER TABLE users DROP COLUMN new_field;
-- DROP INDEX IF EXISTS idx_users_new_field;
```

### API Development Standards:

#### Error Handling Pattern:
```python
from functools import wraps

def handle_errors(f):
    """Decorator for consistent error handling"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            return {'error': 'Invalid input', 'message': str(e)}, 400
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {e}")
            return {'error': 'Internal server error'}, 500
    return wrapper

@handle_errors
def my_endpoint():
    # Your endpoint logic
    pass
```

#### Rate Limiting Implementation:
```python
import time
from datetime import datetime, timedelta

class RateLimiter:
    """Rate limiting for API calls"""
    
    def __init__(self, max_requests, time_window):
        self.max_requests = max_requests
        self.time_window = time_window  # seconds
        self.requests = []
        
    def allow_request(self):
        """Check if request is allowed under rate limit"""
        now = datetime.now()
        # Remove old requests outside time window
        self.requests = [r for r in self.requests 
                        if now - r < timedelta(seconds=self.time_window)]
        
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        return False
        
    def wait_if_needed(self):
        """Wait if rate limit exceeded"""
        while not self.allow_request():
            time.sleep(0.1)
```

#### Input Validation:
```python
def validate_input(data, required_fields, optional_fields=None):
    """Validate API input data"""
    # Check required fields
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
            
    # Check for unknown fields
    allowed_fields = set(required_fields)
    if optional_fields:
        allowed_fields.update(optional_fields)
        
    unknown_fields = set(data.keys()) - allowed_fields
    if unknown_fields:
        raise ValueError(f"Unknown fields: {', '.join(unknown_fields)}")
        
    return True
```

### Testing Checklist:

```bash
# Unit Tests
python -m pytest tests/

# Integration Tests
python -m pytest tests/integration/

# API Endpoint Tests
curl -X GET https://localhost/api/health
curl -X POST https://localhost/api/new-endpoint -d '{"test": "data"}'

# Database Connection Test
docker exec -it docker-project_database_1 psql -U root webapp_db -c "SELECT COUNT(*) FROM users;"

# Performance Test
time curl -X GET https://localhost/api/crypto/prices?limit=1000
```

## �📚 Documentation

For detailed documentation, see the [`docs/`](.) folder:

- **[INDEX.md](INDEX.md)** - Complete documentation index
- **[BACKTESTING_USER_GUIDE.md](BACKTESTING_USER_GUIDE.md)** - How to use the backtesting system
- **[DATABASE_ACCESS_GUIDE.md](DATABASE_ACCESS_GUIDE.md)** - Database configuration
- **[PERFORMANCE_OPTIMIZATION_ROADMAP.md](PERFORMANCE_OPTIMIZATION_ROADMAP.md)** - Complete optimization journey
- **[WEATHER_SYSTEM_README.md](WEATHER_SYSTEM_README.md)** - Weather data system
- **[SYSTEM_STATUS.md](SYSTEM_STATUS.md)** - Current system status

### Optimization Documentation:
- [OPTIMIZATION_8_PROGRESSIVE_LOADING_COMPLETE.md](OPTIMIZATION_8_PROGRESSIVE_LOADING_COMPLETE.md) - SSE streaming implementation
- [OPTIMIZATION_7_NUMPY_VECTORIZATION_COMPLETE.md](OPTIMIZATION_7_NUMPY_VECTORIZATION_COMPLETE.md) - NumPy optimization
- [REDIS_CACHING_COMPLETE.md](REDIS_CACHING_COMPLETE.md) - Redis caching setup
- [QUERY_OPTIMIZATION_GUIDE.md](QUERY_OPTIMIZATION_GUIDE.md) - Database query optimization

## 🐛 Troubleshooting

- **Database connection issues**: Ensure PostgreSQL container is healthy
  ```bash
  docker-compose ps
  docker-compose logs database
  ```
- **Permission errors**: Check file permissions and Docker daemon
  ```bash
  sudo chown -R $USER:$USER .
  ```
- **Port conflicts**: Ensure ports 80, 443, 5432, 6379 are available
  ```bash
  sudo netstat -tulpn | grep -E ':(80|443|5432|6379)'
  ```
- **Container startup**: Check logs with:
  ```bash
  docker-compose logs [service-name]
  docker-compose logs -f  # Follow logs in real-time
  ```
- **Redis connection**: Verify Redis is running
  ```bash
  docker-compose exec redis redis-cli ping
  # Should return: PONG
  ```
- **Backtest performance**: Clear Redis cache if results seem stale
  ```bash
  docker-compose exec redis redis-cli FLUSHDB
  ```

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Internet (HTTPS)                         │
└──────────────────────┬──────────────────────────────────────┘
                       │ Port 443 (HTTPS)
                       │ Port 80 (HTTP → HTTPS redirect)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Nginx Reverse Proxy                         │
│  • SSL/TLS Termination                                       │
│  • Load Balancing                                            │
│  • SSE Streaming Support                                     │
└─────┬────────┬────────┬────────┬──────────┬─────────────────┘
      │        │        │        │          │
      ▼        ▼        ▼        ▼          ▼
┌─────────┐ ┌─────┐ ┌────────┐ ┌──────┐ ┌────────┐
│ Webapp  │ │ API │ │pgAdmin │ │Redis │ │Database│
│ :5000   │ │:8000│ │  :80   │ │:6379 │ │ :5432  │
└─────────┘ └─────┘ └────────┘ └──────┘ └────────┘
     │         │         │         │         │
     └─────────┴─────────┴─────────┴─────────┘
              docker-project-network
```

### Data Flow:
1. **Client** → Nginx (HTTPS)
2. **Nginx** → Routes to webapp/api/pgadmin
3. **Webapp/API** ↔ Database (PostgreSQL)
4. **API** ↔ Redis (Caching)
5. **API** → SSE Stream → Client (Real-time updates)

## 🌐 Container Network

All containers communicate through the `docker-project-network` bridge network:

- **Nginx** ↔ Webapp, API, pgAdmin (Reverse proxy)
- **Webapp** ↔ Database (User data, backtest results)
- **API** ↔ Database (Crypto data, weather data, stocks)
- **API** ↔ Redis (Query caching, backtest caching)
- **API** ↔ Webapp (SSE streaming, API calls)
- **pgAdmin** ↔ Database (Administration)

### Service Discovery:
Containers use Docker's internal DNS for service discovery:
- Database: `database:5432`
- Redis: `redis:6379`
- Webapp: `webapp:5000`
- API: `api:8000`