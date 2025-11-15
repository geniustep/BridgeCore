#!/bin/bash

# BridgeCore Setup Script
# This script sets up the BridgeCore project in a Docker container

set -e

PROJECT_DIR="/opt/BridgeCore"
DOMAIN="bridgecore.geniura.com"

echo "=========================================="
echo "BridgeCore Setup Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    print_error "Please run as root (use sudo)"
    exit 1
fi

# Navigate to project directory
cd "$PROJECT_DIR" || exit 1

# Check if .env exists
if [ -f ".env" ]; then
    print_warning ".env file already exists"
    read -p "Do you want to overwrite it? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Keeping existing .env file"
        SKIP_ENV=true
    fi
fi

if [ "$SKIP_ENV" != true ]; then
    print_info "Generating secure keys..."
    SECRET_KEY=$(openssl rand -base64 32)
    JWT_SECRET_KEY=$(openssl rand -base64 32)
    
    print_info "Creating .env file..."
    cat > .env << EOF
# Application Configuration
APP_NAME=FastAPI Middleware
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=${SECRET_KEY}
HOST=0.0.0.0
PORT=8000

# Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/middleware_db
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Redis Configuration
REDIS_URL=redis://redis:6379/0
CACHE_TTL=300

# JWT Configuration
JWT_SECRET_KEY=${JWT_SECRET_KEY}
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE_PATH=logs/app.log
LOG_ROTATION=10 MB

# CORS Configuration
CORS_ORIGINS=https://${DOMAIN},http://${DOMAIN}

# Rate Limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_PER_MINUTE=60

# Monitoring (Optional)
SENTRY_DSN=

# Celery (Optional)
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2
EOF

    chmod 600 .env
    print_info "Environment file created"
    echo ""
fi

# Create logs directory
print_info "Creating logs directory..."
mkdir -p logs
chmod 755 logs

# Create SSL directory for nginx
print_info "Creating SSL directory..."
mkdir -p docker/ssl
chmod 755 docker/ssl

# Build and start Docker containers
print_info "Building Docker images..."
cd docker
docker-compose build

print_info "Starting Docker containers..."
docker-compose up -d

# Wait for services to be ready
print_info "Waiting for services to start..."
sleep 10

# Check if containers are running
if docker-compose ps | grep -q "Up"; then
    print_info "Containers are running"
else
    print_error "Some containers failed to start"
    docker-compose ps
    exit 1
fi

# Run database migrations
print_info "Running database migrations..."
sleep 5
docker-compose exec -T api alembic upgrade head || print_warning "Migrations may have failed, check logs"

echo ""
echo "=========================================="
print_info "Setup completed successfully!"
echo "=========================================="
echo ""
echo "Services are running:"
echo "  - API: http://${DOMAIN}"
echo "  - API Docs: http://${DOMAIN}/docs"
echo "  - Health Check: http://${DOMAIN}/health"
echo ""
echo "Container names:"
echo "  - bridgecore_api"
echo "  - bridgecore_db"
echo "  - bridgecore_redis"
echo "  - bridgecore_nginx"
echo ""
echo "Useful commands:"
echo "  - View logs: cd $PROJECT_DIR/docker && docker-compose logs -f"
echo "  - Stop services: cd $PROJECT_DIR/docker && docker-compose down"
echo "  - Restart services: cd $PROJECT_DIR/docker && docker-compose restart"
echo ""
print_warning "Make sure your DNS is configured to point ${DOMAIN} to this server's IP address"
echo ""

