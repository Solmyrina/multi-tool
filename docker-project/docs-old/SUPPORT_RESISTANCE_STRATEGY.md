# Support/Resistance Trading Strategy

## Overview

The Support/Resistance strategy is a technical analysis approach that identifies key price levels where an asset tends to find buying support or selling resistance. This strategy exploits these levels to generate buy and sell signals.

**Strategy ID:** 4  
**Implementation Date:** October 8, 2025  
**Status:** ✅ Fully Implemented

---

## Core Concepts

### Support Levels
A **support level** is a price point where buying interest is strong enough to overcome selling pressure, preventing the price from falling further. When price approaches support:
- Buyers tend to enter the market
- Selling pressure decreases
- Price often "bounces" upward

### Resistance Levels
A **resistance level** is a price point where selling pressure overcomes buying interest, preventing the price from rising further. When price approaches resistance:
- Sellers tend to enter the market
- Buying pressure decreases
- Price often reverses downward

### Breakouts & Breakdowns
- **Breakout:** When price breaks above resistance with momentum → Strong buy signal
- **Breakdown:** When price breaks below support with momentum → Strong sell signal

---

## Algorithm Implementation

### Level Detection Algorithm

The strategy uses a **local extrema detection** method to identify support and resistance:

```python
def find_support_resistance(price_series, tolerance=0.02):
    """
    1. Scan price history for local minima (support) and maxima (resistance)
    2. A point is a local minimum if it's lower than 2 prices before AND after
    3. A point is a local maximum if it's higher than 2 prices before AND after
    4. Cluster similar levels within 2% tolerance
    5. Filter levels with minimum number of touches
    """
```

**Example:**
- Price touches $100, $101, $99 → Clustered as $100 support level
- If touched 3+ times (min_touches) → Confirmed as valid level

### Trading Signals

#### BUY SIGNALS

1. **Resistance Breakout**
   ```
   IF current_price > resistance_level * (1 + break_threshold):
       → BUY (breakout above resistance)
   ```
   - Example: Resistance at $100, break_threshold = 2%
   - Price reaches $102+ → BUY signal

2. **Support Bounce**
   ```
   IF abs(current_price - support_level) / support_level < 1%:
       AND previous_price < current_price:
           → BUY (bounce off support)
   ```
   - Example: Support at $100, price drops to $100.50 then rises
   - Confirms bounce → BUY signal

#### SELL SIGNALS

1. **Support Breakdown**
   ```
   IF current_price < support_level * (1 - break_threshold):
       → SELL (breakdown below support)
   ```
   - Example: Support at $100, break_threshold = 2%
   - Price drops to $98- → SELL signal

2. **Resistance Rejection**
   ```
   IF abs(current_price - resistance_level) / resistance_level < 1%:
       AND position is profitable:
           → SELL (resistance reached, take profit)
   ```
   - Example: Resistance at $110, bought at $100
   - Price reaches $109-111 → SELL signal (10% profit)

3. **Stop Loss**
   ```
   IF (current_price - entry_price) / entry_price <= -stop_loss_threshold:
       → SELL (stop loss triggered)
   ```

---

## Strategy Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| **initial_investment** | number | 1000 | 100 - 1,000,000 | Starting capital for backtest |
| **lookback_period** | integer | 50 | 20 - 100 | Number of periods to analyze for S/R levels |
| **min_touches** | integer | 3 | 2 - 5 | Minimum touches required to confirm a level |
| **break_threshold** | percentage | 2.0% | 0.5 - 5.0% | % price must break through S/R to trigger trade |
| **stop_loss_threshold** | number | 10.0 | 1 - 50 | Maximum loss % before force sell |
| **cooldown_unit** | text | hours | hours/days | Unit for cooldown period |
| **cooldown_value** | integer | 24 | 0 - 168 | Cooldown time after sell before next buy |
| **transaction_fee** | percentage | 0.1% | 0 - 5.0% | Fee per transaction (buy/sell) |

### Parameter Tuning Guide

#### Conservative Settings (Lower Risk)
```
lookback_period: 100      # Longer history = more reliable levels
min_touches: 4-5          # Require stronger confirmation
break_threshold: 3-5%     # Only trade on strong breakouts
stop_loss_threshold: 5%   # Tight stop loss
cooldown_value: 48-72h    # Wait longer between trades
```

