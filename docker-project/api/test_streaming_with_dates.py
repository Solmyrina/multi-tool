#!/usr/bin/env python3
"""
Quick Test - Test streaming with Bitcoin only to see actual returns
"""

import requests
import json
import time

API_URL = "http://localhost:8000/crypto/backtest/stream"

def test_single_streaming():
    """Test with limited cryptos to see real returns"""
    
    print("🚀 Quick Test: Streaming with Real Returns")
    print("=" * 60)
    
    # Test with date range for actual trading
    payload = {
        "strategy_id": 1,  # RSI strategy
        "parameters": {
            "rsi_period": 14,
            "rsi_oversold": 30,
            "rsi_overbought": 70
        },
        "interval": "1d",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
    }
    
    print(f"\n📤 Testing RSI strategy for 2024 full year")
    print(f"   Date range: 2024-01-01 to 2024-12-31")
    
    start_time = time.time()
    
    try:
        response = requests.post(API_URL, json=payload, stream=True, timeout=300)
        
        if response.status_code != 200:
            print(f"❌ Error: HTTP {response.status_code}")
            return
        
        print("\n📊 Real-time Results:\n")
        
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith('data: '):
                data = json.loads(line[6:])
                event_type = data.get('type')
                
                if event_type == 'result':
                    result = data.get('data', {})
                    progress = data.get('progress', {})
                    
                    win_rate = (result['profitable_trades'] / result['total_trades'] * 100) if result['total_trades'] > 0 else 0
                    
                    print(f"  {result['symbol']:12s} | Return: {result['total_return']:+8.2f}% | " +
                          f"Trades: {result['total_trades']:3d} | " +
                          f"Win: {result['profitable_trades']}/{result['total_trades']} ({win_rate:5.1f}%) | " +
                          f"[{progress['completed']}/{progress['total']}]")
                
                elif event_type == 'complete':
                    summary = data.get('summary', {})
                    elapsed = data.get('elapsed_time', 0)
                    
                    print(f"\n{'='*60}")
                    print(f"✅ Completed in {elapsed:.2f}s")
                    print(f"\n📈 Performance Summary:")
                    print(f"   Successful Tests: {summary.get('successful_backtests')}")
                    print(f"   Average Return: {summary.get('average_return'):+.2f}%")
                    print(f"   Positive Returns: {summary.get('positive_returns_count')}")
                    
                    best = summary.get('best_performing')
                    if best:
                        print(f"   🏆 Best: {best.get('symbol')} (+{best.get('return')}%)")
                    
                    worst = summary.get('worst_performing')
                    if worst:
                        print(f"   📉 Worst: {worst.get('symbol')} ({worst.get('return')}%)")
        
        elapsed_time = time.time() - start_time
        print(f"\n⏱️  Total wall time: {elapsed_time:.2f}s")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == '__main__':
    test_single_streaming()
