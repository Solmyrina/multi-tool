#!/usr/bin/env python3
"""
Benchmark script to test backtest performance improvements
Tests before/after optimization changes
"""

import sys
import time
sys.path.append('/app')

from crypto_backtest_service import CryptoBacktestService

def benchmark_data_fetching():
    """Test data fetching performance"""
    service = CryptoBacktestService()
    
    print("=" * 70)
    print("DATA FETCHING BENCHMARK")
    print("=" * 70)
    
    # Test hourly data (old way)
    print("\n1. Fetching HOURLY data (old method)...")
    start = time.time()
    df_hourly = service.get_price_data(1, use_daily_sampling=False)
    time_hourly = time.time() - start
    print(f"   ⏱️  Time: {time_hourly:.3f} seconds")
    print(f"   📊 Records: {len(df_hourly):,}")
    print(f"   💾 Memory: ~{len(df_hourly) * 48 / 1024:.1f} KB")
    
    # Test daily aggregated data (new way)
    print("\n2. Fetching DAILY aggregated data (NEW optimized method)...")
    start = time.time()
    df_daily = service.get_price_data(1, interval='1d', use_daily_sampling=True)
    time_daily = time.time() - start
    print(f"   ⏱️  Time: {time_daily:.3f} seconds")
    print(f"   📊 Records: {len(df_daily):,}")
    print(f"   💾 Memory: ~{len(df_daily) * 48 / 1024:.1f} KB")
    
    # Calculate improvement
    speedup = time_hourly / time_daily if time_daily > 0 else 0
    data_reduction = len(df_hourly) / len(df_daily) if len(df_daily) > 0 else 0
    
    print("\n" + "=" * 70)
    print("RESULTS:")
    print("=" * 70)
    print(f"⚡ Speed improvement: {speedup:.1f}x faster")
    print(f"📉 Data reduction: {data_reduction:.1f}x less data")
    print(f"💰 Time saved: {time_hourly - time_daily:.3f} seconds per crypto")
    print(f"🚀 For 211 cryptos: {(time_hourly - time_daily) * 211 / 60:.1f} minutes saved!")
    
    return df_daily

def benchmark_single_backtest(df):
    """Test single backtest performance with optimized data"""
    service = CryptoBacktestService()
    
    print("\n" + "=" * 70)
    print("SINGLE BACKTEST BENCHMARK")
    print("=" * 70)
    
    params = {
        'rsi_period': 14,
        'oversold_threshold': 30,
        'overbought_threshold': 70,
        'initial_investment': 1000,
        'transaction_fee': 0.1
    }
    
    print("\nRunning RSI backtest with optimized daily data...")
    start = time.time()
    result = service.run_backtest(1, 1, params)
    duration = time.time() - start
    
    print(f"⏱️  Backtest time: {duration:.3f} seconds")
    
    if result['success']:
        print(f"✅ Final value: ${result['final_value']:.2f}")
        print(f"📈 Total return: {result['total_return']:.2f}%")
        print(f"🔢 Total trades: {result['total_trades']}")
        print(f"💹 Win rate: {result.get('win_rate', 0):.1f}%")
    
    print("\n" + "=" * 70)
    print(f"ESTIMATED BATCH PERFORMANCE (211 cryptos):")
    print("=" * 70)
    print(f"⏱️  Sequential: ~{duration * 211 / 60:.1f} minutes")
    print(f"⚡ With parallel (8 cores): ~{duration * 211 / 8 / 60:.1f} minutes")
    print("=" * 70)

if __name__ == "__main__":
    print("\n🚀 CRYPTO BACKTESTER OPTIMIZATION BENCHMARK")
    print("Testing Phase 1 improvements: Daily sampling + Database indexes")
    print()
    
    # Run benchmarks
    df = benchmark_data_fetching()
    benchmark_single_backtest(df)
    
    print("\n✅ Benchmark complete!")
    print("\nNEXT STEPS:")
    print("  • Phase 2: Implement parallel processing for 4-8x additional speedup")
    print("  • Phase 3: Add Redis caching for instant repeated tests")
    print()
