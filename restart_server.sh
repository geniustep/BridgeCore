#!/bin/bash
# Script to restart BridgeCore server

cd /opt/BridgeCore

echo "Stopping existing server..."
pkill -9 -f "uvicorn.*app.main:app" 2>/dev/null
sleep 2

echo "Starting server..."
# Use python3.11 if available, otherwise fallback to python3
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD=python3.11
elif command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
else
    echo "❌ Python not found!"
    exit 1
fi

# Try to use run_server.py first, fallback to direct uvicorn
if [ -f "run_server.py" ]; then
    nohup $PYTHON_CMD run_server.py > logs/server.log 2>&1 &
else
    nohup $PYTHON_CMD -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > logs/server.log 2>&1 &
fi

sleep 3

if ps aux | grep -q "[u]vicorn.*app.main:app"; then
    echo "✅ Server started successfully!"
    echo "PID: $(ps aux | grep '[u]vicorn.*app.main:app' | grep -v grep | awk '{print $2}')"
    echo "Logs: tail -f logs/server.log"
else
    echo "❌ Server failed to start. Check logs/server.log"
    tail -20 logs/server.log 2>/dev/null
fi




