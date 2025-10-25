# Quick User Guide: New Backtesting Features

**Updated:** October 5, 2025  
**Features:** Time Range Selection & Sortable Results

---

## 🎯 Quick Start

### Time Range Selection

**Where:** Strategy Configuration Panel → "Time Range" section

**Options:**
```
┌─────────────────────────────────┐
│ Time Range (Optional)           │
│ Leave empty to use all data     │
├─────────────────────────────────┤
│ Start Date: [YYYY-MM-DD]        │
│ End Date:   [YYYY-MM-DD]        │
│                                 │
│ [Clear Dates]                   │
└─────────────────────────────────┘
```

**Examples:**

| Use Case | Start Date | End Date | Result |
|----------|------------|----------|--------|
| Test 2024 only | 2024-01-01 | 2024-12-31 | 1 year |
| Last 6 months | 2024-04-01 | (empty) | Recent data |
| All available | (empty) | (empty) | 5+ years |
| Bull market | 2021-01-01 | 2021-12-31 | 2021 only |

---

### Sortable Results Table

**How to Use:**
1. Click any column header to sort
2. Click again to reverse sort order
3. Watch for arrows: ↑ (ascending) or ↓ (descending)

**Sortable Columns:**

```
╔══════════════════╦═══════════════╦══════════════╗
║ Cryptocurrency ⇅ ║ Total Return ⇅║ Final Value ⇅║
╠══════════════════╬═══════════════╬══════════════╣
║ BTC             ║    +125.5%   ║   $22,550    ║
║ ETH             ║    +89.2%    ║   $18,920    ║
║ ADA             ║    +45.3%    ║   $14,530    ║
╚══════════════════╩═══════════════╩══════════════╝
                   ↑ Click headers to sort
```

---

## 📊 Common Workflows

### Workflow 1: Find Best Performers in 2024

```
1. Select Strategy: "RSI Buy/Sell"
2. Set Time Range:
   - Start: 2024-01-01
   - End: 2024-12-31
3. Choose: "Run Against All Cryptocurrencies"
4. Click: "Run Backtest"
5. Wait: ~20-30 seconds
6. Sort by: "Total Return (%)" (click header)
7. Result: Top performers listed first
```

**Result:**
```
Cryptocurrency  │ Total Return │ Strategy vs Hold
────────────────┼──────────────┼─────────────────
XLMUSDT ↑      │   +525.7%    │     +125.2%
RSRUSDT        │   +331.8%    │     +89.5%
TRXUSDT        │   +220.1%    │     +67.3%
```

---

### Workflow 2: Compare Recent vs Historical

**Test 1: Recent (Last 6 months)**
```
Start Date: 2024-04-01
End Date: (empty)
Run backtest → Note average return
```

**Test 2: Historical (All time)**
```
Start Date: (empty)
End Date: (empty)
Run backtest → Compare results
```

**Analysis:**
- Sort both by "Total Return %"
- Compare top 10 in each
- Identify consistent winners

---

### Workflow 3: Risk Assessment

```
1. Run backtest (any time range)
2. Sort by "Max Drawdown (%)" descending
3. Cryptos at top = highest risk
4. Cryptos at bottom = lowest risk
5. Sort by "Strategy vs Hold" ascending
6. Find low-risk, high-reward options
```

---

## 💡 Pro Tips

### Time Range Selection

**✅ DO:**
- Leave empty for complete analysis
- Use recent dates for quick tests
- Test specific years to understand market cycles
- Compare same strategy across different periods

**❌ DON'T:**
- Set start date after end date (will show error)
- Use dates before 2020 (limited data availability)
- Expect instant results with 5+ year ranges (30s+ for batch)

### Table Sorting

**✅ DO:**
- Sort by "Total Return" to find winners
- Sort by "Max Drawdown" to assess risk
- Sort by "Total Trades" to gauge activity
- Sort by "Profitable Trades" for reliability

