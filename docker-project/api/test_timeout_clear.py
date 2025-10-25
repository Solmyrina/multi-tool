#!/usr/bin/env python3
"""
Test script to demonstrate clearing the API timeout manually
"""

import os
import json
from datetime import datetime

TIMEOUT_FILE = '/app/api_timeout.json'

def clear_timeout():
    """Clear the API timeout manually for testing"""
    if os.path.exists(TIMEOUT_FILE):
        print("⏰ Timeout file exists - clearing it...")
        os.remove(TIMEOUT_FILE)
        print("✅ Timeout cleared - next run will attempt API calls")
    else:
        print("ℹ️  No timeout file found")

def show_timeout_status():
    """Show current timeout status"""
    if os.path.exists(TIMEOUT_FILE):
        with open(TIMEOUT_FILE, 'r') as f:
            timeout_data = json.load(f)
        
        timeout_time = datetime.fromisoformat(timeout_data['timeout_until'])
        current_time = datetime.now()
        
        if current_time < timeout_time:
            remaining = timeout_time - current_time
            hours_remaining = remaining.total_seconds() / 3600
            print(f"🚫 API timeout active - {hours_remaining:.1f} hours remaining")
            print(f"   Timeout until: {timeout_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Reason: {timeout_data['reason']}")
        else:
            print("✅ Timeout expired")
    else:
        print("✅ No active timeout")

if __name__ == "__main__":
    print("📊 Current API timeout status:")
    show_timeout_status()
    
    print("\n🧹 Clearing timeout for testing...")
    clear_timeout()
    
    print("\n📊 Status after clearing:")
    show_timeout_status()