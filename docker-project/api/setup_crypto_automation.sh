#!/bin/bash

# Cryptocurrency Data Collection Automation Setup
# This script sets up automated collection of cryptocurrency data

echo "🚀 Setting up Cryptocurrency Data Collection Automation..."

# Create the main collection script
cat > /usr/local/bin/crypto_collect.sh << 'EOF'
#!/bin/bash

# Cryptocurrency Data Collection Script
cd /app
python3 collect_crypto_data.py

# Check exit code
if [ $? -eq 0 ]; then
    echo "✅ Crypto data collection completed successfully"
else
    echo "❌ Crypto data collection failed"
fi
EOF

# Create the update script
cat > /usr/local/bin/crypto_update.sh << 'EOF'
#!/bin/bash

# Cryptocurrency Data Update Script  
cd /app
python3 collect_crypto_data.py update

# Check exit code
if [ $? -eq 0 ]; then
    echo "✅ Crypto data update completed successfully"
else
    echo "❌ Crypto data update failed"
fi
EOF

# Make scripts executable
chmod +x /usr/local/bin/crypto_collect.sh
chmod +x /usr/local/bin/crypto_update.sh

# Add cron jobs for automation
echo "📅 Setting up cron jobs for automated data collection..."

# Initial full collection (run once)
(crontab -l 2>/dev/null; echo "# Cryptocurrency Data Collection - Initial full collection") | crontab -

# Update every hour (at minute 30 to avoid conflicts with stock updates)
(crontab -l 2>/dev/null; echo "30 * * * * /usr/local/bin/crypto_update.sh >> /var/log/crypto_update.log 2>&1") | crontab -

# Weekly full collection (Sundays at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * 0 /usr/local/bin/crypto_collect.sh >> /var/log/crypto_collection.log 2>&1") | crontab -

# Create log directory
mkdir -p /var/log

echo "✅ Cryptocurrency automation setup completed!"
echo ""
echo "📋 Summary:"
echo "  • Collection script: /usr/local/bin/crypto_collect.sh"
echo "  • Update script: /usr/local/bin/crypto_update.sh" 
echo "  • Hourly updates: Every hour at :30 minutes"
echo "  • Weekly full collection: Sundays at 2:00 AM"
echo "  • Logs: /var/log/crypto_*.log"
echo ""
echo "🔧 Manual commands:"
echo "  • Full collection: /usr/local/bin/crypto_collect.sh"
echo "  • Update only: /usr/local/bin/crypto_update.sh"
echo "  • View cron jobs: crontab -l"
echo "  • View logs: tail -f /var/log/crypto_update.log"