# BridgeCore Deployment Guide

## Overview

This guide covers deploying BridgeCore in various environments, from local development to production.

---

## Prerequisites

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 cores | 4+ cores |
| RAM | 4 GB | 8+ GB |
| Storage | 20 GB | 50+ GB SSD |
| OS | Ubuntu 20.04+ / Debian 11+ | Ubuntu 22.04 LTS |

### Software Requirements

| Software | Version | Purpose |
|----------|---------|---------|
| Docker | 20.10+ | Containerization |
| Docker Compose | 2.0+ | Container orchestration |
| Python | 3.11+ | Backend (if not using Docker) |
| Node.js | 18+ | Admin dashboard (if not using Docker) |
| PostgreSQL | 15+ | Database |
| Redis | 7+ | Cache & rate limiting |

---

## Deployment Options

### Option 1: Docker Compose (Recommended)

The easiest way to deploy BridgeCore.

#### Step 1: Clone Repository

```bash
git clone https://github.com/geniustep/BridgeCore.git
cd BridgeCore
```

#### Step 2: Configure Environment

```bash
cp env.example .env
```

Edit `.env` with your settings:

```bash
nano .env
```

**Important settings to change:**
```env
SECRET_KEY=generate-a-secure-random-key-here
JWT_SECRET_KEY=generate-another-secure-key-here
ADMIN_SECRET_KEY=generate-third-secure-key-here
DATABASE_URL=postgresql+asyncpg://postgres:your_password@db:5432/bridgecore
```

#### Step 3: Build and Start

```bash
docker-compose up -d --build
```

#### Step 4: Run Migrations

```bash
docker-compose exec api alembic upgrade head
```

#### Step 5: Seed Initial Data

```bash
docker-compose exec api python scripts/seed_admin.py
```

#### Step 6: Verify Deployment

```bash
# Check all services are running
docker-compose ps

# Check API health
curl http://localhost:8000/health

# Check admin dashboard
open http://localhost:3000
```

### Option 2: Manual Deployment

For environments without Docker.

#### Step 1: Install Dependencies

**Ubuntu/Debian:**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Install Redis
sudo apt install redis-server -y
```

#### Step 2: Setup Database

```bash
# Login to PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE USER bridgecore WITH PASSWORD 'your_password';
CREATE DATABASE bridgecore_db OWNER bridgecore;
GRANT ALL PRIVILEGES ON DATABASE bridgecore_db TO bridgecore;
\q
```

#### Step 3: Configure Redis

```bash
# Edit Redis config
sudo nano /etc/redis/redis.conf

# Set password (find and modify)
requirepass your_redis_password

# Restart Redis
sudo systemctl restart redis
```

#### Step 4: Setup Backend

```bash
cd BridgeCore

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp env.example .env
nano .env  # Edit with your settings

# Run migrations
alembic upgrade head

# Seed data
python scripts/seed_admin.py
```

#### Step 5: Setup Admin Dashboard

```bash
cd admin

# Install dependencies
npm install

# Build for production
npm run build
```

#### Step 6: Setup Systemd Services

**API Service (`/etc/systemd/system/bridgecore-api.service`):**
```ini
[Unit]
Description=BridgeCore API
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=bridgecore
WorkingDirectory=/opt/bridgecore
Environment=PATH=/opt/bridgecore/venv/bin
ExecStart=/opt/bridgecore/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Celery Worker (`/etc/systemd/system/bridgecore-celery.service`):**
```ini
[Unit]
Description=BridgeCore Celery Worker
After=network.target redis.service

[Service]
Type=simple
User=bridgecore
WorkingDirectory=/opt/bridgecore
Environment=PATH=/opt/bridgecore/venv/bin
ExecStart=/opt/bridgecore/venv/bin/celery -A app.celery_app worker --loglevel=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Celery Beat (`/etc/systemd/system/bridgecore-celery-beat.service`):**
```ini
[Unit]
Description=BridgeCore Celery Beat
After=network.target redis.service

