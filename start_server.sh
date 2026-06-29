#!/bin/bash
# Script to start BridgeCore server

cd /opt/BridgeCore

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Start server
echo "Starting BridgeCore server on port 8000..."
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload