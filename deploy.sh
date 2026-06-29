#!/bin/bash
# Script to deploy BridgeCore to bridgecore.geniura.com

set -e

echo "🚀 Starting BridgeCore deployment..."

cd /opt/BridgeCore/docker

echo "📦 Building Docker images..."
docker-compose build --no-cache api

echo "🔄 Restarting services..."
docker-compose up -d --force-recreate api

echo "⏳ Waiting for API to be healthy..."
sleep 10

echo "✅ Checking API health..."
curl -f http://localhost:8000/health || echo "⚠️  Health check failed, but deployment completed"

echo "✅ Deployment completed!"
echo "🌐 API is available at: https://bridgecore.geniura.com"
echo "📚 API Docs: https://bridgecore.geniura.com/docs"
