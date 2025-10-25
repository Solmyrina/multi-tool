#!/bin/bash

# Start performance monitoring background service
cd "$(dirname "$0")"

echo "Starting performance monitoring service..."

# Check if the performance monitor is already running
PID=$(ps aux | grep 'performance_monitor.py' | grep -v grep | awk '{print $2}')
if [ ! -z "$PID" ]; then
    echo "Performance monitor already running with PID: $PID"
    exit 0
fi

# Start the performance monitor in the background
python3 performance_monitor.py > performance_monitor.log 2>&1 &
PID=$!

echo "Performance monitoring service started with PID: $PID"
echo "Log file: performance_monitor.log"

# Wait a moment to check if it started successfully
sleep 2
if ps -p $PID > /dev/null; then
    echo "Performance monitoring service is running successfully"
else
    echo "Failed to start performance monitoring service"
    exit 1
fi