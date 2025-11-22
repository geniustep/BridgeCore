#!/bin/bash
# Script to deploy BridgeCore updates to production server
# Usage: ./scripts/deploy_to_production.sh

set -e  # Exit on error

echo "🚀 BridgeCore Production Deployment Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/opt/BridgeCore"  # Adjust this to your production path
BRANCH="main"  # or "dev" depending on your setup
SERVICE_NAME="bridgecore"  # Adjust to your service name

# Check if running on production server
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}❌ Error: Project directory not found: $PROJECT_DIR${NC}"
    echo "Please update PROJECT_DIR in this script to match your production setup."
    exit 1
fi

cd "$PROJECT_DIR"

echo -e "${YELLOW}📦 Step 1: Fetching latest changes from GitHub...${NC}"
git fetch origin

echo -e "${YELLOW}📦 Step 2: Checking current branch...${NC}"
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"

if [ "$CURRENT_BRANCH" != "$BRANCH" ]; then
    echo -e "${YELLOW}⚠️  Switching to $BRANCH branch...${NC}"
    git checkout "$BRANCH"
fi

echo -e "${YELLOW}📦 Step 3: Pulling latest changes...${NC}"
git pull origin "$BRANCH"

echo -e "${YELLOW}📦 Step 4: Checking for uncommitted changes...${NC}"
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${RED}⚠️  Warning: There are uncommitted changes. Please commit or stash them first.${NC}"
    git status
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo -e "${YELLOW}📦 Step 5: Checking latest commit...${NC}"
LATEST_COMMIT=$(git log -1 --oneline)
echo "Latest commit: $LATEST_COMMIT"

echo ""
echo -e "${YELLOW}🔄 Step 6: Restarting service...${NC}"

# Try different service management methods
if command -v docker-compose &> /dev/null; then
    echo "Using Docker Compose..."
    docker-compose restart fastapi || docker-compose up -d --build fastapi
    echo -e "${GREEN}✅ Service restarted using Docker Compose${NC}"
elif systemctl list-units --type=service | grep -q "$SERVICE_NAME"; then
    echo "Using systemd..."
    sudo systemctl restart "$SERVICE_NAME" || sudo systemctl restart "${SERVICE_NAME}-api"
    echo -e "${GREEN}✅ Service restarted using systemd${NC}"
elif command -v pm2 &> /dev/null; then
    echo "Using PM2..."
    pm2 restart "$SERVICE_NAME" || pm2 restart "${SERVICE_NAME}-api"
    echo -e "${GREEN}✅ Service restarted using PM2${NC}"
else
    echo -e "${YELLOW}⚠️  Could not automatically restart service.${NC}"
    echo "Please restart the service manually."
fi

echo ""
echo -e "${YELLOW}⏳ Waiting 5 seconds for service to start...${NC}"
sleep 5

echo ""
echo -e "${YELLOW}🔍 Step 7: Verifying deployment...${NC}"

# Check health endpoint
if curl -f -s "https://bridgecore.geniura.com/health" > /dev/null; then
    echo -e "${GREEN}✅ Health check passed${NC}"
else
    echo -e "${RED}❌ Health check failed${NC}"
fi

# Check if new endpoint exists
if curl -f -s "https://bridgecore.geniura.com/openapi.json" | grep -q "tenant/login"; then
    echo -e "${GREEN}✅ New endpoint /api/v1/auth/tenant/login is available${NC}"
else
    echo -e "${YELLOW}⚠️  New endpoint not found yet. Service may need more time to start.${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Deployment completed!${NC}"
echo ""
echo "Test the new endpoint:"
echo "curl -X POST 'https://bridgecore.geniura.com/api/v1/auth/tenant/login' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"email\": \"user@done.com\", \"password\": \"done123\"}'"

