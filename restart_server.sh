#!/bin/bash
# Script to restart BridgeCore server

cd /opt/BridgeCore

echo "Stopping existing server..."
pkill -9 -f "uvicorn.*app.main:app" 2>/dev/null
sleep 2

echo "Starting server..."
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > logs/server.log 2>&1 &

sleep 3

if ps aux | grep -q "[u]vicorn.*app.main:app"; then
    echo "✅ Server started successfully!"
    echo "PID: $(ps aux | grep '[u]vicorn.*app.main:app' | grep -v grep | awk '{print $2}')"
    echo "Logs: tail -f logs/server.log"
else
    echo "❌ Server failed to start. Check logs/server.log"
    tail -20 logs/server.log 2>/dev/null
fi