[Service]
Type=simple
User=bridgecore
WorkingDirectory=/opt/bridgecore
Environment=PATH=/opt/bridgecore/venv/bin
ExecStart=/opt/bridgecore/venv/bin/celery -A app.celery_app beat --loglevel=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start services:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable bridgecore-api bridgecore-celery bridgecore-celery-beat
sudo systemctl start bridgecore-api bridgecore-celery bridgecore-celery-beat
```

---

## Nginx Configuration

### API Reverse Proxy

```nginx
# /etc/nginx/sites-available/bridgecore-api
server {
    listen 80;
    server_name api.bridgecore.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Increase body size for file uploads
    client_max_body_size 50M;
}
```

### Admin Dashboard

```nginx
# /etc/nginx/sites-available/bridgecore-admin
server {
    listen 80;
    server_name admin.bridgecore.com;

    root /opt/bridgecore/admin/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /assets {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Enable Sites

```bash
sudo ln -s /etc/nginx/sites-available/bridgecore-api /etc/nginx/sites-enabled/
sudo ln -s /etc/nginx/sites-available/bridgecore-admin /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## SSL/TLS with Let's Encrypt

### Install Certbot

```bash
sudo apt install certbot python3-certbot-nginx -y
```

### Obtain Certificates

```bash
# For API
sudo certbot --nginx -d api.bridgecore.com

# For Admin
sudo certbot --nginx -d admin.bridgecore.com
```

### Auto-Renewal

Certbot automatically adds a cron job. Verify with:

```bash
sudo certbot renew --dry-run
```

---

## Docker Compose for Production

### Production `docker-compose.yml`

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: bridgecore-api
    restart: always
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - ADMIN_SECRET_KEY=${ADMIN_SECRET_KEY}
      - ENVIRONMENT=production
      - DEBUG=False
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G

  admin-dashboard:
    build:
      context: ./admin
      dockerfile: Dockerfile
    container_name: bridgecore-admin
    restart: always
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=${API_URL}
    depends_on:
      - api

  celery-worker:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: bridgecore-celery-worker
    restart: always
    command: celery -A app.celery_app worker --loglevel=info --concurrency=4
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - CELERY_BROKER_URL=${CELERY_BROKER_URL}
    depends_on:
      - db
      - redis
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G

  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: bridgecore-celery-beat
    restart: always
    command: celery -A app.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - CELERY_BROKER_URL=${CELERY_BROKER_URL}
    depends_on:
      - db
      - redis

  db:
    image: postgres:15-alpine
    container_name: bridgecore-db
    restart: always
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: bridgecore-redis
    restart: always
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  prometheus:
    image: prom/prometheus:latest
    container_name: bridgecore-prometheus
    restart: always
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    container_name: bridgecore-grafana
    restart: always
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
```

---

## Database Backups

### Automated Backup Script

Create `/opt/bridgecore/scripts/backup.sh`:

```bash
#!/bin/bash

# Configuration
BACKUP_DIR="/opt/bridgecore/backups"
RETENTION_DAYS=30
DB_NAME="bridgecore_db"
DB_USER="bridgecore"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
docker-compose exec -T db pg_dump -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Remove old backups
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +$RETENTION_DAYS -delete

# Log
echo "[$DATE] Backup completed: db_$DATE.sql.gz" >> $BACKUP_DIR/backup.log
```

### Schedule with Cron

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /opt/bridgecore/scripts/backup.sh
```

### Restore from Backup

```bash
# Restore database
gunzip < /opt/bridgecore/backups/db_20251121_020000.sql.gz | \
  docker-compose exec -T db psql -U bridgecore bridgecore_db
```

---

## Monitoring Setup

### Prometheus Configuration

Create `monitoring/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'bridgecore-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'postgres'
    static_configs:
      - targets: ['db:5432']
```

### Grafana Dashboards

Import dashboards from `monitoring/grafana/dashboards/`:
- `api-performance.json`
- `tenant-usage.json`
- `system-health.json`

---

## Scaling

### Horizontal Scaling with Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml bridgecore

# Scale API
docker service scale bridgecore_api=3

# Scale workers
docker service scale bridgecore_celery-worker=5
```

### Load Balancing

For multiple API instances, use Nginx upstream:

```nginx
upstream bridgecore_api {
    least_conn;
    server api1:8000 weight=1;
    server api2:8000 weight=1;
    server api3:8000 weight=1;
}

server {
    listen 80;
    server_name api.bridgecore.com;

    location / {
        proxy_pass http://bridgecore_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Security Checklist

### Before Production

- [ ] Change all default passwords
- [ ] Generate secure random keys for SECRET_KEY, JWT_SECRET_KEY, ADMIN_SECRET_KEY
- [ ] Enable HTTPS/TLS
- [ ] Configure proper CORS origins
- [ ] Set DEBUG=False and ENVIRONMENT=production
- [ ] Configure firewall (UFW/iptables)
- [ ] Disable root SSH login
- [ ] Enable fail2ban
- [ ] Set up log rotation
- [ ] Configure backup automation

### Firewall Rules

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow API (if needed externally)
sudo ufw allow 8000/tcp

# Enable firewall
sudo ufw enable
```

---

## Troubleshooting

### Common Issues

#### API Won't Start

```bash
# Check logs
docker-compose logs api

# Common causes:
# - Database not ready
# - Invalid environment variables
# - Missing migrations
```

#### Database Connection Failed

```bash
# Check if PostgreSQL is running
docker-compose ps db

# Check connection
docker-compose exec db psql -U bridgecore -d bridgecore_db -c "SELECT 1"
```

#### Redis Connection Failed

```bash
# Check if Redis is running
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli -a your_password ping
```

#### Celery Tasks Not Running

```bash
# Check worker logs
docker-compose logs celery-worker

# Check beat logs
docker-compose logs celery-beat

# Verify Redis connection
docker-compose exec celery-worker celery -A app.celery_app inspect ping
```

### Health Check Commands

```bash
# API health
curl http://localhost:8000/health

# Database health
curl http://localhost:8000/health/db

# Redis health
curl http://localhost:8000/health/redis

# All services
docker-compose ps
```

---

## Updates and Maintenance

### Updating BridgeCore

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up -d --build

# Run new migrations
docker-compose exec api alembic upgrade head
```

### Zero-Downtime Updates

```bash
# Build new image
docker-compose build api

# Scale up new instances
docker-compose up -d --scale api=2 --no-recreate

# Wait for health checks
sleep 30

# Remove old instances
docker-compose up -d --scale api=1
```