#### Aggressive Settings (Higher Risk)
```
lookback_period: 20-30    # React faster to new levels
min_touches: 2            # Trade on weaker signals
break_threshold: 0.5-1%   # Trade on small movements
stop_loss_threshold: 20%  # Allow larger drawdowns
cooldown_value: 0-12h     # Trade more frequently
```

#### Recommended Starting Settings
```
lookback_period: 50       # Balanced history window
min_touches: 3            # Moderate confirmation
break_threshold: 2%       # Standard breakout threshold
stop_loss_threshold: 10%  # Reasonable risk management
cooldown_value: 24h       # Daily trading frequency
```

---

## Example Backtest Scenario

### Setup
- **Crypto:** Bitcoin (BTC)
- **Period:** 30 days
- **Initial Investment:** $1,000
- **Parameters:** Default settings

### Trading Activity

#### Day 1-5: Level Identification
```
Price range: $28,000 - $30,000
Identified:
  - Support: $28,200 (4 touches)
  - Resistance: $29,800 (3 touches)
Action: Waiting for signal
```

#### Day 6: Breakout Buy
```
Price: $30,400 (breaks resistance at $29,800 by 2.01%)
Signal: BUY (breakout above resistance)
Action: Buy 0.0328 BTC at $30,400
Cost: $1,000 - $1.00 fee = $999.00
```

#### Day 7-15: Position Held
```
Price range: $30,000 - $31,500
New resistance identified: $31,500
Action: Holding position
```

#### Day 16: Resistance Rejection
```
Price: $31,450 (reaches resistance at $31,500)
Profit: ($31,450 - $30,400) / $30,400 = 3.45%
Signal: SELL (resistance reached, take profit)
Action: Sell 0.0328 BTC at $31,450
Revenue: $1,031.56 - $1.03 fee = $1,030.53
```

#### Day 17-25: Wait Period
```
Cooldown: 24 hours since last sell
Action: Observing market, no trades
```

#### Day 26: Support Breakdown
```
Price: $27,900 (breaks support at $28,200 by 2.13%)
Action: No position held, no sell signal
```

#### Day 30: Final Results
```
Final Value: $1,030.53
Total Return: +3.05%
Total Trades: 2 (1 buy, 1 sell)
Total Fees: $2.03
Profitable Trades: 1
```

---

## Performance Characteristics

### Strengths
✅ **Clear Entry/Exit Rules** - Objective signals based on price action  
✅ **Risk Management** - Built-in stop loss protection  
✅ **Trend Following** - Catches breakout momentum  
✅ **Mean Reversion** - Profits from support bounces  
✅ **Adaptable** - Adjusts to current market conditions

### Weaknesses
❌ **False Breakouts** - Price may break level then reverse quickly  
❌ **Whipsaw Markets** - Choppy conditions generate many false signals  
❌ **Lagging Indicator** - Requires historical data to identify levels  
❌ **Parameter Sensitivity** - Results vary significantly with settings  
❌ **Market Gaps** - Large gaps can skip through stop loss levels

### Best Market Conditions
- **Trending Markets:** Catches breakouts effectively
- **Range-Bound Markets:** Profits from bounces at support/resistance
- **Medium Volatility:** Enough movement to trigger signals without excessive noise

### Worst Market Conditions
- **High Volatility:** Too many false breakouts
- **Low Liquidity:** Slippage can invalidate levels
- **Strong Trends:** May miss entry if price gaps through resistance

---

## Technical Details

### Database Schema

```sql
-- Strategy definition
INSERT INTO crypto_strategies (id, name, description)
VALUES (4, 'Support/Resistance', 
        'Buy at support levels, sell at resistance levels based on recent price action');

-- Parameters (8 total)
INSERT INTO crypto_strategy_parameters 
(strategy_id, parameter_name, parameter_type, default_value, min_value, max_value)
VALUES 
(4, 'initial_investment', 'number', 1000, 100, 1000000),
(4, 'lookback_period', 'integer', 50, 20, 100),
(4, 'min_touches', 'integer', 3, 2, 5),
(4, 'break_threshold', 'percentage', 2, 0.5, 5),
(4, 'stop_loss_threshold', 'number', 10, 1, 50),
(4, 'cooldown_unit', 'text', 'hours', NULL, NULL),
(4, 'cooldown_value', 'integer', 24, 0, 168),
(4, 'transaction_fee', 'percentage', 0.1, 0, 5);
```

### Implementation File
- **Location:** `/api/crypto_backtest_service.py`
- **Method:** `backtest_support_resistance_strategy(df, params)`
- **Lines:** ~830-1030
- **Dependencies:** pandas, numpy
- **Data Source:** TimescaleDB hypertable `crypto_prices`

### API Endpoints

```bash
# Get strategy parameters
GET /api/strategies/4/parameters

# Run backtest
POST /api/crypto/backtest
{
  "crypto_id": 1,
  "strategy_id": 4,
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "parameters": {
    "initial_investment": 1000,
    "lookback_period": 50,
    "min_touches": 3,
    "break_threshold": 2,
    "stop_loss_threshold": 10,
    "cooldown_unit": "hours",
    "cooldown_value": 24,
    "transaction_fee": 0.1
  }
}
```

---

## Testing & Validation

### Unit Tests Needed
- [ ] Level detection accuracy
- [ ] Breakout signal generation
- [ ] Bounce signal generation
- [ ] Stop loss execution
- [ ] Cooldown period enforcement
- [ ] Fee calculation
- [ ] Edge cases (insufficient data, no levels found)

### Integration Tests
- [ ] Full backtest with real historical data
- [ ] Compare against other strategies (RSI, MA Crossover)
- [ ] Performance across different cryptocurrencies
- [ ] Parameter sensitivity analysis

### Manual Testing Steps

1. **Access Strategy in UI**
   ```
   Navigate to: Crypto Backtester → Select "Support/Resistance"
   Verify: 8 parameters display correctly
   ```

2. **Run Default Backtest**
   ```
   Settings: BTC, Last 90 days, Default parameters
   Expected: Trades executed, results displayed
   ```

3. **Test Parameter Ranges**
   ```
   Try: lookback_period = 20, 50, 100
   Verify: Different results, no errors
   ```

4. **Verify Trade Logic**
   ```
   Check: Trades show proper triggers
   Example: "breakout above resistance $30,400"
   ```

---

## Comparison with Other Strategies

| Feature | Support/Resistance | RSI | MA Crossover | Momentum |
|---------|-------------------|-----|--------------|----------|
| **Complexity** | High | Low | Medium | Low |
| **Signals/Month** | 5-15 | 10-25 | 3-8 | 15-40 |
| **Best For** | Range-bound | Oversold/Overbought | Trends | Strong trends |
| **Parameter Count** | 8 | 8 | 7 | 8 |
| **Computational Cost** | High | Low | Medium | Low |
| **Adaptability** | High | Medium | Low | Medium |

---

## Future Enhancements

### Potential Improvements
1. **Volume Confirmation**
   - Require high volume on breakouts
   - Ignore low-volume false signals

2. **Dynamic Tolerance**
   - Adjust clustering tolerance based on volatility
   - Tighter clusters in low volatility

3. **Multiple Timeframes**
   - Identify levels on daily + hourly charts
   - Only trade when both align

4. **Machine Learning**
   - Train model to identify strongest levels
   - Predict breakout success probability

5. **Risk Management**
   - Trailing stop loss
   - Position sizing based on distance to support
   - Partial profit taking at resistance

---

## References

### Academic Papers
- Edwards, R. D., & Magee, J. (2007). *Technical Analysis of Stock Trends*
- Murphy, J. J. (1999). *Technical Analysis of the Financial Markets*

### Implementation Notes
- Created: October 8, 2025
- Developer: GitHub Copilot
- Tested: ✅ Database parameters verified
- Status: Ready for UI testing

### Related Documentation
- [`TIMESCALEDB_IMPLEMENTATION_PLAN.md`](./TIMESCALEDB_IMPLEMENTATION_PLAN.md) - Data infrastructure
- [`DATABASE_ACCESS_GUIDE.md`](../DATABASE_ACCESS_GUIDE.md) - Database connection info
- [`api/crypto_backtest_service.py`](../api/crypto_backtest_service.py) - Implementation code

---

## Support

For questions or issues:
1. Check database: `docker exec -it docker-project-database psql -U root webapp_db`
2. Check API logs: `docker compose logs -f api`
3. Verify parameters: `SELECT * FROM crypto_strategy_parameters WHERE strategy_id = 4;`

**Last Updated:** October 8, 2025
