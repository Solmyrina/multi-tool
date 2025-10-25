#!/usr/bin/env python3
"""
Test Redis Cache with Multiple Cryptocurrencies
Shows real-world performance with batch backtests
"""

import sys
import time
from crypto_backtest_service import CryptoBacktestService
from cache_service import get_cache_service

def test_batch_cache():
    """Test cache performance with multiple cryptos"""
    
    print("=" * 80)
    print("🚀 BATCH BACKTEST CACHE TEST")
    print("=" * 80)
    print()
    
    service = CryptoBacktestService()
    cache = get_cache_service()
    
    if not cache.enabled:
        print("❌ Redis cache not available")
        return
    
    # Clear cache for clean test
    cache.flush_all()
    print("🗑️  Cleared cache for clean test")
    print()
    
    # Test parameters
    strategy_id = 1  # RSI
    parameters = {
        'rsi_period': 14,
        'oversold_threshold': 30,
        'overbought_threshold': 70,
        'initial_investment': 10000,
        'transaction_fee': 0.1,
        'cooldown_value': 0,
        'cooldown_unit': 'hours'
    }
    
    print("🧪 Test: Run backtest on 10 cryptocurrencies")
    print("   Strategy: RSI Buy/Sell")
    print("   Period: 2024-01-01 to 2024-12-31")
    print()
    
    # Get first 10 cryptos
    cryptos = service.get_cryptocurrencies_with_data()[:10]
    print(f"   Selected cryptos: {', '.join([c['symbol'] for c in cryptos])}")
    print()
    
    # First run (no cache)
    print("-" * 80)
    print("RUN 1: First execution (computing all results)")
    print("-" * 80)
    
    start = time.time()
    results1 = service.run_strategy_against_all_cryptos(
        strategy_id=strategy_id,
        parameters=parameters,
        use_parallel=True,
        start_date='2024-01-01',
        end_date='2024-12-31',
        interval='1d',
        force_refresh=True  # Skip cache
    )
    time1 = time.time() - start
    
    successful1 = len([r for r in results1 if r.get('success')])
    print(f"\n   ✅ Completed: {successful1}/{len(cryptos)} successful")
    print(f"   ⏱️  Total time: {time1:.3f}s ({time1*1000:.0f}ms)")
    print(f"   ⏱️  Avg per crypto: {time1/len(cryptos)*1000:.0f}ms")
    print(f"   🎯 Cache hits: 0 (first run)")
    
    # Second run (all cached!)
    print()
    print("-" * 80)
    print("RUN 2: Second execution (all results cached)")
    print("-" * 80)
    
    start = time.time()
    results2 = service.run_strategy_against_all_cryptos(
        strategy_id=strategy_id,
        parameters=parameters,
        use_parallel=True,
        start_date='2024-01-01',
        end_date='2024-12-31',
        interval='1d',
        force_refresh=False  # Use cache
    )
    time2 = time.time() - start
    
    successful2 = len([r for r in results2 if r.get('success')])
    cached2 = len([r for r in results2 if r.get('from_cache')])
    
    print(f"\n   ✅ Completed: {successful2}/{len(cryptos)} successful")
    print(f"   ⏱️  Total time: {time2:.3f}s ({time2*1000:.0f}ms)")
    print(f"   ⏱️  Avg per crypto: {time2/len(cryptos)*1000:.0f}ms")
    print(f"   🎯 Cache hits: {cached2}/{len(cryptos)} ({cached2/len(cryptos)*100:.0f}%)")
    
    # Performance comparison
    print()
    print("=" * 80)
    print("📊 PERFORMANCE COMPARISON")
    print("=" * 80)
    print()
    print(f"   First Run (No Cache):     {time1:.3f}s")
    print(f"   Second Run (Cached):      {time2:.3f}s")
    print()
    
    speedup = time1 / time2 if time2 > 0 else 0
    print(f"   🚀 Speedup: {speedup:.1f}x faster with cache!")
    print()
    print(f"   Time saved: {(time1 - time2):.3f}s per batch")
    print(f"   For 243 cryptos: ~{(time1 - time2) * 24.3:.1f}s saved!")
    print()
    
    # Cache stats
    stats = cache.get_stats()
    print("-" * 80)
    print("📊 Cache Statistics:")
    print("-" * 80)
    print(f"   Total Keys: {stats['total_keys']}")
    print(f"   Memory Used: {stats['used_memory']}")
    print(f"   Cache Hits: {stats['keyspace_hits']}")
    print(f"   Cache Misses: {stats['keyspace_misses']}")
    print(f"   Hit Rate: {stats['hit_rate']}")
    print()
    
    print("=" * 80)
    print("✅ BATCH CACHE TEST COMPLETE!")
    print("=" * 80)
    print()

if __name__ == '__main__':
    try:
        test_batch_cache()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
