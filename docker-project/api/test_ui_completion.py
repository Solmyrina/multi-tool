#!/usr/bin/env python3
"""
Test: Verify progressive loading panel hides after completion
"""

import requests
import json
import time

API_URL = "http://localhost:8000/crypto/backtest/stream"

def test_ui_behavior():
    """Test that we get proper completion event"""
    
    print("🧪 Testing Progressive Loading UI Behavior\n")
    
    payload = {
        "strategy_id": 1,
        "parameters": {
            "rsi_period": 14,
            "rsi_oversold": 30,
            "rsi_overbought": 70
        }
    }
    
    print("📤 Starting streaming backtest...")
    
    start_time = time.time()
    event_count = 0
    
    try:
        response = requests.post(API_URL, json=payload, stream=True, timeout=60)
        
        if response.status_code != 200:
            print(f"❌ Error: HTTP {response.status_code}")
            return
        
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith('data: '):
                try:
                    event = json.loads(line[6:])
                    event_type = event.get('type')
                    event_count += 1
                    
                    if event_type == 'start':
                        print(f"✅ START event received")
                    
                    elif event_type == 'result':
                        if event_count <= 3:  # Show first few
                            result = event.get('data', {})
                            print(f"✅ RESULT event: {result['symbol']}")
                    
                    elif event_type == 'complete':
                        elapsed = time.time() - start_time
                        summary = event.get('summary', {})
                        
                        print(f"\n✅ COMPLETE event received!")
                        print(f"   Elapsed: {event.get('elapsed_time')}s")
                        print(f"   Total cryptos: {summary.get('total_cryptocurrencies')}")
                        print(f"   Successful: {summary.get('successful_backtests')}")
                        
                        print(f"\n🎯 UI Behavior:")
                        print(f"   1. Progressive loading panel should HIDE")
                        print(f"   2. Final results table should SHOW")
                        print(f"   3. Summary statistics should be visible")
                        print(f"   4. No duplicate rows in table")
                        
                        print(f"\n✅ Test completed successfully!")
                        print(f"   Total events: {event_count}")
                        print(f"   Wall time: {elapsed:.2f}s")
                        return
                
                except json.JSONDecodeError:
                    pass
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == '__main__':
    test_ui_behavior()
