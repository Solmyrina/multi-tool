# .NET Data API - Endpoint Reference

**Base URL:** `http://localhost:5002` (dev) or `https://your-domain/dotnet-api` (production)

**Version:** 1.0.0  
**Framework:** .NET 9  
**Last Updated:** October 9, 2025

---

## Table of Contents

1. [Cryptocurrency Endpoints](#cryptocurrency-endpoints)
2. [Strategy Endpoints](#strategy-endpoints)
3. [Backtest Endpoints](#backtest-endpoints)
4. [Indicator Endpoints](#indicator-endpoints)
5. [System Endpoints](#system-endpoints)

---

## Cryptocurrency Endpoints

### List Cryptocurrencies
`GET /cryptocurrencies`

Returns a list of active cryptocurrencies.

**Query Parameters:** None

**Response:**
```json
[
  {
    "id": 1,
    "symbol": "BTC",
    "name": "Bitcoin",
    "binanceSymbol": "BTCUSDT",
    "active": true,
    "createdAt": "2024-01-01T00:00:00Z"
  }
]
```

---

### Get Cryptocurrency by ID
`GET /cryptocurrencies/{id}`

Returns details for a specific cryptocurrency.

**Path Parameters:**
- `id` (integer, required): Cryptocurrency ID

**Response:**
```json
{
  "id": 1,
  "symbol": "BTC",
  "name": "Bitcoin",
  "binanceSymbol": "BTCUSDT",
  "active": true,
  "createdAt": "2024-01-01T00:00:00Z"
}
```

---

### Get Cryptocurrency Prices
`GET /cryptocurrencies/{id}/prices`

Returns historical price data with optional aggregation.

**Path Parameters:**
- `id` (integer, required): Cryptocurrency ID

**Query Parameters:**
- `startDate` (datetime, optional): Start date (default: 30 days ago)
- `endDate` (datetime, optional): End date (default: now)
- `interval` (string, optional): Time bucket interval
  - Options: `1m`, `5m`, `15m`, `30m`, `1h`, `4h`, `1d`
  - Default: `1h`
- `limit` (integer, optional): Maximum rows (default: 500, max: 10000)

**Response:**
```json
{
  "cryptoId": 1,
  "interval": "1 hour",
  "startDate": "2025-10-01T00:00:00Z",
  "endDate": "2025-10-09T00:00:00Z",
  "count": 192,
  "prices": [
    {
      "timestamp": "2025-10-09T12:00:00Z",
      "price": 62500.50,
      "volume": 1250000.00,
      "marketCap": 1200000000000.00
    }
  ]
}
```

---

## Strategy Endpoints

### List Strategies
`GET /strategies`

Returns all available trading strategies.

**Query Parameters:** None

**Response:**
```json
[
  {
    "id": 1,
    "name": "RSI Strategy",
    "description": "Relative Strength Index strategy...",
    "parameters": [
      {
        "name": "rsi_period",
        "type": "int",
        "defaultValue": 14,
        "description": "Period for RSI calculation"
      }
    ]
  }
]
```

---

### Get Strategy by ID
`GET /strategies/{id}`

Returns details for a specific strategy.

**Path Parameters:**
- `id` (integer, required): Strategy ID

**Response:**
```json
{
  "id": 1,
  "name": "RSI Strategy",
  "description": "Relative Strength Index strategy...",
  "parameters": [
    {
      "name": "rsi_period",
      "type": "int",
      "defaultValue": 14,
      "description": "Period for RSI calculation"
    }
  ]
}
```

---

## Backtest Endpoints

### Execute Backtest
`POST /backtest`

Executes a backtest with the given parameters.

**Request Body:**
```json
{
  "strategyId": 1,
  "cryptoId": 1,
  "startDate": "2024-01-01T00:00:00Z",
  "endDate": "2024-12-31T23:59:59Z",
  "initialInvestment": 10000,
  "parameters": {
    "rsi_period": 14,
    "oversold": 30,
    "overbought": 70
  }
}
```

**Response:**
```json
{
  "id": 123,
  "strategyId": 1,
  "cryptoId": 1,
  "cryptoName": "Bitcoin",
  "strategyName": "RSI Strategy",
  "startDate": "2024-01-01T00:00:00Z",
  "endDate": "2024-12-31T23:59:59Z",
  "initialInvestment": 10000.00,
  "finalValue": 12500.00,
  "totalReturn": 2500.00,
  "totalReturnPercentage": 25.00,
  "totalTrades": 45,
  "winningTrades": 28,
  "losingTrades": 17,
  "winRate": 62.22,
  "maxDrawdown": 8.50,
  "sharpeRatio": 1.85,
  "executionTimeMs": 120,
  "trades": [...],
  "portfolioValues": [...],
  "parameters": {...},
  "createdAt": "2025-10-09T12:00:00Z"
}
```

---

### List Backtest Results
`GET /backtest/results`

Returns a paginated, filterable list of backtest results.

**Query Parameters:**
- `cryptoId` (integer, optional): Filter by cryptocurrency
- `strategyId` (integer, optional): Filter by strategy
- `startDate` (datetime, optional): Filter by creation date (>=)
- `endDate` (datetime, optional): Filter by creation date (<=)
- `minReturn` (decimal, optional): Minimum return percentage
- `maxReturn` (decimal, optional): Maximum return percentage
- `sortBy` (string, optional): Sort column
  - Options: `created_at`, `return`, `return_pct`, `trades`, `sharpe`, `max_drawdown`
  - Default: `created_at`
- `sortOrder` (string, optional): Sort direction (`ASC` or `DESC`, default: `DESC`)
- `offset` (integer, optional): Skip rows (default: 0)
- `limit` (integer, optional): Max rows (default: 20, max: 100)

**Response:**
```json
{
  "data": [
    {
      "id": 123,
      "strategyId": 1,
      "cryptoId": 1,
      "cryptoName": "Bitcoin",
      "strategyName": "RSI Strategy",
      "startDate": "2024-01-01T00:00:00Z",
      "endDate": "2024-12-31T23:59:59Z",
      "initialInvestment": 10000.00,
      "finalValue": 12500.00,
      "totalReturn": 2500.00,
      "totalReturnPercentage": 25.00,
      "totalTrades": 45,
      "winningTrades": 28,
      "losingTrades": 17,
      "maxDrawdown": 8.50,
      "sharpeRatio": 1.85,
      "executionTimeMs": 120,
      "createdAt": "2025-10-09T12:00:00Z"
    }
  ],
  "pagination": {
    "offset": 0,
    "limit": 20,
    "count": 1
  }
}
```

---

### Get Backtest Result by ID
`GET /backtest/results/{id}` or `GET /backtest/{id}`

Returns detailed backtest result including trades and portfolio snapshots.

**Path Parameters:**
- `id` (integer, required): Backtest result ID

**Response:** Same as Execute Backtest response

---

### Get Backtest Trades
`GET /backtest/{id}/trades`

Returns only the trade history for a specific backtest.

**Path Parameters:**
- `id` (integer, required): Backtest result ID

**Response:**
```json
[
  {
    "timestamp": "2024-01-15T10:30:00Z",
    "type": "BUY",
    "price": 42000.00,
    "quantity": 0.238,
    "value": 9996.00,
    "portfolioValue": 10000.00,
    "reason": "RSI 28.5 below oversold 30"
  }
]
```

---

### Delete Backtest Result
`DELETE /backtest/{id}`

Deletes a single backtest result.

**Path Parameters:**
- `id` (integer, required): Backtest result ID

**Response:** `204 No Content`

---

### Batch Delete Backtest Results
`DELETE /backtest/batch`

Deletes multiple backtest results.

**Request Body:**
```json
{
  "backtestIds": [123, 124, 125]
}
```

**Response:**
```json
{
  "deleted": 3
}
```

**Limits:** Maximum 50 backtests per request

---

### Compare Backtest Results
`POST /backtest/compare`

Compares multiple backtest results side-by-side.

**Request Body:**
```json
{
  "backtestIds": [123, 124, 125]
}
```

**Response:**
```json
{
  "count": 3,
  "results": [
    {
      "id": 123,
      "strategyName": "RSI Strategy",
      "cryptoName": "Bitcoin",
      "totalReturnPercentage": 25.00,
      "sharpeRatio": 1.85,
      "maxDrawdown": 8.50
    }
  ],
  "summary": {
    "bestReturn": {...},
    "worstReturn": {...},
    "bestSharpe": {...},
    "lowestDrawdown": {...},
    "avgReturn": 18.50,
    "avgSharpe": 1.45,
    "avgDrawdown": 10.20
  }
}
```

**Limits:** Maximum 10 backtests per comparison

---

### Get Backtest Statistics
`GET /backtest/stats`

Returns aggregate statistics across backtests.

**Query Parameters:**
- `cryptoId` (integer, optional): Filter by cryptocurrency
- `strategyId` (integer, optional): Filter by strategy

**Response:**
```json
{
  "total_backtests": 150,
  "avg_return_pct": 12.50,
  "max_return_pct": 85.00,
  "min_return_pct": -15.00,
  "avg_sharpe": 1.25,
  "avg_max_drawdown": 12.30,
  "avg_trades": 42.5,
  "overall_win_rate": 58.50
}
```

---

## Indicator Endpoints

### Get Technical Indicators
`GET /indicators/{cryptoId}`

Calculates and returns technical indicators for a cryptocurrency.

**Path Parameters:**
- `cryptoId` (integer, required): Cryptocurrency ID

**Query Parameters:**
- `startDate` (datetime, optional): Start date (default: 30 days ago)
- `endDate` (datetime, optional): End date (default: now)
- `smaShort` (integer, optional): Short SMA period (default: 20)
- `smaLong` (integer, optional): Long SMA period (default: 50)
- `emaShort` (integer, optional): Short EMA period (default: 12)
- `emaLong` (integer, optional): Long EMA period (default: 26)
- `rsiPeriod` (integer, optional): RSI period (default: 14)
- `bollingerPeriod` (integer, optional): Bollinger Bands period (default: 20)
- `bollingerStdDev` (decimal, optional): Bollinger Bands std dev (default: 2.0)

**Response:**
```json
{
  "cryptoId": 1,
  "startDate": "2025-09-09T00:00:00Z",
  "endDate": "2025-10-09T00:00:00Z",
  "count": 720,
  "latest": {
    "close": 62500.50,
    "rsi": 55.30,
    "smaShort": 61800.00,
    "smaLong": 60500.00,
    "emaShort": 62100.00,
    "emaLong": 61200.00,
    "bollingerUpper": 64500.00,
    "bollingerMiddle": 62000.00,
    "bollingerLower": 59500.00
  },
  "data": [
    {
      "timestamp": "2025-10-09T12:00:00Z",
      "close": 62500.50,
      "rsi": 55.30,
      "smaShort": 61800.00,
      "smaLong": 60500.00,
      "emaShort": 62100.00,
      "emaLong": 61200.00,
      "bollingerUpper": 64500.00,
      "bollingerMiddle": 62000.00,
      "bollingerLower": 59500.00
    }
  ]
}
```

---

## System Endpoints

### Root / API Info
`GET /`

Returns API information and available endpoints.

**Response:**
```json
{
  "name": "Crypto Backtest Data API",
  "version": "1.0.0",
  "framework": ".NET 9",
  "status": "Running",
  "endpoints": {
    "cryptocurrencies": [...],
    "strategies": [...],
    "backtest": [...],
    "indicators": [...],
    "system": [...]
  }
}
```

---

### Health Check
`GET /health`

Returns health status for container orchestration.

**Response:** `200 OK` with body `Healthy`

---

### Database Connection Test
`GET /test-db`

Tests database connectivity and returns basic stats.

**Response:**
```json
{
  "status": "Connected",
  "database": "webapp_db",
  "cryptocurrencies": 263,
  "timestamp": "2025-10-09T12:00:00Z"
}
```

---

### API Documentation (Swagger)
`GET /swagger`

Interactive API documentation and testing interface.

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "error": "End date must be after start date"
}
```

### 404 Not Found
```json
{
  "message": "Cryptocurrency with ID 999 not found"
}
```

### 500 Internal Server Error
```json
{
  "type": "https://tools.ietf.org/html/rfc9110#section-15.6.1",
  "title": "An error occurred while processing your request.",
  "status": 500,
  "detail": "Failed to retrieve cryptocurrencies"
}
```

---

## Rate Limiting

Currently no rate limiting is enforced. Consider implementing rate limiting for production use.

---

## Authentication

Currently no authentication is required. Consider implementing JWT or API key authentication for production use.

---

## CORS

CORS is configured to allow all origins in development. Restrict this in production:

```csharp
policy.WithOrigins("https://your-domain.com")
      .AllowAnyMethod()
      .AllowAnyHeader();
```

---

## Examples

### cURL Examples

**List cryptocurrencies:**
```bash
curl http://localhost:5002/cryptocurrencies
```

**Execute backtest:**
```bash
curl -X POST http://localhost:5002/backtest \
  -H "Content-Type: application/json" \
  -d '{
    "strategyId": 1,
    "cryptoId": 1,
    "startDate": "2024-01-01T00:00:00Z",
    "endDate": "2024-12-31T23:59:59Z",
    "initialInvestment": 10000,
    "parameters": {
      "rsi_period": 14,
      "oversold": 30,
      "overbought": 70
    }
  }'
```

**Get indicators:**
```bash
curl "http://localhost:5002/indicators/1?smaShort=20&smaLong=50&rsiPeriod=14"
```

**Filter backtest results:**
```bash
curl "http://localhost:5002/backtest/results?cryptoId=1&sortBy=return_pct&sortOrder=DESC&limit=10"
```

---

## Performance Notes

- All database queries use connection pooling (5-100 connections)
- Queries honor `CancellationToken` for graceful cancellation
- Results are streamed where possible to reduce memory usage
- TimescaleDB hypertables optimize time-series queries
- Consider adding Redis caching for frequently accessed data

---

**Documentation Version:** 1.0  
**Last Updated:** October 9, 2025
