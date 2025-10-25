#!/usr/bin/env python3
"""
Cryptocurrency Service Configuration Checker
Shows current API configuration and upgrade options
"""

import requests
import json

def check_crypto_config():
    """Check current cryptocurrency service configuration"""
    print("🔍 Checking Cryptocurrency Service Configuration...\n")
    
    # Try to connect to the API through different endpoints
    base_urls = [
        "https://localhost/api",  # Through nginx with SSL
        "http://localhost/api",   # Through nginx without SSL  
        "http://localhost:8000"   # Direct to API (fallback)
    ]
    
    config = None
    api_url = None
    
    for url in base_urls:
        try:
            response = requests.get(f"{url}/crypto/config", verify=False, timeout=5)
            if response.status_code == 200:
                config = response.json()
                api_url = url
                break
        except Exception:
            continue
    
    if not config:
        print("❌ Error: Cannot connect to API. Make sure containers are running.")
        print("� Try: docker-compose up -d")
        return
        
    print(f"🌐 Connected via: {api_url}")
    print("\n�📊 Current Configuration:")
    print(f"   Performance Tier: {config['configuration']['performance_tier']}")
    print(f"   Rate Limit: {config['configuration']['rate_limit_per_minute']:,} requests/minute")
    print(f"   API Key Configured: {'✅ Yes' if config['configuration']['api_key_configured'] else '❌ No'}")
    print(f"   Status: {config['status'].title()}")
    
    if config['configuration']['upgrade_available']:
        print("\n🚀 Upgrade Available!")
        print("   Benefits: 5x faster data collection")
        print("   📋 Upgrade Instructions:")
        for step, instruction in config['configuration']['upgrade_instructions'].items():
            if step.startswith('step'):
                print(f"      {step}: {instruction}")
            elif step == 'benefit':
                print(f"      ✨ Benefit: {instruction}")
    else:
        print("\n✅ Premium configuration active!")

if __name__ == "__main__":
    check_crypto_config()