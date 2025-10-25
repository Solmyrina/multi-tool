#!/usr/bin/env python3
"""
Test Redis Cache Performance
Demonstrates the speed improvement from Redis caching
"""

import sys
import time
from datetime import datetime
from crypto_backtest_service import CryptoBacktestService
from cache_service import get_cache_service

def test_cache_performance():
    """Test backtest performance with and without caching"""
    
    print("=" * 80)
    print("🚀 REDIS CACHE PERFORMANCE TEST")
    print("=" * 80)
    print()
    
    # Initialize service
    service = CryptoBacktestService()
    cache = get_cache_service()
    
    # Display cache status
    print("📊 Cache Status:")
    stats = cache.get_stats()
    if stats.get('enabled'):
        print(f"   ✅ Redis connected: {stats['host']}:{stats['port']}")
        print(f"   📦 Memory used: {stats['used_memory']}")
        print(f"   🎯 Total keys: {stats['total_keys']}")
        print()
    else:
        print(f"   ❌ Redis not available: {stats.get('error', 'Unknown')}")
        print()
        return
    
    # Test parameters
    crypto_id = 1  # Bitcoin
    strategy_id = 1  # RSI Strategy
    parameters = {
        'rsi_period': 14,
        'oversold_threshold': 30,
        'overbought_threshold': 70,
        'initial_investment': 10000,
        'transaction_fee': 0.1,
        'cooldown_value': 0,
        'cooldown_unit': 'hours'
    }
    
    print("🧪 Test Configuration:")
    print(f"   Crypto: Bitcoin (ID: {crypto_id})")
    print(f"   Strategy: RSI Buy/Sell (ID: {strategy_id})")
    print(f"   Parameters: RSI Period={parameters['rsi_period']}, Oversold={parameters['oversold_threshold']}, Overbought={parameters['overbought_threshold']}")
    print()
    
    # Test 1: First run (no cache) - force refresh
    print("-" * 80)
    print("TEST 1: First Run (No Cache) - Computing fresh result")
    print("-" * 80)
    
    start = time.time()
    result1 = service.run_backtest(
        strategy_id=strategy_id,
        crypto_id=crypto_id,
        parameters=parameters,
        start_date='2024-01-01',
        end_date='2024-12-31',
        interval='1d',
        force_refresh=True  # Skip cache
    )
    time1 = time.time() - start
    
    if result1.get('success'):
        print(f"   ✅ Success!")
        print(f"   ⏱️  Time: {time1*1000:.2f}ms ({time1:.4f}s)")
        print(f"   💰 Total Return: {result1['total_return']:.2f}%")
        print(f"   📈 Trades: {result1['total_trades']}")
        print(f"   🎯 From Cache: {result1.get('from_cache', False)}")
    else:
        print(f"   ❌ Failed: {result1.get('error')}")
        return
    
    print()
    
    # Wait a moment
    time.sleep(0.5)
    
    # Test 2: Second run (cached)
    print("-" * 80)
    print("TEST 2: Second Run (Cached) - Retrieving from cache")
    print("-" * 80)
    
    start = time.time()
    result2 = service.run_backtest(
        strategy_id=strategy_id,
        crypto_id=crypto_id,
        parameters=parameters,
        start_date='2024-01-01',
        end_date='2024-12-31',
        interval='1d',
        force_refresh=False  # Use cache
    )
    time2 = time.time() - start
    
    if result2.get('success'):
        print(f"   ✅ Success!")
        print(f"   ⏱️  Time: {time2*1000:.2f}ms ({time2:.4f}s)")
        print(f"   💰 Total Return: {result2['total_return']:.2f}%")
        print(f"   📈 Trades: {result2['total_trades']}")
        print(f"   🎯 From Cache: {result2.get('from_cache', False)}")
    else:
        print(f"   ❌ Failed: {result2.get('error')}")
        return
    
    print()
    
    # Test 3: Third run (cached again)
    print("-" * 80)
    print("TEST 3: Third Run (Still Cached) - Another cache hit")
    print("-" * 80)
    
    start = time.time()
    result3 = service.run_backtest(
        strategy_id=strategy_id,
        crypto_id=crypto_id,
        parameters=parameters,
        start_date='2024-01-01',
        end_date='2024-12-31',
        interval='1d',
        force_refresh=False
    )
    time3 = time.time() - start
    
    if result3.get('success'):
        print(f"   ✅ Success!")
        print(f"   ⏱️  Time: {time3*1000:.2f}ms ({time3:.4f}s)")
        print(f"   💰 Total Return: {result3['total_return']:.2f}%")
        print(f"   📈 Trades: {result3['total_trades']}")
        print(f"   🎯 From Cache: {result3.get('from_cache', False)}")
    else:
        print(f"   ❌ Failed: {result3.get('error')}")
        return
    
    print()
    
    # Performance comparison
    print("=" * 80)
    print("📊 PERFORMANCE COMPARISON")
    print("=" * 80)
    print()
    print(f"   First Run (No Cache):    {time1*1000:.2f}ms")
    print(f"   Second Run (Cached):     {time2*1000:.2f}ms")
    print(f"   Third Run (Cached):      {time3*1000:.2f}ms")
    print()
    
    speedup2 = time1 / time2 if time2 > 0 else 0
    speedup3 = time1 / time3 if time3 > 0 else 0
    avg_cached_time = (time2 + time3) / 2
    avg_speedup = time1 / avg_cached_time if avg_cached_time > 0 else 0
    
    print(f"   🚀 Speedup (2nd run):     {speedup2:.1f}x faster")
    print(f"   🚀 Speedup (3rd run):     {speedup3:.1f}x faster")
    print(f"   🎯 Average Speedup:       {avg_speedup:.1f}x faster")
    print()
    
    # Display updated cache stats
    print("-" * 80)
    print("📊 Updated Cache Statistics:")
    print("-" * 80)
    stats = cache.get_stats()
    print(f"   Total Keys: {stats['total_keys']}")
    print(f"   Memory Used: {stats['used_memory']}")
    print(f"   Cache Hits: {stats['keyspace_hits']}")
    print(f"   Cache Misses: {stats['keyspace_misses']}")
    print(f"   Hit Rate: {stats['hit_rate']}")
    print()
    
    print("=" * 80)
    print("✅ CACHE TEST COMPLETE!")
    print("=" * 80)
    print()
    print(f"🎉 Redis caching provides {avg_speedup:.0f}x speedup for repeated queries!")
    print("   This means users get instant results when testing the same")
    print("   crypto/strategy combination multiple times.")
    print()

if __name__ == '__main__':
    try:
        test_cache_performance()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
