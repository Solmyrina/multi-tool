#!/usr/bin/env python3
"""
Test Progressive Loading SSE Endpoint
Verifies streaming backtest results work correctly
"""

import requests
import json
import time

API_URL = "http://localhost:8000/crypto/backtest/stream"

def test_streaming_backtest():
    """Test the streaming backtest endpoint"""
    
    print("🚀 Testing Progressive Loading (Server-Sent Events)")
    print("=" * 60)
    
    # Test data - RSI strategy with simple parameters
    payload = {
        "strategy_id": 1,  # RSI strategy
        "parameters": {
            "rsi_period": 14,
            "rsi_oversold": 30,
            "rsi_overbought": 70
        },
        "interval": "1d"
    }
    
    print(f"\n📤 Sending request to: {API_URL}")
    print(f"   Strategy: RSI")
    print(f"   Testing all cryptocurrencies with streaming...")
    
    start_time = time.time()
    events_received = 0
    results_count = 0
    
    try:
        # Make streaming request
        response = requests.post(
            API_URL,
            json=payload,
            stream=True,  # Enable streaming
            timeout=300
        )
        
        if response.status_code != 200:
            print(f"❌ Error: HTTP {response.status_code}")
            print(response.text)
            return
        
        print("\n📡 Streaming events:\n")
        
        # Process SSE stream
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith('data: '):
                events_received += 1
                
                try:
                    # Parse JSON event
                    data = json.loads(line[6:])  # Remove 'data: ' prefix
                    event_type = data.get('type')
                    
                    if event_type == 'start':
                        total = data.get('total', 0)
                        print(f"🟢 START: {data.get('message')} ({total} cryptos)")
                    
                    elif event_type == 'result':
                        results_count += 1
                        result_data = data.get('data', {})
                        progress = data.get('progress', {})
                        
                        symbol = result_data.get('symbol')
                        total_return = result_data.get('total_return', 0)
                        
                        print(f"✅ RESULT #{results_count}: {symbol} = {total_return:+.2f}% | " +
                              f"Progress: {progress.get('completed')}/{progress.get('total')} " +
                              f"({progress.get('percent')}%)")
                    
                    elif event_type == 'progress':
                        progress = data.get('progress', {})
                        print(f"⏳ PROGRESS: {progress.get('completed')}/{progress.get('total')} " +
                              f"({progress.get('percent')}%) - {data.get('message', '')}")
                    
                    elif event_type == 'complete':
                        elapsed = data.get('elapsed_time', 0)
                        summary = data.get('summary', {})
                        
                        print(f"\n🎉 COMPLETE: {data.get('message')}")
                        print(f"\n📊 Final Summary:")
                        print(f"   Total Cryptos: {summary.get('total_cryptocurrencies')}")
                        print(f"   Successful: {summary.get('successful_backtests')}")
                        print(f"   Failed: {summary.get('failed_backtests')}")
                        print(f"   Average Return: {summary.get('average_return')}%")
                        print(f"   Positive Returns: {summary.get('positive_returns_count')}")
                        
                        best = summary.get('best_performing')
                        if best:
                            print(f"   Best: {best.get('symbol')} (+{best.get('return')}%)")
                        
                        worst = summary.get('worst_performing')
                        if worst:
                            print(f"   Worst: {worst.get('symbol')} ({worst.get('return')}%)")
                    
                    elif event_type == 'error':
                        print(f"❌ ERROR: {data.get('message')}")
                
                except json.JSONDecodeError as e:
                    print(f"⚠️  Failed to parse event: {e}")
        
        elapsed_time = time.time() - start_time
        
        print("\n" + "=" * 60)
        print(f"✅ Test completed successfully!")
        print(f"   Events received: {events_received}")
        print(f"   Results received: {results_count}")
        print(f"   Total time: {elapsed_time:.2f}s")
        print(f"   Average time per crypto: {elapsed_time / results_count:.2f}s" if results_count > 0 else "")
        
    except requests.exceptions.Timeout:
        print(f"❌ Request timed out after 5 minutes")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_streaming_backtest()