**❌ DON'T:**
- Forget current sort when analyzing
- Assume default order is sorted (it's not)
- Overlook negative returns (sort ascending)

---

## 🎨 Visual Guide

### Time Range UI

```
┌──────────────────────────────────────────┐
│ ⚙️  Strategy Configuration               │
├──────────────────────────────────────────┤
│                                          │
│ 🎯 Backtest Mode                        │
│  ○ Run Against All Cryptocurrencies     │
│  ○ Single Cryptocurrency                │
│                                          │
│ ╔════════════════════════════════════╗  │
│ ║ 📅 Time Range (Optional)          ║  │
│ ║ Leave empty to use all data       ║  │
│ ╠════════════════════════════════════╣  │
│ ║ Start Date: [2024-01-01     ▼]    ║  │
│ ║ End Date:   [2024-12-31     ▼]    ║  │
│ ║                                    ║  │
│ ║ [✖ Clear Dates]                   ║  │
│ ╚════════════════════════════════════╝  │
│                                          │
│ 📊 Available Strategies                 │
│ [RSI Buy/Sell]  [Selected]             │
│                                          │
│ ⚡ Strategy Parameters                  │
│ [Parameter inputs...]                   │
│                                          │
│ [▶ Run Backtest]                        │
└──────────────────────────────────────────┘
```

### Sortable Table Headers

```
Before Sorting (hover):
┌─────────────────┐
│ Total Return ⇅  │  ← Neutral icon, ready to sort
└─────────────────┘

After Click 1 (descending):
┌─────────────────┐
│ Total Return ↓  │  ← Sorted highest to lowest
└─────────────────┘

After Click 2 (ascending):
┌─────────────────┐
│ Total Return ↑  │  ← Sorted lowest to highest
└─────────────────┘
```

---

## 📈 Performance Impact

### Time Range Benefits

| Range | Data Size | Speed | Use Case |
|-------|-----------|-------|----------|
| 1 month | ~720 records | ⚡⚡⚡ Very Fast | Quick tests |
| 6 months | ~4,320 records | ⚡⚡ Fast | Recent trends |
| 1 year | ~8,760 records | ⚡ Normal | Annual analysis |
| 5 years | ~43,800 records | ⏱️ Slower | Full history |

**With Optimizations:**
- Daily aggregation: 24x less data
- Parallel processing: 2.7x faster
- Combined: 10.4x faster than original

### Sorting Performance

- **Response time:** < 10ms (instant)
- **Data size:** No impact (client-side)
- **Memory:** Negligible (< 1 MB for 211 cryptos)

---

## 🔧 Troubleshooting

### Time Range Issues

**Problem:** "Start date must be before end date"
- **Fix:** Check date order, swap if needed

**Problem:** No results returned
- **Fix:** Verify dates are within available data range (2020-2025)

**Problem:** Takes very long
- **Fix:** Use shorter date range or run single crypto first

### Sorting Issues

**Problem:** Column won't sort
- **Fix:** Refresh page, ensure results are loaded

**Problem:** Sort order seems wrong
- **Fix:** Check if sorting by correct column, look for arrow indicator

**Problem:** Lost sorted view
- **Fix:** Click header again to re-sort

---

## 📞 Quick Reference

**Default Behavior:**
- Time range: ALL available data (5+ years)
- Sort order: NONE (API order, usually by return)
- Processing: PARALLEL (2.7x faster)

**Keyboard Shortcuts:**
- None currently (future enhancement)

**Export:**
- CSV export uses current display order
- Includes date range in metadata

**Performance:**
- Single backtest: ~0.33 seconds
- Batch (48 cryptos): ~5-6 seconds
- Batch (211 cryptos): ~20-30 seconds

---

*Quick Guide Version 1.0*  
*Last Updated: October 5, 2025*  
*For detailed docs: see UI_ENHANCEMENTS_TIME_AND_SORTING.md*
