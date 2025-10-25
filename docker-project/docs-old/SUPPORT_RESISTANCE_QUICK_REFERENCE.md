# Support/Resistance Strategy - Quick Reference

## 🎯 Strategy Overview
**Buy at support levels, sell at resistance levels based on recent price action**

## 📊 Parameters (8)

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| initial_investment | 1000 | 100-1M | Starting capital |
| lookback_period | 50 | 20-100 | Periods to analyze |
| min_touches | 3 | 2-5 | Touches to confirm level |
| break_threshold | 2% | 0.5-5% | Breakout trigger % |
| stop_loss_threshold | 10 | 1-50 | Max loss % |
| cooldown_unit | hours | - | hours/days |
| cooldown_value | 24 | 0-168 | Wait period |
| transaction_fee | 0.1% | 0-5% | Fee per trade |

## 📈 Trading Signals

### BUY Signals
✅ **Resistance Breakout** - Price > resistance × (1 + break_threshold)  
✅ **Support Bounce** - Price near support (±1%) and rising

### SELL Signals
🔴 **Support Breakdown** - Price < support × (1 - break_threshold)  
🔴 **Resistance Rejection** - Price at resistance & profitable  
🔴 **Stop Loss** - Loss exceeds threshold

## 🎨 Trading Example

```
Current Price: $30,500
Recent History:
  Support detected at: $28,200 (4 touches)
  Resistance detected at: $29,800 (3 touches)

Break Threshold: 2%
→ Buy if price > $30,396 (resistance + 2%)
→ Sell if price < $27,636 (support - 2%)

Action: BUY at $30,500
Trigger: "breakout above resistance $29,800"
Position: 0.0328 BTC
```

## 💡 Quick Tips

### Conservative Setup (Low Risk)
```
lookback_period: 100
min_touches: 4-5
break_threshold: 3-5%
stop_loss: 5%
cooldown: 48-72h
```

### Aggressive Setup (High Risk)
```
lookback_period: 20-30
min_touches: 2
break_threshold: 0.5-1%
stop_loss: 20%
cooldown: 0-12h
```

### Balanced Setup (Recommended)
```
lookback_period: 50
min_touches: 3
break_threshold: 2%
stop_loss: 10%
cooldown: 24h
```

## 🎯 Best For
- **Range-bound markets** - Horizontal price action
- **Medium volatility** - Clear levels without noise
- **Established trends** - Well-defined support/resistance

## ⚠️ Avoid When
- **High volatility** - Too many false breakouts
- **Strong trends** - Price gaps through levels
- **Low liquidity** - Slippage invalidates levels

## 🔧 Testing Commands

```bash
# Check parameters
docker exec docker-project-database psql -U root webapp_db -c \
  "SELECT * FROM crypto_strategy_parameters WHERE strategy_id = 4;"

# Check API logs
docker compose logs -f api

# Restart API
docker compose restart api
```

## 📚 Full Documentation
See: `docs/SUPPORT_RESISTANCE_STRATEGY.md`

## ✅ Status
**Implementation:** Complete  
**Parameters:** 8/8 loaded  
**API:** Operational  
**Ready to use:** YES

---
*Last Updated: October 8, 2025*
