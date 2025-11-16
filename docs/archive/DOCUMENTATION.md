# BridgeCore - Comprehensive Documentation

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [API Reference](#api-reference)
7. [Odoo Version Migration (13.0 → 19.0)](#odoo-version-migration)
8. [Security](#security)
9. [Performance](#performance)
10. [Monitoring](#monitoring)
11. [Task Queue](#task-queue)
12. [WebSocket](#websocket)
13. [Deployment](#deployment)
14. [Best Practices](#best-practices)
15. [Troubleshooting](#troubleshooting)

---

## Overview

**BridgeCore** is a comprehensive FastAPI middleware that bridges Flutter applications with ERP/CRM systems (Odoo, SAP, Salesforce). It provides:

- **Universal API**: Single unified API for multiple systems
- **Smart Field Mapping**: Automatic field transformation between systems
- **Version Migration**: Seamless Odoo 13.0 → 19.0 multi-hop migration
- **Security**: JWT authentication, encryption, rate limiting
- **Performance**: Redis caching, connection pooling, circuit breakers
- **Monitoring**: Sentry error tracking, Prometheus metrics
- **Real-time**: WebSocket support for live updates
- **Scalability**: Celery task queue for heavy operations

---

## Architecture

### Design Patterns

```
┌─────────────────────────────────────────────────────────────┐
│                     Flutter Application                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      BridgeCore API                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Authentication (JWT) + Rate Limiting + Encryption   │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Field Mapping Service + Version Handler (13→19)     │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Redis Cache + Circuit Breaker + Audit Logging       │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
           │                  │                  │
           ▼                  ▼                  ▼
    ┌──────────┐      ┌──────────┐      ┌──────────┐
    │   Odoo   │      │   SAP    │      │Salesforce│
    │ 13.0-19.0│      │          │      │          │
    └──────────┘      └──────────┘      └──────────┘
```

### Core Components

1. **Adapters** (`app/adapters/`)
   - `odoo_adapter.py`: Odoo XML-RPC integration
   - Pattern: Adapter Pattern for uniform interface

2. **Services** (`app/services/`)
   - `system_service.py`: Orchestration layer
   - `field_mapping_service.py`: Field transformation
   - `version_handler_v2.py`: Multi-hop version migration
   - `odoo_versions.py`: Migration rules 13.0 → 19.0

3. **Core** (`app/core/`)
   - `security.py`: JWT authentication
   - `encryption.py`: Fernet encryption for credentials
   - `rate_limiter.py`: SlowAPI rate limiting
   - `circuit_breaker.py`: Fault tolerance
   - `monitoring.py`: Sentry + Prometheus
   - `cache.py`: Redis caching

4. **Database** (`app/models/`)
   - `user.py`: User management
   - `system.py`: System configurations
   - `audit_log.py`: Audit trail
   - `field_mapping.py`: Mapping configurations

---

## Features

### ✅ Phase 1: Core Infrastructure

- [x] Odoo adapter with smart fallback
- [x] Field mapping service
- [x] Version handler (13.0 → 19.0)
- [x] Redis caching with TTL
- [x] JWT authentication
- [x] Audit logging
- [x] Rate limiting (SlowAPI)
- [x] Encryption (Fernet)
- [x] Alembic migrations

### ✅ Phase 2: Reliability & Monitoring

- [x] Circuit Breaker pattern
- [x] Sentry error tracking
- [x] Prometheus metrics
- [x] Custom monitoring dashboards
- [x] Connection health checks

### ✅ Phase 3: Advanced Features

- [x] WebSocket real-time updates
- [x] Celery task queue
- [x] Batch operations
- [x] Report generation (PDF, Excel, CSV)
- [x] Multi-language support (EN, AR, FR)
- [x] Barcode integration

---

## Installation

### Prerequisites

```bash
# Required
Python 3.10+
PostgreSQL 13+
Redis 6+

# Optional (for production)
Docker & Docker Compose
Celery workers
Prometheus & Grafana
```

### Quick Start

```bash
# Clone repository
git clone https://github.com/yourusername/BridgeCore.git
cd BridgeCore

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run database migrations
alembic upgrade head

# Start application
uvicorn app.main:app --reload

# Access API documentation
# Open http://localhost:8000/docs
```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f app

# Stop services
docker-compose down
```

---

## Configuration

### Environment Variables

```bash
# App Settings
APP_NAME="BridgeCore API"
APP_VERSION="1.0.0"
ENVIRONMENT="development"  # development, staging, production
DEBUG=true

# Server
HOST="0.0.0.0"
PORT=8000

# Database
DATABASE_URL="postgresql://user:password@localhost:5432/bridgecore"

# Redis
REDIS_URL="redis://localhost:6379/0"
CACHE_TTL=300  # seconds

# Security
SECRET_KEY="your-secret-key-here"  # Generate with: openssl rand -hex 32
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60

# Monitoring
SENTRY_DSN="https://your-sentry-dsn@sentry.io/project-id"

# Celery
CELERY_BROKER_URL="redis://localhost:6379/1"
CELERY_RESULT_BACKEND="redis://localhost:6379/2"

# CORS
CORS_ORIGINS=["http://localhost:3000", "https://yourapp.com"]
```

### Generating Encryption Key

```python
from app.core.encryption import EncryptionService

# Generate new Fernet key
key = EncryptionService.generate_key()
print(f"Encryption Key: {key}")
```

---

## API Reference

### Authentication

#### Login

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password123"
}

# Response
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### Refresh Token

```bash
POST /api/v1/auth/refresh
Authorization: Bearer {refresh_token}

# Response
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### System Management

#### Register System

```bash
POST /api/v1/systems
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "system_id": "odoo_main",
  "system_type": "odoo",
  "system_version": "17.0",
  "name": "Odoo Production",
  "description": "Main Odoo instance",
  "connection_config": {
    "url": "https://odoo.example.com",
    "database": "production",
    "username": "admin",
    "password": "secret123"
  }
}

# Response
{
  "id": 1,
  "system_id": "odoo_main",
  "system_type": "odoo",
  "system_version": "17.0",
  "is_active": true,
  "created_at": "2024-01-15T12:00:00Z"
}
```

### CRUD Operations

#### Create Record

```bash
POST /api/v1/systems/{system_id}/crud
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "action": "create",
  "model": "res.partner",
  "data": {
    "name": "Ahmed Al-Saudi",
    "email": "ahmed@example.com",
    "phone": "+966501234567",
    "is_company": false
  }
}

# Response
{
  "success": true,
  "result": {
    "id": 123,
    "name": "Ahmed Al-Saudi",
    "email": "ahmed@example.com"
  }
}
```

#### Read Records

```bash
POST /api/v1/systems/{system_id}/crud
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "action": "read",
  "model": "res.partner",
  "domain": [["is_company", "=", false]],
  "fields": ["name", "email", "phone"],
  "limit": 10,
  "offset": 0
}

# Response
{
  "success": true,
  "result": [
    {
      "id": 123,
      "name": "Ahmed Al-Saudi",
      "email": "ahmed@example.com",
      "phone": "+966501234567"
    }
  ]
}
```

#### Update Record

```bash
POST /api/v1/systems/{system_id}/crud
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "action": "update",
  "model": "res.partner",
  "record_id": 123,
  "data": {
    "phone": "+966509876543"
  }
}

# Response
{
  "success": true,
  "result": {
    "id": 123,
    "phone": "+966509876543"
  }
}
```

#### Delete Record

```bash
POST /api/v1/systems/{system_id}/crud
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "action": "delete",
  "model": "res.partner",
  "record_id": 123
}

# Response
{
  "success": true,
  "message": "Record deleted successfully"
}
```

### Batch Operations

```bash
POST /api/v1/batch/execute
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "system_id": "odoo_main",
  "operations": [
    {
      "model": "res.partner",
      "action": "create",
      "data": {"name": "Customer 1", "email": "c1@example.com"}
    },
    {
      "model": "res.partner",
      "action": "create",
      "data": {"name": "Customer 2", "email": "c2@example.com"}
    }
  ],
  "stop_on_error": false
}

# Response
{
  "total": 2,
  "successful": 2,
  "failed": 0,
  "results": [...]
}
```

### Barcode Operations

```bash
GET /api/v1/barcode/lookup?barcode=6281000000123&system_id=odoo_main
Authorization: Bearer {access_token}

# Response
{
  "success": true,
  "product": {
    "id": 456,
    "name": "Product XYZ",
    "barcode": "6281000000123",
    "price": 99.99,
    "quantity": 150
  }
}
```

### File Operations

#### Upload File

```bash
POST /api/v1/files/upload
Authorization: Bearer {access_token}
Content-Type: multipart/form-data

file: [binary file data]
system_id: odoo_main
model: product.product
record_id: 456

# Response
{
  "success": true,
  "file_id": "abc123",
  "filename": "product-image.jpg",
  "size": 52341
}
```

#### Generate Report

```bash
POST /api/v1/files/export
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "system_id": "odoo_main",
  "model": "sale.order",
  "filters": [["state", "=", "sale"]],
  "format": "pdf"
}

# Response
{
  "success": true,
  "download_url": "/api/v1/files/download/report-abc123.pdf"
}
```

---

## Odoo Version Migration

### Overview

BridgeCore supports **automatic multi-hop migration** from Odoo 13.0 through 19.0. The system intelligently migrates data through intermediate versions.

### Supported Migration Paths

```
13.0 → 14.0 → 15.0 → 16.0 → 17.0 → 18.0 → 19.0
```

**Direct migrations** are also supported for consecutive versions:
- 13.0 → 14.0
- 14.0 → 15.0
- 15.0 → 16.0
- 16.0 → 17.0
- 17.0 → 18.0
- 18.0 → 19.0

**Multi-hop migrations** automatically traverse the path:
- 13.0 → 19.0 (goes through 14, 15, 16, 17, 18)
- 13.0 → 17.0 (goes through 14, 15, 16)
- 15.0 → 19.0 (goes through 16, 17, 18)

### Migration Rules

#### res.partner (Customers/Suppliers)

**13.0 → 14.0:**
- `customer` field removed → use `type = 'contact'`
- `supplier` field removed → use vendor management

**14.0 → 15.0:**
- `phone` → `phone_primary`
- `mobile` → `phone_secondary`

**15.0 → 16.0:**
- `user_id` → `sales_person_id`

**16.0 → 17.0:**
- Address format changes (street structure)

**17.0 → 18.0:**
- Payment terms restructured

**18.0 → 19.0:**
- Enhanced contact classification

#### product.product (Products)

**13.0 → 14.0:**
- `list_price` → `standard_price` field changes

**15.0 → 16.0:**
- `track_inventory` → `tracking` enum

**17.0 → 18.0:**
- New variant system

**18.0 → 19.0:**
- Enhanced attribute system

#### sale.order (Sales Orders)

**14.0 → 15.0:**
- Workflow state changes

**16.0 → 17.0:**
- Tax calculation method changes

**17.0 → 18.0:**
- Line-level discounts enhanced

### Usage Examples

#### Automatic Migration

```python
from app.services.version_handler_v2 import EnhancedVersionHandler

handler = EnhancedVersionHandler()

# Migrate partner data from Odoo 13 to 19
data = {
    "name": "Ahmed Al-Saudi",
    "customer": True,  # Removed in 14.0
    "phone": "+966501234567",  # Renamed in 15.0
    "user_id": 5  # Renamed in 16.0
}

migrated = await handler.migrate_data(
    data=data,
    system_type="odoo",
    from_version="13.0",
    to_version="19.0",
    model="res.partner",
    auto_multi_hop=True  # Automatically use multi-hop
)

# Result:
# {
#     "name": "Ahmed Al-Saudi",
#     "type": "contact",  # customer=True converted
#     "phone_primary": "+966501234567",  # phone renamed
#     "sales_person_id": 5  # user_id renamed
# }
```

#### Migration Plan (Dry Run)

```python
# Get migration plan without executing
plan = await handler.get_migration_plan(
    system_type="odoo",
    from_version="13.0",
    to_version="19.0",
    model="res.partner"
)

print(plan)
# {
#     "success": True,
#     "from_version": "13.0",
#     "to_version": "19.0",
#     "migration_path": ["13.0", "14.0", "15.0", "16.0", "17.0", "18.0", "19.0"],
#     "steps": [
#         {
#             "from": "13.0",
#             "to": "14.0",
#             "changes": {
#                 "removed_fields": ["customer", "supplier"],
#                 "renamed_fields": [],
#                 "warnings": ["customer field removed, use type field"]
#             }
#         },
#         ...
#     ],
#     "complexity": 6
# }
```

#### API Endpoint

```bash
POST /api/v1/systems/{system_id}/migrate
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "model": "res.partner",
  "from_version": "13.0",
  "to_version": "19.0",
  "record_ids": [123, 124, 125]
}

# Response
{
  "success": true,
  "migration_path": ["13.0", "14.0", "15.0", "16.0", "17.0", "18.0", "19.0"],
  "migrated": 3,
  "errors": []
}
```

### Best Practices

1. **Always test migrations on a copy** of your data first
2. **Review migration plan** before executing
3. **Backup your database** before major version jumps
4. **Monitor warnings** for manual interventions needed
5. **Use smaller batches** for large datasets

---

## Security

### JWT Authentication

```python
# Token structure
{
  "sub": "user123",  # User ID
  "exp": 1642243200,  # Expiration timestamp
  "type": "access"  # Token type
}
```

### Encryption

All sensitive data (connection configs, passwords) are encrypted using **Fernet** encryption:

```python
from app.core.encryption import encryption_service

# Encrypt connection config
encrypted = encryption_service.encrypt_config({
    "url": "https://odoo.example.com",
    "username": "admin",
    "password": "secret123"
})

# Decrypt when needed
config = encryption_service.decrypt_config(encrypted)
```

### Rate Limiting

Different limits for different operations:

- **Authentication**: 10 requests/minute
- **Read operations**: 100 requests/minute
- **Write operations**: 50 requests/minute
- **Delete operations**: 20 requests/minute
- **Batch operations**: 10 requests/minute
- **File operations**: 30 requests/minute
- **Reports**: 20 requests/minute

### CORS Configuration

```python
# Configure in .env
CORS_ORIGINS=["http://localhost:3000", "https://app.example.com"]
```

---

## Performance

### Redis Caching

```python
# Automatic caching for read operations
# TTL: 300 seconds (5 minutes) by default

# Cache keys format
"system:{system_id}:model:{model}:id:{record_id}"

# Cache invalidation on:
# - Create
# - Update
# - Delete
```

### Connection Pooling

```python
# Database connection pool
POOL_SIZE = 20
MAX_OVERFLOW = 10

# Redis connection pool
REDIS_MAX_CONNECTIONS = 50
```

### Circuit Breaker

```python
# Automatic failure protection
FAILURE_THRESHOLD = 5  # Open circuit after 5 failures
RECOVERY_TIMEOUT = 60  # Try recovery after 60 seconds

# States:
# - CLOSED: Normal operation
# - OPEN: Blocking calls (service down)
# - HALF_OPEN: Testing recovery
```

---

## Monitoring

### Prometheus Metrics

Access metrics at: `GET /metrics`

**Available Metrics:**

- `http_requests_total{method, endpoint, status}`
- `http_request_duration_seconds{method, endpoint}`
- `active_connections{system_type}`
- `cache_hits_total{operation}`
- `cache_misses_total{operation}`
- `db_query_duration_seconds{operation}`
- `api_operations_total{system_type, model, operation, status}`
- `circuit_breaker_state{system_id}`
- `version_migrations_total{system_type, from_version, to_version, status}`

### Sentry Error Tracking

```bash
# Configure in .env
SENTRY_DSN="https://your-key@sentry.io/project-id"

# Automatic error capture
# - All uncaught exceptions
# - Request context
# - User information
# - Stack traces
```

### Grafana Dashboard

Import dashboard template from `/grafana/dashboard.json`

**Panels:**
- Request rate
- Response time (p50, p95, p99)
- Error rate
- Cache hit ratio
- Active connections
- Circuit breaker states

---

## Task Queue

### Celery Workers

```bash
# Start Celery worker
celery -A app.tasks.celery_app worker --loglevel=info

# Start Celery beat (for periodic tasks)
celery -A app.tasks.celery_app beat --loglevel=info

# Monitor tasks with Flower
celery -A app.tasks.celery_app flower
# Access http://localhost:5555
```

### Available Tasks

#### Batch Operations

```python
from app.tasks.celery_app import process_batch_operation

# Queue batch operation
task = process_batch_operation.delay(
    user_id=123,
    system_id="odoo_main",
    operations=[...],
    stop_on_error=False
)

# Check status
result = task.get(timeout=300)
```

#### Report Generation

```python
from app.tasks.celery_app import generate_report

task = generate_report.delay(
    user_id=123,
    system_id="odoo_main",
    report_type="sales",
    model="sale.order",
    filters=[["state", "=", "sale"]],
    format="pdf"
)

result = task.get(timeout=600)
```

#### Data Synchronization

```python
from app.tasks.celery_app import sync_data

task = sync_data.delay(
    user_id=123,
    source_system_id="odoo_main",
    target_system_id="odoo_backup",
    model="res.partner",
    bidirectional=True
)
```

### Periodic Tasks

Configured in `celery_app.conf.beat_schedule`:

- **Cleanup old audit logs**: Daily at 2 AM
- **Refresh system connections**: Every 30 minutes
- **Update cache stats**: Every 5 minutes

---

## WebSocket

### Connection

```javascript
// JavaScript client example
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/123');

ws.onopen = () => {
  console.log('Connected');

  // Subscribe to channels
  ws.send(JSON.stringify({
    type: 'subscribe',
    channel: 'system_status'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);

  if (data.type === 'notification') {
    // Handle notification
    console.log('Channel:', data.channel);
    console.log('Data:', data.data);
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected');
};
```

### Available Channels

- **system_status**: System connection changes
- **operations**: Long-running operation progress
- **audit**: Audit log events
- **cache**: Cache invalidation events

### Notifications

```python
# Send notification from server
from app.api.routes.websocket import notify_operation_progress

await notify_operation_progress(
    user_id=123,
    operation_id="batch_123",
    progress=50,
    status="running",
    message="Processing record 500 of 1000"
)
```

---

## Deployment

### Production Checklist

- [ ] Set `DEBUG=false`
- [ ] Set `ENVIRONMENT=production`
- [ ] Use strong `SECRET_KEY` (32+ characters)
- [ ] Configure HTTPS/SSL
- [ ] Enable rate limiting
- [ ] Configure Sentry DSN
- [ ] Set up PostgreSQL backups
- [ ] Configure Redis persistence
- [ ] Set up Prometheus + Grafana
- [ ] Configure firewall rules
- [ ] Set up log rotation
- [ ] Configure Celery workers
- [ ] Enable database connection pooling
- [ ] Set up health check monitoring

### Docker Compose Production

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: bridgecore
      POSTGRES_USER: bridgecore
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    restart: always

  app:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://bridgecore:${DB_PASSWORD}@db:5432/bridgecore
      REDIS_URL: redis://redis:6379/0
      SENTRY_DSN: ${SENTRY_DSN}
    depends_on:
      - db
      - redis
    restart: always

  celery_worker:
    build: .
    command: celery -A app.tasks.celery_app worker --loglevel=info
    environment:
      DATABASE_URL: postgresql://bridgecore:${DB_PASSWORD}@db:5432/bridgecore
      REDIS_URL: redis://redis:6379/0
      CELERY_BROKER_URL: redis://redis:6379/1
    depends_on:
      - db
      - redis
    restart: always

  celery_beat:
    build: .
    command: celery -A app.tasks.celery_app beat --loglevel=info
    environment:
      CELERY_BROKER_URL: redis://redis:6379/1
    depends_on:
      - redis
    restart: always

  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    restart: always

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    restart: always

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
```

### Nginx Reverse Proxy

```nginx
upstream bridgecore {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name api.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.example.com;

    ssl_certificate /etc/letsencrypt/live/api.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;

    location / {
        proxy_pass http://bridgecore;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://bridgecore;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## Best Practices

### 1. Error Handling

```python
try:
    result = await service.create(...)
except ConnectionError:
    # System unavailable
    logger.error("System connection failed")
except ValidationError:
    # Invalid data
    logger.warning("Validation failed")
except Exception as e:
    # Unexpected error
    logger.exception("Unexpected error")
    # Automatically sent to Sentry
```

### 2. Field Mapping

```python
# Always use field mapping service
# Don't hardcode field names

# Good
mapped_data = field_mapping_service.map_to_system(
    universal_data, system_type, model
)

# Bad
data = {"name": universal_data["full_name"]}  # Hardcoded
```

### 3. Version Migration

```python
# Always check version before operations
if system.version != target_version:
    data = await version_handler.migrate_data(
        data, system_type, system.version, target_version, model
    )
```

### 4. Caching Strategy

```python
# Use cache for read-heavy operations
# Invalidate on writes

# Cached automatically
result = await service.read(...)

# Cache invalidated automatically
await service.update(...)
```

### 5. Audit Trail

```python
# All operations automatically logged
# Include context for debugging

await service.create(
    user_id=current_user.id,  # Always include user
    system_id=system_id,
    model=model,
    data=data
)
# Audit log created automatically
```

---

## Troubleshooting

### Connection Issues

**Problem**: Cannot connect to Odoo system

**Solutions**:
1. Check system is accessible: `curl https://odoo.example.com`
2. Verify credentials in system configuration
3. Check circuit breaker status: `GET /api/v1/systems/{system_id}/status`
4. Review audit logs for error details

### Performance Issues

**Problem**: Slow API responses

**Solutions**:
1. Check Redis is running: `redis-cli ping`
2. Review cache hit ratio in metrics
3. Check database query performance
4. Monitor circuit breaker states
5. Review Prometheus metrics for bottlenecks

### Migration Issues

**Problem**: Version migration fails

**Solutions**:
1. Get migration plan first: `await handler.get_migration_plan(...)`
2. Review warnings in plan
3. Check if all required fields are present
4. Test with single record first
5. Review migration logs

### Task Queue Issues

**Problem**: Celery tasks not processing

**Solutions**:
1. Check Celery worker is running: `celery -A app.tasks.celery_app inspect active`
2. Check Redis broker connection
3. Review Celery logs
4. Check task queue: `celery -A app.tasks.celery_app inspect reserved`

### WebSocket Issues

**Problem**: WebSocket disconnects frequently

**Solutions**:
1. Implement ping/pong heartbeat
2. Check network stability
3. Review proxy configuration (Nginx)
4. Increase timeout settings

---

## Support

For issues and questions:
- **GitHub Issues**: https://github.com/yourusername/BridgeCore/issues
- **Email**: support@example.com
- **Documentation**: https://docs.example.com

---

## License

MIT License - See LICENSE file for details

---

## Changelog

### Version 1.0.0 (2024-01-15)

**Phase 1: Core Infrastructure**
- ✅ Odoo adapter with smart fallback
- ✅ Field mapping service
- ✅ Version handler (Odoo 13.0 → 19.0)
- ✅ Redis caching
- ✅ JWT authentication
- ✅ Rate limiting
- ✅ Encryption
- ✅ Alembic migrations

**Phase 2: Reliability & Monitoring**
- ✅ Circuit Breaker pattern
- ✅ Sentry integration
- ✅ Prometheus metrics
- ✅ Health checks

**Phase 3: Advanced Features**
- ✅ WebSocket support
- ✅ Celery task queue
- ✅ Batch operations
- ✅ Report generation
- ✅ Multi-language support (EN, AR, FR)
- ✅ Barcode integration

---

**End of Documentation**
