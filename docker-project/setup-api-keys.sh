#!/bin/bash
# API Keys Setup Script

echo "🔑 Stock API Keys Setup"
echo "======================="
echo ""

# Check if .env already exists
if [ -f .env ]; then
    echo "⚠️  .env file already exists. Backing up to .env.backup"
    cp .env .env.backup
fi

# Copy template
cp .env.template .env
echo "✅ Created .env file from template"

echo ""
echo "📋 Please get your FREE API keys from:"
echo ""
echo "1️⃣  Alpha Vantage (RECOMMENDED - Most reliable)"
echo "   🌐 https://www.alphavantage.co/support/#api-key"
echo "   📊 Free: 5 requests/minute, 500/day"
echo ""
echo "2️⃣  Finnhub (Good for real-time data)"
echo "   🌐 https://finnhub.io/register"
echo "   📊 Free: 60 calls/minute"
echo ""
echo "3️⃣  IEX Cloud (Generous monthly limit)"
echo "   🌐 https://iexcloud.io/console/"
echo "   📊 Free: 50,000 requests/month"
echo ""

echo "📝 Next steps:"
echo "1. Get at least ONE API key from above (Alpha Vantage recommended)"
echo "2. Edit the .env file: nano .env"
echo "3. Replace 'your_xxx_key_here' with your actual API keys"
echo "4. Restart containers: docker compose down && docker compose up -d"
echo ""

# Function to set API key
set_api_key() {
    local service=$1
    local var_name=$2
    
    echo -n "Enter your $service API key (or press Enter to skip): "
    read api_key
    
    if [ ! -z "$api_key" ]; then
        # Use sed to replace the placeholder in .env file
        sed -i "s/${var_name}=your_.*_key_here/${var_name}=${api_key}/g" .env
        echo "✅ $service API key configured"
    else
        echo "⏭️  Skipped $service"
    fi
    echo ""
}

echo "🔧 Would you like to enter your API keys now? (y/n)"
read -n 1 configure_now
echo ""

if [ "$configure_now" = "y" ] || [ "$configure_now" = "Y" ]; then
    echo ""
    echo "🔑 Configure API Keys:"
    echo "====================="
    
    set_api_key "Alpha Vantage" "ALPHA_VANTAGE_API_KEY"
    set_api_key "Finnhub" "FINNHUB_API_KEY"
    set_api_key "IEX Cloud" "IEX_CLOUD_API_KEY"
    
    echo "✅ Configuration complete!"
    echo ""
    echo "🚀 Restart containers to apply changes:"
    echo "   docker compose down && docker compose up -d"
else
    echo ""
    echo "⚡ Quick setup: nano .env"
    echo "📋 Edit the .env file manually with your API keys"
fi

echo ""
echo "🧪 Test your setup with: docker exec docker-project-api python -c \"
import os
print('API Keys Status:')
print(f'Alpha Vantage: {\"✅ Set\" if os.environ.get(\"ALPHA_VANTAGE_API_KEY\") else \"❌ Missing\"}')
print(f'Finnhub: {\"✅ Set\" if os.environ.get(\"FINNHUB_API_KEY\") else \"❌ Missing\"}')
print(f'IEX Cloud: {\"✅ Set\" if os.environ.get(\"IEX_CLOUD_API_KEY\") else \"❌ Missing\"}')
\""