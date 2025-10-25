#!/usr/bin/env python3
from crypto_service import CryptoDataService

def check_data_structure():
    service = CryptoDataService()
    top_cryptos = service.get_top_cryptocurrencies(5)  # Just get 5 for testing
    
    print(f"Found {len(top_cryptos)} cryptocurrencies")
    if top_cryptos:
        print("\nFirst crypto data structure:")
        for key, value in top_cryptos[0].items():
            print(f"   {key}: {value}")
            
        print("\nTop 5 symbols:")
        for i, crypto in enumerate(top_cryptos):
            print(f"   {i+1}. {crypto.get('binance_symbol', 'Unknown')}")

if __name__ == "__main__":
    check_data_structure()