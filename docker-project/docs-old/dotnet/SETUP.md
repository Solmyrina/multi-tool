# .NET 10 Crypto Backtester - Setup Guide

Complete installation and configuration guide for the .NET 10 integration.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Project Creation](#project-creation)
4. [Dependency Installation](#dependency-installation)
5. [Database Configuration](#database-configuration)
6. [Docker Configuration](#docker-configuration)
7. [Nginx Configuration](#nginx-configuration)
8. [Build and Deploy](#build-and-deploy)
9. [Verification](#verification)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

**Operating System:**
- ✅ Ubuntu 20.04+ (recommended)
- ✅ Debian 11+
- ✅ Other Linux distributions with Docker support

**Software Requirements:**
- ✅ Docker 28.4.0+
- ✅ Docker Compose 2.39.2+
- ✅ .NET 10 SDK (for local development)
- ✅ Git

**Hardware Requirements:**
- CPU: 4+ cores recommended
- RAM: 8GB minimum, 16GB recommended
- Disk: 20GB free space

### Verify Prerequisites

```bash
# Check Docker version
docker --version
# Expected: Docker version 28.4.0 or higher

# Check Docker Compose version
docker compose version
# Expected: Docker Compose version 2.39.2 or higher

# Check existing containers
docker ps
# Ensure database, redis, nginx are running

# Check .NET SDK (optional, for local dev)
dotnet --version
# Expected: 10.0.0 or higher
```

### Install .NET 10 SDK (Optional)

**For local development only (not required for Docker deployment):**

```bash
# Download and install .NET 10 SDK
wget https://dot.net/v1/dotnet-install.sh
chmod +x dotnet-install.sh
./dotnet-install.sh --channel 10.0

# Add to PATH
echo 'export PATH="$HOME/.dotnet:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Verify installation
dotnet --version
```

---

## Environment Setup

### 1. Navigate to Project Directory

```bash
cd /home/one_control/docker-project
```

### 2. Verify Existing Services

```bash
# Check that Python services are running
docker ps | grep -E "webapp|api|database|redis"

# Expected output:
# docker-project-webapp-1
# docker-project-api-1
# docker-project-database-1
# docker-project-redis-1
# docker-project-nginx-1
```

### 3. Check Database Connection

```bash
# Test database connectivity
docker exec docker-project-database-1 psql -U root -d webapp_db -c "SELECT COUNT(*) FROM cryptocurrencies;"

# Should return count of cryptocurrencies
```

---

## Project Creation

### 1. Create Data API Project

```bash
# Create directory
mkdir -p dotnet-data-api
cd dotnet-data-api

# Create new Web API project
dotnet new webapi -n DotnetDataApi -f net10.0 --use-minimal-apis

# Navigate into project
cd DotnetDataApi

# Remove template files
rm WeatherForecast.cs

# Return to root
cd ../..
```

### 2. Create Blazor Web Project

```bash
# Create directory
mkdir -p dotnet-web
cd dotnet-web

# Create new Blazor Server project
dotnet new blazor -n DotnetWeb -f net10.0 --interactivity Server --all-interactive

# Navigate into project
cd DotnetWeb

# Remove template files
rm -rf Data/
rm Pages/Weather.razor

# Return to root
cd ../..
```

### 3. Verify Project Structure

```bash
# Check directory structure
tree -L 2 dotnet-data-api dotnet-web

# Expected structure:
# dotnet-data-api/
# └── DotnetDataApi/
#     ├── DotnetDataApi.csproj
#     ├── Program.cs
#     ├── appsettings.json
#     └── Properties/
#
# dotnet-web/
# └── DotnetWeb/
#     ├── DotnetWeb.csproj
#     ├── Program.cs
#     ├── App.razor
#     ├── Pages/
#     └── Components/
```

---

## Dependency Installation

### 1. Data API Dependencies

```bash
cd dotnet-data-api/DotnetDataApi

# PostgreSQL driver
dotnet add package Npgsql --version 8.0.5

# Micro-ORM
dotnet add package Dapper --version 2.1.35

# Caching
dotnet add package Microsoft.Extensions.Caching.Memory --version 10.0.0

# Swagger/OpenAPI
dotnet add package Swashbuckle.AspNetCore --version 7.2.0

# Health checks
dotnet add package AspNetCore.HealthChecks.Npgsql --version 10.0.0

# Return to root
cd ../..
```

### 2. Blazor Web Dependencies

```bash
cd dotnet-web/DotnetWeb

# MudBlazor UI components
dotnet add package MudBlazor --version 7.20.0

# Radzen Blazor components (charts)
dotnet add package Radzen.Blazor --version 5.6.8

# HTTP client
dotnet add package Microsoft.Extensions.Http --version 10.0.0

# Return to root
cd ../..
```

### 3. Verify Dependencies

```bash
# Check Data API packages
cat dotnet-data-api/DotnetDataApi/DotnetDataApi.csproj

# Check Blazor Web packages
cat dotnet-web/DotnetWeb/DotnetWeb.csproj
```

---

## Database Configuration

### 1. Verify Database Schema

```bash
# Check that crypto tables exist
docker exec docker-project-database-1 psql -U root -d webapp_db -c "\dt" | grep crypto

# Expected tables:
# crypto_backtest_results
# crypto_data_sources
# crypto_fetch_logs
# crypto_market_stats
# crypto_prices
# crypto_strategies
# crypto_strategy_parameters
# crypto_technical_indicators
# cryptocurrencies
```

### 2. Add .NET Execution Tracking (Optional)

```bash
# Add executed_by column if not exists
docker exec docker-project-database-1 psql -U root -d webapp_db << 'EOF'
ALTER TABLE crypto_backtest_results 
ADD COLUMN IF NOT EXISTS executed_by VARCHAR(50) DEFAULT 'python';

CREATE INDEX IF NOT EXISTS idx_backtest_executed_by 
ON crypto_backtest_results(executed_by);
EOF
```

### 3. Create Connection String Secret

```bash
# Get database password
DB_PASSWORD=$(grep POSTGRES_PASSWORD docker-compose.yml | awk -F: '{print $2}' | tr -d ' "')

# Create connection string (replace *** with actual password)
CONNECTION_STRING="Host=database;Port=5432;Database=webapp_db;Username=root;Password=${DB_PASSWORD};Pooling=true;Minimum Pool Size=5;Maximum Pool Size=100"

echo "Connection String (store securely):"
echo "$CONNECTION_STRING"
```

---

## Docker Configuration

### 1. Create Data API Dockerfile

```bash
cat > dotnet-data-api/Dockerfile << 'EOF'
# Build stage
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src

# Copy project file
COPY DotnetDataApi/*.csproj DotnetDataApi/
RUN dotnet restore DotnetDataApi/DotnetDataApi.csproj

# Copy source code
COPY DotnetDataApi/ DotnetDataApi/

# Build application
WORKDIR /src/DotnetDataApi
RUN dotnet build -c Release -o /app/build

# Publish stage
FROM build AS publish
RUN dotnet publish -c Release -o /app/publish /p:UseAppHost=false

# Runtime stage
FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS final
WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy published application
COPY --from=publish /app/publish .

# Set environment
ENV ASPNETCORE_URLS=http://+:5002
ENV ASPNETCORE_ENVIRONMENT=Production

# Expose port
EXPOSE 5002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:5002/health || exit 1

# Run application
ENTRYPOINT ["dotnet", "DotnetDataApi.dll"]
EOF
```

### 2. Create Blazor Web Dockerfile

```bash
cat > dotnet-web/Dockerfile << 'EOF'
# Build stage
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src

# Copy project file
COPY DotnetWeb/*.csproj DotnetWeb/
RUN dotnet restore DotnetWeb/DotnetWeb.csproj

# Copy source code
COPY DotnetWeb/ DotnetWeb/

# Build application
WORKDIR /src/DotnetWeb
RUN dotnet build -c Release -o /app/build

# Publish stage
FROM build AS publish
RUN dotnet publish -c Release -o /app/publish /p:UseAppHost=false

# Runtime stage
FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS final
WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy published application
COPY --from=publish /app/publish .

# Set environment
ENV ASPNETCORE_URLS=http://+:5001
ENV ASPNETCORE_ENVIRONMENT=Production

# Expose port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:5001/ || exit 1

# Run application
ENTRYPOINT ["dotnet", "DotnetWeb.dll"]
EOF
```

### 3. Create .dockerignore Files

```bash
# Data API .dockerignore
cat > dotnet-data-api/.dockerignore << 'EOF'
**/.dockerignore
**/.git
**/.gitignore
**/.vs
**/.vscode
**/*.*proj.user
**/bin
**/obj
**/node_modules
**/npm-debug.log
**/Dockerfile*
**/docker-compose*
**/.DS_Store
EOF

# Blazor Web .dockerignore
cat > dotnet-web/.dockerignore << 'EOF'
**/.dockerignore
**/.git
**/.gitignore
**/.vs
**/.vscode
**/*.*proj.user
**/bin
**/obj
**/node_modules
**/npm-debug.log
**/Dockerfile*
**/docker-compose*
**/.DS_Store
EOF
```

### 4. Update docker-compose.yml

```bash
# Backup existing docker-compose.yml
cp docker-compose.yml docker-compose.yml.backup

# Add .NET services (append to existing docker-compose.yml)
cat >> docker-compose.yml << 'EOF'

  # .NET Data API
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
      - ConnectionStrings__PostgreSQL=Host=database;Port=5432;Database=webapp_db;Username=root;Password=${POSTGRES_PASSWORD}
      - Redis__Connection=redis:6379
    depends_on:
      database:
        condition: service_healthy
      redis:
        condition: service_started
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5002/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # .NET Blazor Web
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
      dotnet-data-api:
        condition: service_healthy
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5001/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
EOF
```

---

## Nginx Configuration

### 1. Update nginx.conf

```bash
# Backup existing nginx configuration
cp nginx/nginx.conf nginx/nginx.conf.backup

# Add .NET routes to nginx.conf (add after Python routes)
# Edit nginx/nginx.conf and add these location blocks:
```

```nginx
    # .NET Blazor Web App
    location /dotnet/ {
        proxy_pass http://dotnet-web:5001/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }

    # .NET Data API
    location /dotnet-api/ {
        proxy_pass http://dotnet-data-api:5002/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
    }

    # .NET Data API Swagger
    location /dotnet-api/swagger {
        proxy_pass http://dotnet-data-api:5002/swagger;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
```

### 2. Add WebSocket Support (if not exists)

Add to http block in nginx.conf:

```nginx
http {
    # WebSocket support
    map $http_upgrade $connection_upgrade {
        default upgrade;
        '' close;
    }
    
    # ... rest of configuration
}
```

---

## Build and Deploy

### 1. Build Docker Images

```bash
# Build Data API
docker compose build dotnet-data-api

# Expected output:
# => [final 1/1] COPY --from=publish /app/publish .
# => exporting to image
# => => naming to docker.io/library/docker-project-dotnet-data-api

# Build Blazor Web
docker compose build dotnet-web

# Expected output:
# => [final 1/1] COPY --from=publish /app/publish .
# => exporting to image
# => => naming to docker.io/library/docker-project-dotnet-web
```

**Build Time:**
- Data API: ~3-5 minutes (first build)
- Blazor Web: ~3-5 minutes (first build)
- Subsequent builds: ~30-60 seconds (cached layers)

### 2. Start Services

```bash
# Start .NET services
docker compose up -d dotnet-data-api dotnet-web

# Wait for health checks (30-40 seconds)
sleep 40

# Check container status
docker ps | grep dotnet

# Expected output:
# dotnet-data-api    Up 40 seconds (healthy)
# dotnet-web         Up 40 seconds (healthy)
```

### 3. Restart Nginx

```bash
# Reload nginx configuration
docker compose restart nginx

# Or reload without restart
docker exec docker-project-nginx-1 nginx -s reload

# Check nginx status
docker logs docker-project-nginx-1 --tail 20
```

---

## Verification

### 1. Check Container Health

```bash
# Check all containers
docker ps --format "table {{.Names}}\t{{.Status}}"

# Expected output:
# NAMES                         STATUS
# dotnet-web                    Up 2 minutes (healthy)
# dotnet-data-api               Up 2 minutes (healthy)
# docker-project-nginx-1        Up 2 minutes
# docker-project-webapp-1       Up 2 hours
# docker-project-api-1          Up 2 hours
# docker-project-database-1     Up 2 hours (healthy)
# docker-project-redis-1        Up 2 hours
```

### 2. Test Data API Health

```bash
# Test health endpoint
curl http://localhost:5002/health

# Expected output:
# {"status":"Healthy","duration":"00:00:00.0234567"}

# Test via nginx (HTTPS)
curl -k https://localhost/dotnet-api/health

# Expected output:
# {"status":"Healthy","duration":"00:00:00.0234567"}
```

### 3. Test Blazor Web

```bash
# Test direct access
curl -I http://localhost:5001/

# Expected output:
# HTTP/1.1 200 OK
# Content-Type: text/html; charset=utf-8

# Test via nginx (HTTPS)
curl -I -k https://localhost/dotnet/

# Expected output:
# HTTP/2 200
# content-type: text/html; charset=utf-8
```

### 4. Test Database Connectivity

```bash
# Check from Data API container
docker exec dotnet-data-api dotnet --version

# Test database connection (add test endpoint first)
curl -k https://localhost/dotnet-api/test-db

# Expected: Success message or crypto count
```

### 5. View Logs

```bash
# Data API logs
docker logs dotnet-data-api --tail 50

# Blazor Web logs
docker logs dotnet-web --tail 50

# Check for errors
docker logs dotnet-data-api 2>&1 | grep -i error
docker logs dotnet-web 2>&1 | grep -i error
```

### 6. Access in Browser

Open browser and navigate to:

1. **Blazor Web App:**
   - URL: `https://localhost/dotnet/`
   - Expected: .NET home page loads

2. **Swagger API Docs:**
   - URL: `https://localhost/dotnet-api/swagger`
   - Expected: OpenAPI documentation

3. **Health Check:**
   - URL: `https://localhost/dotnet-api/health`
   - Expected: JSON health status

### 7. Performance Check

```bash
# Test API response time
time curl -s -k https://localhost/dotnet-api/health > /dev/null

# Expected: real 0m0.010s (10ms)

# Load test with Apache Bench
ab -n 100 -c 10 http://localhost:5002/health

# Expected:
# Requests per second: 500+ req/s
# Time per request: <20ms
```

---

## Troubleshooting

### Issue: Container Won't Start

**Symptoms:**
- Container exits immediately
- Status shows "Restarting"

**Diagnosis:**
```bash
# Check logs
docker logs dotnet-data-api
docker logs dotnet-web

# Check exit code
docker inspect dotnet-data-api --format='{{.State.ExitCode}}'
```

**Solutions:**
```bash
# Rebuild without cache
docker compose build --no-cache dotnet-data-api

# Check port conflicts
netstat -tulpn | grep -E "5001|5002"

# Verify dependencies
docker ps | grep -E "database|redis"
```

### Issue: Database Connection Failed

**Symptoms:**
- Health check fails
- Logs show "connection refused" or "authentication failed"

**Diagnosis:**
```bash
# Test database connectivity
docker exec dotnet-data-api ping -c 3 database

# Test PostgreSQL port
docker exec dotnet-data-api nc -zv database 5432

# Check database status
docker exec docker-project-database-1 pg_isready
```

**Solutions:**
```bash
# Verify connection string
docker exec dotnet-data-api env | grep ConnectionStrings

# Test manual connection
docker exec -it dotnet-data-api sh
apk add postgresql-client
psql -h database -U root -d webapp_db

# Check database logs
docker logs docker-project-database-1 --tail 50
```

### Issue: Nginx 502 Bad Gateway

**Symptoms:**
- Browser shows 502 error
- nginx logs show "upstream" errors

**Diagnosis:**
```bash
# Check nginx error log
docker logs docker-project-nginx-1 | grep error

# Test direct container access
curl http://localhost:5001/
curl http://localhost:5002/health

# Check network connectivity
docker exec docker-project-nginx-1 ping -c 3 dotnet-web
docker exec docker-project-nginx-1 ping -c 3 dotnet-data-api
```

**Solutions:**
```bash
# Verify nginx configuration
docker exec docker-project-nginx-1 nginx -t

# Restart nginx
docker compose restart nginx

# Check if containers are in same network
docker network inspect docker-project_app-network
```

### Issue: High Memory Usage

**Symptoms:**
- Container using >500MB RAM
- Slow response times
- OOM killer messages

**Diagnosis:**
```bash
# Check resource usage
docker stats dotnet-data-api dotnet-web

# Check memory limits
docker inspect dotnet-data-api | grep -i memory
```

**Solutions:**
```bash
# Add memory limits to docker-compose.yml
# dotnet-data-api:
#   mem_limit: 512m
#   mem_reservation: 256m

# Restart with limits
docker compose down
docker compose up -d

# Monitor memory usage
watch -n 5 'docker stats --no-stream dotnet-data-api dotnet-web'
```

### Issue: Slow Build Times

**Symptoms:**
- Docker build takes >10 minutes
- Download speeds are slow

**Solutions:**
```bash
# Use build cache effectively
docker compose build --parallel

# Clear old images
docker image prune -a

# Use faster mirror (edit Dockerfile)
# FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
# RUN dotnet nuget add source https://api.nuget.org/v3/index.json
```

### Issue: Port Already in Use

**Symptoms:**
- "bind: address already in use"
- Container fails to start

**Diagnosis:**
```bash
# Find what's using the port
netstat -tulpn | grep -E "5001|5002"
lsof -i :5001
lsof -i :5002
```

**Solutions:**
```bash
# Kill the process
sudo kill -9 <PID>

# Or change port in docker-compose.yml
# ports:
#   - "5003:5002"  # Changed from 5002:5002
```

### Issue: SignalR Connection Failed

**Symptoms:**
- Real-time updates not working
- Browser console shows WebSocket errors

**Diagnosis:**
```bash
# Check nginx WebSocket configuration
docker exec docker-project-nginx-1 cat /etc/nginx/nginx.conf | grep -A 5 "map.*upgrade"

# Test WebSocket upgrade
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" http://localhost:5001/
```

**Solutions:**
```bash
# Ensure nginx has WebSocket support (see Nginx Configuration section)
# Add connection_upgrade mapping
# Restart nginx
docker compose restart nginx
```

---

## Post-Installation Steps

### 1. Configure Monitoring

```bash
# Enable detailed logging
docker compose down
# Edit docker-compose.yml, set ASPNETCORE_ENVIRONMENT=Development
docker compose up -d dotnet-data-api dotnet-web

# View detailed logs
docker logs -f dotnet-data-api
```

### 2. Set Up Backups

```bash
# Backup script for .NET artifacts
cat > backup-dotnet.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/one_control/backups/dotnet-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup source code
cp -r dotnet-data-api "$BACKUP_DIR/"
cp -r dotnet-web "$BACKUP_DIR/"

# Backup configurations
cp docker-compose.yml "$BACKUP_DIR/"
cp nginx/nginx.conf "$BACKUP_DIR/"

echo "Backup completed: $BACKUP_DIR"
EOF

chmod +x backup-dotnet.sh
./backup-dotnet.sh
```

### 3. Performance Tuning

```bash
# Adjust connection pool settings in appsettings.json
# Adjust memory limits in docker-compose.yml
# Enable response caching
# Configure Redis caching

# Monitor and adjust based on metrics
docker stats dotnet-data-api dotnet-web
```

### 4. Security Hardening

```bash
# Use secrets management for sensitive data
# Enable HTTPS only
# Configure rate limiting
# Implement authentication (future enhancement)
# Regular dependency updates
```

---

## Quick Reference

### Common Commands

```bash
# Build
docker compose build dotnet-data-api dotnet-web

# Start
docker compose up -d dotnet-data-api dotnet-web

# Stop
docker compose stop dotnet-data-api dotnet-web

# Restart
docker compose restart dotnet-data-api dotnet-web

# Logs
docker logs -f dotnet-data-api
docker logs -f dotnet-web

# Shell access
docker exec -it dotnet-data-api sh
docker exec -it dotnet-web sh

# Remove
docker compose down
docker compose rm -f dotnet-data-api dotnet-web

# Clean rebuild
docker compose down
docker compose build --no-cache dotnet-data-api dotnet-web
docker compose up -d
```

### URLs

- Blazor Web: `https://localhost/dotnet/`
- Data API: `https://localhost/dotnet-api/`
- Swagger: `https://localhost/dotnet-api/swagger`
- Health: `https://localhost/dotnet-api/health`

### Key Ports

- dotnet-web: 5001
- dotnet-data-api: 5002
- nginx: 80, 443

---

## Next Steps

After successful setup:

1. ✅ Implement API endpoints (see [API_REFERENCE.md](./API_REFERENCE.md))
2. ✅ Build Blazor components (see [BLAZOR_COMPONENTS.md](./BLAZOR_COMPONENTS.md))
3. ✅ Implement strategies (see [STRATEGIES.md](./STRATEGIES.md))
4. ✅ Run performance tests (see [PERFORMANCE.md](./PERFORMANCE.md))
5. ✅ Deploy to production (see [DEPLOYMENT.md](./DEPLOYMENT.md))

---

**Version:** 1.0.0  
**Last Updated:** October 9, 2025  
**Status:** 🟢 Ready for Implementation

---

**Need help?** See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) or check container logs.
