# Backtesting System Quick Start

**Run trading strategy backtests against historical cryptocurrency data.**

## 🚀 Get Started in 3 Steps

### 1. Open the Backtesting Interface
Navigate to: `http://localhost:5003/backtest/new`

### 2. Configure Your Backtest

**Select Cryptocurrency**
- Choose from 230 cryptocurrencies with price data
- Includes BTC, ETH, ADA, XRP, SOL, and many others

**Select Strategy**
- **RSI (Relative Strength Index)**: Oscillator-based, trades on oversold/overbought
- **MA Crossover (Moving Averages)**: Trend-following, uses fast/slow moving averages
- **Bollinger Bands**: Volatility-based, trades range breaks

**Set Time Parameters**
- **Start Date**: Historical data available from 2020+
- **End Date**: Up to present day
- **Time Interval**: 1h (hourly), 4h, or 1d (daily)

**Set Initial Investment**
- Default: $10,000
- Adjustable from $0 to any amount

**Configure Strategy Parameters**
Each strategy has specific parameters:

| Strategy | Parameters |
|----------|------------|
| RSI | Period (2-100), Oversold (0-50), Overbought (50-100) |
| MA Crossover | Short MA (2-200), Long MA (2-200) |
| Bollinger Bands | Period (2-100), Std Dev Multiplier (0.1-5) |

### 3. Run Backtest
Click **"Run Backtest"** and wait for results

---

## 📊 Understanding Results

### Key Metrics

| Metric | Meaning |
|--------|---------|
| **Total Return %** | Profit/loss as percentage |
| **Final Value** | Portfolio value at end |
| **Total Trades** | Number of buy/sell signals |
| **Win Rate %** | Percentage of profitable trades |
| **Max Drawdown %** | Largest peak-to-trough decline |
| **Sharpe Ratio** | Risk-adjusted return (higher = better) |

### Result Display

```
Cryptocurrency    │ Total Return │ Final Value │ Trades │ Win Rate
─────────────────┼──────────────┼─────────────┼────────┼─────────
BTCUSDT          │    +45.3%    │   $14,530   │   23   │  65.2%
ETHUSDT          │    +32.1%    │   $13,210   │   18   │  61.1%
ADAUSDT          │     -8.5%    │    $9,150   │   12   │  50.0%
```

---

## 💡 Common Workflows

### Workflow 1: Find Best Strategy
1. Select single cryptocurrency (e.g., BTC)
2. Run all 3 strategies against same date range
3. Compare results
4. Winner = best strategy for that crypto + period

### Workflow 2: Test Different Time Periods
1. Run backtest for 2024 only (Jan 1 - Dec 31)
2. Run again for 2023 only
3. Compare performance consistency
4. Identify strategies stable across periods

### Workflow 3: Risk Analysis
1. Run backtest normally
2. Review "Max Drawdown" % (risk metric)
3. Lower max drawdown = less risky
4. Balance return vs. risk

---

## ⚡ Performance

- **Single backtest**: ~0.1-0.3 seconds (first result via SSE)
- **Full results**: 0.3-1 second per cryptocurrency
- **Batch (48 cryptos)**: 15-30 seconds total
- **Real-time updates**: Streamed via Server-Sent Events

---

## 🎯 Pro Tips

### ✅ DO
- Start with pre-set strategies before customizing parameters
- Test on 1-year date ranges for balanced analysis
- Compare strategies on same cryptocurrency + period
- Use max drawdown to assess strategy safety
- Check backtest date range matches your test period

### ❌ DON'T
- Expect past performance to predict future results
- Use only one metric (consider return + drawdown + win rate)
- Test on very short periods (< 1 month) - limited data
- Forget to account for trading fees & slippage
- Over-optimize to historical data (overfitting)

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| Results take too long | Reduce date range or use daily (1d) interval |
| No data error | Ensure cryptocurrency has price data for selected period |
| Strategy parameters invalid | Check min/max ranges, use default values as guide |
| Backtest failed | Verify dates are valid (start < end), retry |

---

## 📚 Related Documentation

- [Database Access Guide](./DATABASE.md) - Access historical data
- [Backtesting Engine Technical](../features/BACKTESTING_ENGINE.md) - How it works
- [System Status](./SYSTEM_STATUS.md) - Check data availability

---

## 🌐 UI Components

- **Configuration Panel**: Left side, strategy & parameter setup
- **Results Table**: Center, sortable results
- **Statistics Panel**: Right side, aggregate metrics
- **Progress Bar**: Real-time backtest progress
- **Charts** (Phase 4): Visual performance analysis

---

*Last Updated: October 25, 2025*  
*For technical details, see [Backtesting Engine](../features/BACKTESTING_ENGINE.md)*
