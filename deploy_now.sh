#!/bin/bash
# BridgeCore Production Deployment - All Methods
# Execute this on the production server

set -e

cd /opt/BridgeCore

echo "📦 Step 1: Updating code..."
git fetch origin
git pull origin main

echo ""
echo "🔄 Step 2: Trying to restart service..."

# Method 1: Docker Compose
if command -v docker-compose &> /dev/null; then
    if docker-compose ps 2>/dev/null | grep -q fastapi; then
        echo "🐳 Found Docker Compose, restarting..."
        docker-compose restart fastapi
        echo "✅ Restarted via Docker Compose"
        sleep 5
        exit 0
    fi
fi

# Method 2: Docker
if command -v docker &> /dev/null; then
    CONTAINER=$(docker ps -q --filter "name=bridgecore" --filter "name=fastapi" --filter "name=api" | head -1)
    if [ ! -z "$CONTAINER" ]; then
        echo "🐳 Found Docker container, restarting..."
        docker restart $CONTAINER
        echo "✅ Restarted via Docker"
        sleep 5
        exit 0
    fi
fi

# Method 3: PM2
if command -v pm2 &> /dev/null; then
    if pm2 list 2>/dev/null | grep -q bridgecore; then
        echo "📦 Found PM2 process, restarting..."
        pm2 restart bridgecore
        echo "✅ Restarted via PM2"
        sleep 5
        exit 0
    fi
    if pm2 list 2>/dev/null | grep -q fastapi; then
        echo "📦 Found PM2 process, restarting..."
        pm2 restart fastapi
        echo "✅ Restarted via PM2"
        sleep 5
        exit 0
    fi
fi

# Method 4: systemd
for service in bridgecore bridgecore-api fastapi bridgecore-fastapi api; do
    if systemctl list-units --type=service --all 2>/dev/null | grep -q "$service.service"; then
        echo "⚙️ Found systemd service: $service, restarting..."
        systemctl restart "$service"
        echo "✅ Restarted via systemd: $service"
        sleep 5
        exit 0
    fi
done

# Method 5: supervisor
if command -v supervisorctl &> /dev/null; then
    if supervisorctl status 2>/dev/null | grep -q bridgecore; then
        echo "👷 Found supervisor process, restarting..."
        supervisorctl restart bridgecore
        echo "✅ Restarted via supervisor"
        sleep 5
        exit 0
    fi
fi

# Method 6: Find and restart process
PID=$(ps aux | grep -E "uvicorn.*app.main|python.*app.main|gunicorn.*app.main" | grep -v grep | awk '{print $2}' | head -1)
if [ ! -z "$PID" ]; then
    echo "🔍 Found process PID: $PID, sending HUP signal..."
    kill -HUP $PID 2>/dev/null || kill $PID 2>/dev/null
    echo "✅ Sent signal to process"
    sleep 5
    exit 0
fi

echo "❌ Could not automatically restart service."
echo ""
echo "Please check manually:"
echo "  - docker-compose ps"
echo "  - docker ps"
echo "  - pm2 list"
echo "  - systemctl list-units | grep bridge"
echo "  - ps aux | grep uvicorn"

