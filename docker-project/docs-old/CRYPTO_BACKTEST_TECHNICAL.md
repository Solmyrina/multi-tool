# Cryptocurrency Backtest Technical Documentation

**Complete technical reference for the backtesting system**

> **Consolidated from**: CRYPTO_BACKTEST_DATA_FLOW.md, CRYPTO_BACKTEST_STRATEGIES.md, CRYPTO_BACKTEST_STREAMING_IMPLEMENTATION.md

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Data Flow Architecture](#data-flow-architecture)
3. [Trading Strategies](#trading-strategies)
4. [Streaming Implementation](#streaming-implementation)
5. [Database Schema](#database-schema)
6. [API Reference](#api-reference)
7. [Frontend Integration](#frontend-integration)

---

## System Overview

### Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                            │
│  - crypto_backtest.html (UI)                                │
│  - Progressive loading with SSE                             │
│  - Real-time result display                                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                       Flask API                             │
│  - api.py (routing)                                         │
│  - streaming_backtest_service.py (SSE streaming)            │
│  - crypto_backtest_service.py (core engine)                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                 ┌───────┴────────┐
                 ↓                ↓
         ┌──────────────┐  ┌──────────────┐
         │  PostgreSQL  │  │    Redis     │
         │  (Primary)   │  │   (Cache)    │
         └──────────────┘  └──────────────┘
```

### Technology Stack

- **Backend**: Python 3.11, Flask, psycopg2
- **Database**: PostgreSQL 15 with optimized indexes
- **Cache**: Redis 7 (Alpine)
- **Calculations**: NumPy, Pandas
- **Streaming**: Server-Sent Events (SSE)
- **Concurrency**: ThreadPoolExecutor
- **Frontend**: jQuery, Bootstrap 5

---

## Data Flow Architecture

### Complete Request Flow

```
1. User selects strategy + parameters
           ↓
2. Frontend validates inputs
           ↓
3. POST /api/crypto/backtest/stream
           ↓
4. streaming_backtest_service.py receives request
           ↓
5. ThreadPoolExecutor spawns 4 workers
           ↓
6. Each worker:
   a. Check Redis cache for price data
   b. If miss → Query PostgreSQL
   c. Run strategy calculations (NumPy)
   d. Calculate performance metrics
   e. Yield SSE event with result
           ↓
7. Frontend receives SSE events
   a. Parse JSON data
   b. Update progress bar
   c. Add result row to table
   d. Update statistics
           ↓
8. All workers complete
           ↓
9. Send summary event
           ↓
10. Display final results + summary
```

### Data Flow Diagram

```
┌──────────────┐
│   User UI    │
│  (Browser)   │
└──────┬───────┘
       │ 1. POST /api/crypto/backtest/stream
       │    {strategy_id, parameters}
       ↓
┌──────────────────────────────────────────┐
│  streaming_backtest_service.py           │
│  ┌────────────────────────────────────┐  │
│  │ ThreadPoolExecutor (4 workers)     │  │
│  │  ┌──────────┐  ┌──────────┐       │  │
│  │  │ Worker 1 │  │ Worker 2 │  ...  │  │
│  │  └────┬─────┘  └────┬─────┘       │  │
│  └───────┼─────────────┼─────────────┘  │
└──────────┼─────────────┼────────────────┘
           │             │
           ↓             ↓
    ┌───────────┐ ┌───────────┐
    │  crypto   │ │  crypto   │
    │  #1 BTC   │ │  #2 ETH   │
    └─────┬─────┘ └─────┬─────┘
          │             │
          ↓             ↓
┌──────────────────────────────────────────┐
│  crypto_backtest_service.py              │
│  ┌────────────────────────────────────┐  │
│  │ get_price_data_cached()            │  │
│  │   Check Redis → PostgreSQL         │  │
│  └────────────┬───────────────────────┘  │
│               ↓                          │
│  ┌────────────────────────────────────┐  │
│  │ run_rsi_strategy()                 │  │
│  │ run_ma_crossover_strategy()        │  │
│  │ run_bollinger_bands_strategy()     │  │
│  │ etc.                               │  │
│  └────────────┬───────────────────────┘  │
│               ↓                          │
│  ┌────────────────────────────────────┐  │
│  │ Calculate metrics:                 │  │
│  │ - Total return                     │  │
│  │ - Win rate                         │  │
│  │ - Sharpe ratio                     │  │
│  │ - Max drawdown                     │  │
│  └────────────┬───────────────────────┘  │
└───────────────┼──────────────────────────┘
                │
                ↓
         SSE Event Stream
                │
    ┌───────────┴──────────┐
    │ event: result        │
    │ data: {              │
    │   success: true,     │
    │   crypto: "BTC",     │
    │   total_return: 45.2,│
    │   ...                │
    │ }                    │
    └───────────┬──────────┘
                │
                ↓
┌──────────────────────────────────────────┐
│  Frontend (crypto_backtest.html)         │
│  ┌────────────────────────────────────┐  │
│  │ handleStreamEvent()                │  │
│  │   - Parse result                   │  │
│  │   - Update progress                │  │
│  │   - Add table row                  │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

---

## Trading Strategies

### Available Strategies

| ID | Strategy | Description | Parameters |
|----|----------|-------------|------------|
| 1 | RSI Mean Reversion | Buy oversold, sell overbought | RSI period, thresholds, stop-loss |
| 2 | MA Crossover | Buy on fast>slow cross | Fast/slow periods, stop-loss |
| 3 | MACD | Buy on MACD>signal cross | Fast, slow, signal periods |
| 4 | Stochastic | Buy on %K<%D in oversold | %K, %D periods, thresholds |
| 5 | Bollinger Bands | Buy at lower band | Period, std multiplier, stop-loss |
| 6 | Mean Reversion | Buy on deviation from MA | Period, threshold, stop-loss |

### Strategy Details

#### 1. RSI Mean Reversion Strategy

**Concept**: RSI (Relative Strength Index) identifies overbought/oversold conditions.

**Buy Signal**: RSI < oversold_threshold (default: 30)  
**Sell Signal**: RSI > overbought_threshold (default: 70) OR stop-loss triggered  
**Stop-Loss**: Exit if loss exceeds threshold (default: 10%)

**Implementation:**
```python
def run_rsi_strategy(self, prices_df, parameters):
    """RSI Mean Reversion Strategy"""
    # Extract parameters
    rsi_period = parameters.get('rsi_period', 14)
    oversold = parameters.get('oversold_threshold', 30)
    overbought = parameters.get('overbought_threshold', 70)
    stop_loss = parameters.get('stop_loss_threshold', 10)
    
    # Calculate RSI (vectorized with NumPy)
    delta = prices_df['close_price'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    # Backtest logic
    position = 0  # 0 = no position, 1 = holding
    entry_price = 0
    trades = []
    
    for i in range(len(prices_df)):
        current_price = prices_df.iloc[i]['close_price']
        current_rsi = rsi.iloc[i]
        
        if position == 0:
            # Look for buy signal
            if current_rsi < oversold:
                position = 1
                entry_price = current_price
                trades.append({
                    'type': 'buy',
                    'price': entry_price,
                    'date': prices_df.iloc[i]['datetime']
                })
        else:
            # Check stop-loss
            profit_pct = ((current_price - entry_price) / entry_price) * 100
            if profit_pct <= -stop_loss:
                position = 0
                exit_price = current_price
                trades.append({
                    'type': 'sell',
                    'price': exit_price,
                    'date': prices_df.iloc[i]['datetime'],
                    'reason': 'stop_loss'
                })
            # Check sell signal
            elif current_rsi > overbought:
                position = 0
                exit_price = current_price
                trades.append({
                    'type': 'sell',
                    'price': exit_price,
                    'date': prices_df.iloc[i]['datetime'],
                    'reason': 'signal'
                })
    
    # Calculate performance metrics
    return self.calculate_performance(trades, prices_df)
```

**Parameters:**
- `rsi_period`: Lookback period for RSI (default: 14)
- `oversold_threshold`: Buy when RSI below this (default: 30)
- `overbought_threshold`: Sell when RSI above this (default: 70)
- `stop_loss_threshold`: Maximum acceptable loss % (default: 10)

#### 2. Moving Average Crossover Strategy

**Concept**: Two MAs - buy when fast crosses above slow, sell when fast crosses below slow.

**Buy Signal**: Fast MA > Slow MA (golden cross)  
**Sell Signal**: Fast MA < Slow MA (death cross) OR stop-loss triggered  
**Stop-Loss**: Exit if loss exceeds threshold (default: 10%)

**Implementation:**
```python
def run_ma_crossover_strategy(self, prices_df, parameters):
    """Moving Average Crossover Strategy"""
    fast_period = parameters.get('fast_ma_period', 10)
    slow_period = parameters.get('slow_ma_period', 30)
    stop_loss = parameters.get('stop_loss_threshold', 10)
    
    # Calculate moving averages
    fast_ma = prices_df['close_price'].rolling(window=fast_period).mean()
    slow_ma = prices_df['close_price'].rolling(window=slow_period).mean()
    
    position = 0
    entry_price = 0
    trades = []
    
    for i in range(slow_period, len(prices_df)):
        current_price = prices_df.iloc[i]['close_price']
        prev_fast = fast_ma.iloc[i-1]
        prev_slow = slow_ma.iloc[i-1]
        curr_fast = fast_ma.iloc[i]
        curr_slow = slow_ma.iloc[i]
        
        if position == 0:
            # Golden cross - buy
            if prev_fast <= prev_slow and curr_fast > curr_slow:
                position = 1
                entry_price = current_price
                trades.append({
                    'type': 'buy',
                    'price': entry_price,
                    'date': prices_df.iloc[i]['datetime']
                })
        else:
            # Check stop-loss
            profit_pct = ((current_price - entry_price) / entry_price) * 100
            if profit_pct <= -stop_loss:
                position = 0
                trades.append({
                    'type': 'sell',
                    'price': current_price,
                    'date': prices_df.iloc[i]['datetime'],
                    'reason': 'stop_loss'
                })
            # Death cross - sell
            elif prev_fast >= prev_slow and curr_fast < curr_slow:
                position = 0
                trades.append({
                    'type': 'sell',
                    'price': current_price,
                    'date': prices_df.iloc[i]['datetime'],
                    'reason': 'signal'
                })
    
    return self.calculate_performance(trades, prices_df)
```

**Parameters:**
- `fast_ma_period`: Fast MA period (default: 10)
- `slow_ma_period`: Slow MA period (default: 30)
- `stop_loss_threshold`: Maximum acceptable loss % (default: 10)

#### 3. Bollinger Bands Strategy

**Concept**: Price tends to revert to mean (middle band). Buy at lower band, sell at upper band.

**Buy Signal**: Price touches/crosses below lower band  
**Sell Signal**: Price touches/crosses above upper band OR stop-loss  
**Stop-Loss**: Exit if loss exceeds threshold (default: 10%)

**Implementation:**
```python
def run_bollinger_bands_strategy(self, prices_df, parameters):
    """Bollinger Bands Mean Reversion Strategy"""
    period = parameters.get('bb_period', 20)
    std_mult = parameters.get('bb_std_multiplier', 2.0)
    stop_loss = parameters.get('stop_loss_threshold', 10)
    
    # Calculate Bollinger Bands
    middle_band = prices_df['close_price'].rolling(window=period).mean()
    std = prices_df['close_price'].rolling(window=period).std()
    upper_band = middle_band + (std * std_mult)
    lower_band = middle_band - (std * std_mult)
    
    position = 0
    entry_price = 0
    trades = []
    
    for i in range(period, len(prices_df)):
        current_price = prices_df.iloc[i]['close_price']
        current_lower = lower_band.iloc[i]
        current_upper = upper_band.iloc[i]
        
        if position == 0:
            # Buy at lower band
            if current_price <= current_lower:
                position = 1
                entry_price = current_price
                trades.append({
                    'type': 'buy',
                    'price': entry_price,
                    'date': prices_df.iloc[i]['datetime']
                })
        else:
            # Check stop-loss
            profit_pct = ((current_price - entry_price) / entry_price) * 100
            if profit_pct <= -stop_loss:
                position = 0
                trades.append({
                    'type': 'sell',
                    'price': current_price,
                    'date': prices_df.iloc[i]['datetime'],
                    'reason': 'stop_loss'
                })
            # Sell at upper band
            elif current_price >= current_upper:
                position = 0
                trades.append({
                    'type': 'sell',
                    'price': current_price,
                    'date': prices_df.iloc[i]['datetime'],
                    'reason': 'signal'
                })
    
    return self.calculate_performance(trades, prices_df)
```

**Parameters:**
- `bb_period`: Lookback period for MA and std dev (default: 20)
- `bb_std_multiplier`: Standard deviation multiplier (default: 2.0)
- `stop_loss_threshold`: Maximum acceptable loss % (default: 10)

### Performance Metrics

All strategies calculate these metrics:

```python
def calculate_performance(self, trades, prices_df):
    """Calculate comprehensive performance metrics"""
    
    # Match buy/sell pairs
    buy_trades = [t for t in trades if t['type'] == 'buy']
    sell_trades = [t for t in trades if t['type'] == 'sell']
    
    total_return = 0
    profitable_trades = 0
    losing_trades = 0
    
    for i in range(min(len(buy_trades), len(sell_trades))):
        buy_price = buy_trades[i]['price']
        sell_price = sell_trades[i]['price']
        trade_return = ((sell_price - buy_price) / buy_price) * 100
        
        total_return += trade_return
        
        if trade_return > 0:
            profitable_trades += 1
        else:
            losing_trades += 1
    
    # Calculate additional metrics
    win_rate = (profitable_trades / len(buy_trades) * 100) if buy_trades else 0
    
    # Buy & Hold comparison
    if len(prices_df) > 0:
        buy_hold_return = (
            (prices_df.iloc[-1]['close_price'] - prices_df.iloc[0]['close_price'])
            / prices_df.iloc[0]['close_price']
        ) * 100
    else:
        buy_hold_return = 0
    
    # Sharpe Ratio (simplified)
    if len(buy_trades) > 1:
        returns = [
            ((sell_trades[i]['price'] - buy_trades[i]['price']) / buy_trades[i]['price'])
            for i in range(min(len(buy_trades), len(sell_trades)))
        ]
        sharpe_ratio = (
            (sum(returns) / len(returns)) / (pd.Series(returns).std())
            if pd.Series(returns).std() > 0 else 0
        )
    else:
        sharpe_ratio = 0
    
    # Max Drawdown
    max_drawdown = self.calculate_max_drawdown(trades, prices_df)
    
    return {
        'total_return': round(total_return, 2),
        'win_rate': round(win_rate, 2),
        'total_trades': len(buy_trades),
        'profitable_trades': profitable_trades,
        'losing_trades': losing_trades,
        'buy_hold_return': round(buy_hold_return, 2),
        'sharpe_ratio': round(sharpe_ratio, 2),
        'max_drawdown': round(max_drawdown, 2)
    }
```

---

## Streaming Implementation

### Server-Sent Events (SSE)

SSE allows the server to push real-time updates to the client over a single HTTP connection.

#### Backend: Streaming Service

```python
# api/streaming_backtest_service.py
from concurrent.futures import ThreadPoolExecutor
import json
import time

class StreamingBacktestService:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.backtest_service = CryptoBacktestService()
        
    def stream_strategy_against_all_cryptos(self, strategy_id, parameters, 
                                           start_date, end_date):
        """Generator that yields SSE events"""
        start_time = time.time()
        
        # Get list of cryptocurrencies
        cryptos = self.backtest_service.get_cryptocurrencies_with_data()
        total = len(cryptos)
        
        # Send start event
        yield self._format_sse({
            'type': 'start',
            'total': total,
            'strategy_id': strategy_id,
            'start_date': start_date,
            'end_date': end_date
        })
        
        # Submit all backtests to thread pool
        futures = []
        for crypto in cryptos:
            future = self.executor.submit(
                self._run_single_backtest_safe,
                strategy_id,
                crypto,
                parameters,
                start_date,
                end_date
            )
            futures.append((crypto, future))
        
        # Process results as they complete
        completed = 0
        successful = 0
        results = []
        
        for crypto, future in futures:
            # Wait for result
            result = future.result()
            completed += 1
            
            if result.get('success'):
                successful += 1
                results.append(result)
                
                # Send result event
                yield self._format_sse({
                    'type': 'result',
                    'data': result
                })
            else:
                # Send error event
                yield self._format_sse({
                    'type': 'error',
                    'crypto': crypto['symbol'],
                    'error': result.get('error', 'Unknown error')
                })
            
            # Send progress event
            yield self._format_sse({
                'type': 'progress',
                'completed': completed,
                'total': total,
                'successful': successful,
                'percent': round((completed / total) * 100, 1)
            })
        
        # Calculate summary
        summary = self._calculate_summary(results, total, successful)
        
        # Send complete event
        yield self._format_sse({
            'type': 'complete',
            'summary': summary,
            'elapsed_time': round(time.time() - start_time, 2)
        })
    
    def _format_sse(self, data):
        """Format data as Server-Sent Event"""
        return f"data: {json.dumps(data)}\n\n"
    
    def _run_single_backtest_safe(self, strategy_id, crypto, parameters, 
                                  start_date, end_date):
        """Run single backtest with error handling"""
        try:
            result = self.backtest_service.run_strategy_against_crypto(
                strategy_id,
                crypto['id'],
                parameters,
                start_date,
                end_date
            )
            result['success'] = True
            result['crypto_symbol'] = crypto['symbol']
            result['crypto_name'] = crypto['name']
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'crypto_symbol': crypto['symbol']
            }
    
    def _calculate_summary(self, results, total, successful):
        """Calculate summary statistics"""
        if not results:
            return {}
        
        return {
            'total_cryptos': total,
            'successful': successful,
            'failed': total - successful,
            'avg_return': round(sum(r['total_return'] for r in results) / len(results), 2),
            'avg_win_rate': round(sum(r['win_rate'] for r in results) / len(results), 2),
            'total_trades': sum(r['total_trades'] for r in results),
            'total_winning_trades': sum(r.get('profitable_trades', 0) for r in results),
            'total_losing_trades': sum(r.get('losing_trades', 0) for r in results),
            'best_performer': max(results, key=lambda x: x['total_return']),
            'worst_performer': min(results, key=lambda x: x['total_return'])
        }
```

#### API Endpoint

```python
# api/api.py
from flask import Response, stream_with_context, request

@app.route('/api/crypto/backtest/stream', methods=['POST'])
def stream_backtest():
    """SSE streaming endpoint"""
    data = request.get_json()
    
    strategy_id = data.get('strategy_id')
    parameters = data.get('parameters', {})
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    streaming_service = StreamingBacktestService()
    
    def generate():
        """Generator function for streaming"""
        for event in streaming_service.stream_strategy_against_all_cryptos(
            strategy_id,
            parameters,
            start_date,
            end_date
        ):
            yield event
    
    # Return SSE response
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',  # Disable nginx buffering
            'Connection': 'keep-alive'
        }
    )
```

#### Frontend: XHR Streaming

```javascript
// webapp/templates/crypto_backtest.html
function runAllBacktestsProgressive(strategyId, parameters, startDate, endDate) {
    // Initialize state
    const state = {
        results: [],
        completed: 0,
        total: 0,
        successful: 0
    };
    
    // Show progressive loading panel
    $('#progressiveLoading').show();
    $('#streamingTitle').html('<i class="fas fa-spinner fa-spin"></i> Running Backtests...');
    
    // Create XHR for streaming
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/crypto/backtest/stream', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    
    let buffer = '';
    let lastProcessed = 0;
    
    xhr.onprogress = function() {
        // Get new chunk
        const newData = xhr.responseText.substring(lastProcessed);
        lastProcessed = xhr.responseText.length;
        buffer += newData;
        
        // Process complete SSE events (ending with \n\n)
        const lines = buffer.split('\n\n');
        
        // Keep incomplete event in buffer
        buffer = lines.pop() || '';
        
        // Process each complete event
        for (const line of lines) {
            if (line.trim().startsWith('data: ')) {
                const jsonStr = line.trim().substring(6);
                try {
                    const event = JSON.parse(jsonStr);
                    handleStreamEvent(event, state);
                } catch (e) {
                    console.error('Error parsing SSE event:', e, jsonStr);
                }
            }
        }
    };
    
    xhr.onerror = function() {
        console.error('Stream error');
        showError('Connection error. Please try again.');
        $('#progressiveLoading').hide();
    };
    
    xhr.onload = function() {
        console.log('Stream complete');
    };
    
    // Send request
    xhr.send(JSON.stringify({
        strategy_id: strategyId,
        parameters: parameters,
        start_date: startDate,
        end_date: endDate
    }));
}

function handleStreamEvent(event, state) {
    switch(event.type) {
        case 'start':
            state.total = event.total;
            $('#streamingTotal').text(event.total);
            $('#streamingCompleted').text('0');
            $('#streamingProgress').css('width', '0%');
            break;
            
        case 'result':
            // Add result to state
            state.results.push(event.data);
            
            // Add row to table immediately
            addResultRowProgressive(event.data);
            break;
            
        case 'progress':
            // Update progress bar and counters
            state.completed = event.completed;
            state.successful = event.successful;
            
            $('#streamingCompleted').text(event.completed);
            $('#streamingProgress').css('width', event.percent + '%');
            $('#streamingProgress').text(event.percent + '%');
            break;
            
        case 'error':
            console.error('Backtest error:', event.crypto, event.error);
            break;
            
        case 'complete':
            // Display final results
            displayResults(state.results, false, event.summary);
            
            // Hide progressive panel
            setTimeout(() => {
                $('#progressiveLoading').fadeOut(300);
            }, 500);
            break;
    }
}
```

---

## Database Schema

### Cryptocurrencies Table

```sql
CREATE TABLE cryptocurrencies (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cryptocurrencies_active ON cryptocurrencies(is_active);
CREATE INDEX idx_cryptocurrencies_symbol ON cryptocurrencies(symbol);
```

### Crypto Prices Table

```sql
CREATE TABLE crypto_prices (
    id SERIAL PRIMARY KEY,
    crypto_id INTEGER REFERENCES cryptocurrencies(id),
    datetime TIMESTAMP NOT NULL,
    open_price NUMERIC(20, 8) NOT NULL,
    high_price NUMERIC(20, 8) NOT NULL,
    low_price NUMERIC(20, 8) NOT NULL,
    close_price NUMERIC(20, 8) NOT NULL,
    volume NUMERIC(20, 8),
    interval_type VARCHAR(10) DEFAULT '1h',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(crypto_id, datetime, interval_type)
);

-- Performance indexes
CREATE INDEX idx_crypto_prices_composite 
    ON crypto_prices(crypto_id, interval_type, datetime);

CREATE INDEX idx_crypto_prices_datetime 
    ON crypto_prices(datetime);
```

### Strategies Table

```sql
CREATE TABLE crypto_strategies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Strategy Parameters Table

```sql
CREATE TABLE crypto_strategy_parameters (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER REFERENCES crypto_strategies(id),
    parameter_name VARCHAR(100) NOT NULL,
    display_name VARCHAR(100),
    parameter_type VARCHAR(20),  -- 'number', 'boolean', 'select'
    default_value TEXT,
    min_value NUMERIC,
    max_value NUMERIC,
    options TEXT,  -- JSON array for select type
    display_order INTEGER DEFAULT 0,
    UNIQUE(strategy_id, parameter_name)
);
```

---

## API Reference

### POST /api/crypto/backtest/stream

**Description**: Stream backtest results in real-time using Server-Sent Events.

**Request:**
```json
{
  "strategy_id": 1,
  "parameters": {
    "rsi_period": 14,
    "oversold_threshold": 30,
    "overbought_threshold": 70,
    "stop_loss_threshold": 10
  },
  "start_date": "2024-01-01",
  "end_date": "2024-12-31"
}
```

**Response**: Server-Sent Events stream

**Event Types:**

1. **start** - Initial event
```json
{
  "type": "start",
  "total": 48,
  "strategy_id": 1,
  "start_date": "2024-01-01",
  "end_date": "2024-12-31"
}
```

2. **result** - Individual backtest result
```json
{
  "type": "result",
  "data": {
    "success": true,
    "crypto_symbol": "BTC",
    "crypto_name": "Bitcoin",
    "total_return": 45.23,
    "win_rate": 62.5,
    "total_trades": 24,
    "profitable_trades": 15,
    "losing_trades": 9,
    "buy_hold_return": 38.72,
    "sharpe_ratio": 1.45,
    "max_drawdown": -15.3
  }
}
```

3. **progress** - Progress update
```json
{
  "type": "progress",
  "completed": 12,
  "total": 48,
  "successful": 11,
  "percent": 25.0
}
```

4. **error** - Error for specific crypto
```json
{
  "type": "error",
  "crypto": "DOGE",
  "error": "Insufficient data for backtest"
}
```

5. **complete** - Final summary
```json
{
  "type": "complete",
  "summary": {
    "total_cryptos": 48,
    "successful": 47,
    "failed": 1,
    "avg_return": 23.45,
    "avg_win_rate": 58.3,
    "total_trades": 1152,
    "total_winning_trades": 672,
    "total_losing_trades": 480,
    "best_performer": {
      "crypto_symbol": "ETH",
      "total_return": 125.6
    },
    "worst_performer": {
      "crypto_symbol": "XRP",
      "total_return": -12.3
    }
  },
  "elapsed_time": 3.42
}
```

---

## Frontend Integration

### Progressive Result Display

```javascript
function addResultRowProgressive(result) {
    // Create table row with animated entrance
    const row = $('<tr>').hide();
    
    // Crypto name
    row.append($('<td>').text(result.crypto_name));
    
    // Total return with color
    const returnClass = result.total_return >= 0 ? 'positive' : 'negative';
    const returnText = (result.total_return >= 0 ? '+' : '') + result.total_return.toFixed(2) + '%';
    row.append($('<td>').addClass(returnClass).text(returnText));
    
    // Win rate
    row.append($('<td>').text(result.win_rate.toFixed(1) + '%'));
    
    // Total trades
    row.append($('<td>').text(result.total_trades));
    
    // Buy & Hold with color
    const bhClass = result.buy_hold_return >= 0 ? 'positive' : 'negative';
    const bhText = (result.buy_hold_return >= 0 ? '+' : '') + result.buy_hold_return.toFixed(2) + '%';
    row.append($('<td>').addClass(bhClass).text(bhText));
    
    // Add to table with fade-in animation
    $('#results-tbody').append(row);
    row.fadeIn(200);
    
    // Scroll to bottom
    const resultsContainer = $('#results-container');
    resultsContainer.scrollTop(resultsContainer.prop('scrollHeight'));
}
```

### Summary Display

```javascript
function displaySummary(summary) {
    $('#summary-total').text(summary.total_cryptos);
    $('#summary-successful').text(summary.successful);
    $('#summary-avg-return').text(summary.avg_return.toFixed(2) + '%');
    $('#summary-avg-winrate').text(summary.avg_win_rate.toFixed(1) + '%');
    $('#summary-total-trades').text(summary.total_trades);
    $('#summary-winning-trades').text(summary.total_winning_trades);
    $('#summary-losing-trades').text(summary.total_losing_trades);
    
    // Best performer
    $('#best-performer-name').text(summary.best_performer.crypto_symbol);
    $('#best-performer-return').text('+' + summary.best_performer.total_return.toFixed(2) + '%');
    
    // Worst performer
    $('#worst-performer-name').text(summary.worst_performer.crypto_symbol);
    $('#worst-performer-return').text(summary.worst_performer.total_return.toFixed(2) + '%');
}
```

---

## Conclusion

This technical documentation covers:

- ✅ Complete data flow architecture
- ✅ 6 trading strategies with stop-loss support
- ✅ Server-Sent Events streaming implementation
- ✅ Database schema with optimized indexes
- ✅ API reference with event types
- ✅ Frontend progressive loading integration

**Result**: A high-performance, real-time backtesting system with instant feedback and comprehensive metrics!

---

**Last Updated**: October 8, 2025  
**Consolidated From**: 3 technical backtest documents
