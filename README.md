# BridgeCore - Enterprise Multi-Tenant Middleware Platform

<div align="center">

**A powerful, production-ready middleware platform with multi-tenant management, built with FastAPI to bridge Flutter applications with Odoo ERP/CRM systems**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org)
[![React](https://img.shields.io/badge/React-18.2+-61DAFB.svg)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.2+-3178C6.svg)](https://www.typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7+-red.svg)](https://redis.io)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[Features](#-key-features) | [Quick Start](#-quick-start) | [Admin Panel](#-admin-panel) | [API Reference](#-api-reference) | [Documentation](#-documentation)

</div>

---

## Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Admin Panel](#-admin-panel)
- [Multi-Tenancy](#-multi-tenancy)
- [API Reference](#-api-reference)
- [Webhook System](#-webhook-system)
- [Smart Sync](#-smart-sync)
- [Configuration](#-configuration)
- [Deployment](#-deployment)
- [Monitoring](#-monitoring)
- [Contributing](#-contributing)

---

## Overview

BridgeCore is an enterprise-grade multi-tenant middleware platform that serves as a unified interface between Flutter mobile applications and Odoo ERP/CRM systems. It provides comprehensive tenant management, real-time change tracking, smart synchronization, and a full-featured admin dashboard.

### What BridgeCore Does

- **Multi-Tenant Management**: Manage multiple companies/clients from a single platform
- **Real-time Sync**: Track all Odoo changes via webhook system
- **Smart Synchronization**: Efficient incremental sync per user/device
- **Admin Dashboard**: Full React-based admin panel for management
- **Rate Limiting**: Per-tenant rate limits with Redis
- **Analytics**: Comprehensive usage tracking and reporting
- **Secure**: JWT authentication with role-based access control

### Use Cases

- **SaaS Platform**: Offer Odoo integration as a service to multiple clients
- **Mobile Apps**: Connect Flutter apps to Odoo ERP for multiple tenants
- **Enterprise Solutions**: Centralized middleware for large-scale deployments
- **Multi-Company Setup**: Single platform managing multiple Odoo instances

---

## Key Features

### Multi-Tenant Architecture
- **Tenant Isolation**: Complete data isolation between tenants
- **Per-Tenant Rate Limits**: Configurable API limits per tenant
- **Subscription Plans**: Multiple plans (Free, Starter, Professional, Enterprise)
- **Usage Tracking**: Automatic logging of all API requests per tenant
- **Tenant Lifecycle**: Active, Trial, Suspended, Deleted states

### Admin Panel (React Dashboard)
- **Dashboard Overview**: System statistics and health metrics
- **Tenant Management**: Create, edit, suspend, activate tenants
- **Analytics Dashboard**: Charts and graphs for usage patterns
- **Usage Logs**: View and filter API request logs
- **Error Logs**: Track and resolve application errors
- **Connection Testing**: Test Odoo connections per tenant

### Authentication & Security
- **Dual JWT System**: Separate tokens for admins and tenant users
- **Role-Based Access**: Super Admin, Admin, Support roles
- **Password Hashing**: bcrypt for secure password storage
- **Rate Limiting**: Redis-based per-tenant rate limiting
- **Audit Logging**: Complete audit trail for admin actions

### Webhook System
- **Real-time Change Detection**: Track all Odoo changes instantly
- **Smart Multi-User Sync**: Efficient sync for multiple devices/users
- **Universal Model Discovery**: Auto-discover and monitor Odoo models
- **Retry Mechanism**: Automatic retry with exponential backoff
- **Dead Letter Queue**: Handle failed events gracefully

### Performance
- **Redis Caching**: Fast data retrieval with configurable TTL
- **Connection Pooling**: Optimized database connections
- **Async/Await**: Non-blocking I/O operations
- **Background Tasks**: Celery for stats aggregation and cleanup
- **Gzip Compression**: Automatic response compression

### Monitoring & Analytics
- **Prometheus Metrics**: Real-time performance monitoring
- **Usage Statistics**: Per-tenant API usage tracking
- **Error Tracking**: Severity-based error classification
- **Response Time Tracking**: Performance analytics per endpoint
- **Grafana Dashboards**: Visual analytics and dashboards

---

## Architecture

```
                          BridgeCore Platform
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Admin Dashboard (React)                   │   │
│  │  - Dashboard Overview    - Tenant Management                │   │
│  │  - Analytics & Charts    - Usage/Error Logs                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                   Admin API (FastAPI)                        │   │
│  │  /admin/auth/*     /admin/tenants/*    /admin/analytics/*   │   │
│  │  /admin/plans/*    /admin/logs/*                            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│  ┌───────────────────────────┼───────────────────────────────────┐ │
│  │                    Middleware Layer                           │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │ │
│  │  │   Usage     │ │   Tenant    │ │      Rate Limit         │ │ │
│  │  │  Tracking   │ │   Context   │ │   (Per-Tenant/Redis)    │ │ │
│  │  └─────────────┘ └─────────────┘ └─────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                              │                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Tenant API (FastAPI)                      │   │
│  │  /api/v1/auth/*    /api/v1/odoo/*    /api/v1/webhooks/*     │   │
│  │  /api/v2/sync/*    /batch/*          /files/*               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Background Tasks (Celery)                 │   │
│  │  - Hourly Stats Aggregation   - Daily Stats Aggregation     │   │
│  │  - Old Logs Cleanup           - Scheduled Reports           │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────────┐   │
│  │ PostgreSQL  │ │    Redis    │ │         Prometheus          │   │
│  │ (Database)  │ │   (Cache)   │ │        (Monitoring)         │   │
│  └─────────────┘ └─────────────┘ └─────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Tenant Odoo Instances                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
│  │  Tenant A   │ │  Tenant B   │ │  Tenant C   │ │  Tenant N   │   │
│  │   Odoo 17   │ │   Odoo 16   │ │   Odoo 15   │ │   Odoo 18   │   │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology |
|-----------|------------|
| **Backend API** | FastAPI (Python 3.11+) |
| **Admin Dashboard** | React 18, TypeScript, Vite |
| **UI Components** | Ant Design 5.12 |
| **State Management** | Zustand 4.4 |
| **Charts** | Recharts 2.10 |
| **Database** | PostgreSQL 15+ (async with asyncpg) |
| **Cache** | Redis 7+ |
| **ORM** | SQLAlchemy 2.0 (async) |
| **Migrations** | Alembic |
| **Background Tasks** | Celery with Redis |
| **Authentication** | JWT (python-jose) + bcrypt |
| **Monitoring** | Prometheus + Grafana |
| **Containerization** | Docker & Docker Compose |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (for Admin Dashboard)
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (recommended)

### Option 1: Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/geniustep/BridgeCore.git
cd BridgeCore

# Setup environment
cp env.example .env
# Edit .env with your configuration

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

Services will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Admin Dashboard**: http://localhost:3000
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001

### Option 2: Local Development

```bash
# Clone repository
git clone https://github.com/geniustep/BridgeCore.git
cd BridgeCore

# Setup Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Setup environment
cp env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Seed initial data (admin user & plans)
python scripts/seed_admin.py

# Start API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start Admin Dashboard
cd admin
npm install
npm run dev
```

### Default Admin Credentials

After running the seed script:
- **Email**: admin@bridgecore.local
- **Password**: admin123

**Important**: Change these credentials immediately in production!

---

## Admin Panel

The BridgeCore Admin Panel is a comprehensive React-based dashboard for managing the platform.

### Dashboard
- System overview with key statistics
- Active tenants count
- API requests (24h)
- Error rate metrics
- Quick actions

### Tenant Management
- **List View**: View all tenants with status indicators
- **Create Tenant**: Add new tenants with Odoo connection details
- **Edit Tenant**: Modify tenant settings and credentials
- **Suspend/Activate**: Control tenant access
- **Connection Test**: Verify Odoo connectivity

### Analytics
- **Requests Over Time**: Line chart showing API usage trends
- **Status Distribution**: Pie chart of response codes
- **Response Times**: Bar chart of performance by hour
- **Top Tenants**: Most active tenants table
- **Top Endpoints**: Most used API endpoints

### Logs
- **Usage Logs**: Filter by tenant, method, status, date range
- **Error Logs**: View errors with severity levels
- **Error Resolution**: Mark errors as resolved with notes
- **Export**: Download logs as CSV

### Admin Dashboard Screenshots

| Feature | Description |
|---------|-------------|
| Dashboard | System overview with statistics cards |
| Tenants | CRUD operations with status management |
| Analytics | Charts and graphs using Recharts |
| Usage Logs | Filterable API request logs |
| Error Logs | Error tracking with resolution workflow |

---

## Multi-Tenancy

### Tenant Model

Each tenant represents a company/client using the BridgeCore platform:

```python
{
    "id": "uuid",
    "name": "Company Name",
    "slug": "company-name",
    "status": "active",  # active, trial, suspended, deleted
    "odoo_url": "https://company.odoo.com",
    "odoo_database": "company_db",
    "odoo_username": "api_user",
    "plan_id": "uuid",  # Subscription plan
    "max_requests_per_day": 10000,
    "max_requests_per_hour": 1000,
    "allowed_models": ["res.partner", "sale.order"],
    "allowed_features": ["sync", "webhooks"]
}
```

### Subscription Plans

| Plan | Daily Requests | Hourly Requests | Users | Storage |
|------|----------------|-----------------|-------|---------|
| Free | 1,000 | 100 | 5 | 1 GB |
| Starter | 10,000 | 1,000 | 25 | 10 GB |
| Professional | 100,000 | 10,000 | 100 | 100 GB |
| Enterprise | Unlimited | Unlimited | Unlimited | Unlimited |

### Rate Limiting

Rate limits are enforced per-tenant using Redis:

```python
# Middleware checks limits before processing requests
hourly_key = f"rate_limit:tenant:{tenant_id}:hour:{current_hour}"
daily_key = f"rate_limit:tenant:{tenant_id}:day:{current_day}"

# Returns 429 Too Many Requests if limit exceeded
```

---

## API Reference

### Admin API Endpoints

#### Authentication
```bash
# Admin Login
POST /admin/auth/login
{
    "email": "admin@bridgecore.local",
    "password": "admin123"
}

# Get Current Admin
GET /admin/auth/me
Authorization: Bearer {admin_token}

# Logout
POST /admin/auth/logout
Authorization: Bearer {admin_token}
```

#### Tenant Management
```bash
# List Tenants
GET /admin/tenants?status=active&skip=0&limit=100

# Create Tenant
POST /admin/tenants
{
    "name": "New Company",
    "slug": "new-company",
    "contact_email": "contact@newcompany.com",
    "odoo_url": "https://newcompany.odoo.com",
    "odoo_database": "newcompany_db",
    "odoo_username": "api_user",
    "odoo_password": "secure_password",
    "plan_id": "uuid"
}

# Get Tenant
GET /admin/tenants/{tenant_id}

# Update Tenant
PUT /admin/tenants/{tenant_id}
{
    "name": "Updated Company Name",
    "max_requests_per_day": 20000
}

# Suspend Tenant
POST /admin/tenants/{tenant_id}/suspend

# Activate Tenant
POST /admin/tenants/{tenant_id}/activate

# Delete Tenant
DELETE /admin/tenants/{tenant_id}

# Test Connection
POST /admin/tenants/{tenant_id}/test-connection
```

#### Analytics
```bash
# System Overview
GET /admin/analytics/overview

# Top Tenants
GET /admin/analytics/top-tenants?limit=10&days=7

# Tenant Analytics
GET /admin/analytics/tenants/{tenant_id}?days=30

# Daily Statistics
GET /admin/analytics/tenants/{tenant_id}/daily?days=30
```

#### Logs
```bash
# Usage Logs
GET /admin/logs/usage?tenant_id={id}&method=POST&limit=100

# Usage Summary
GET /admin/logs/usage/summary?tenant_id={id}&days=7

# Error Logs
GET /admin/logs/errors?severity=high&unresolved_only=true

# Error Summary
GET /admin/logs/errors/summary?tenant_id={id}&days=7

# Resolve Error
POST /admin/logs/errors/{error_id}/resolve
{
    "resolution_notes": "Fixed by updating configuration"
}
```

### Tenant API Endpoints

#### Authentication
```bash
# Login
POST /api/v1/auth/login
{
    "username": "user@company.com",
    "password": "password",
    "database": "company_db"
}

# Response
{
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "user": {
        "id": 1,
        "username": "user@company.com",
        "name": "User Name"
    }
}
```

#### Odoo Operations
```bash
# Search & Read
POST /api/v1/odoo/search_read
{
    "model": "res.partner",
    "domain": [["customer_rank", ">", 0]],
    "fields": ["id", "name", "email"],
    "limit": 100
}

# Create
POST /api/v1/odoo/create
{
    "model": "res.partner",
    "values": {
        "name": "New Customer",
        "email": "customer@example.com"
    }
}

# Update
POST /api/v1/odoo/write
{
    "model": "res.partner",
    "ids": [1, 2, 3],
    "values": {
        "phone": "+1234567890"
    }
}

# Delete
POST /api/v1/odoo/unlink
{
    "model": "res.partner",
    "ids": [1, 2, 3]
}
```

---

## Webhook System

BridgeCore includes a comprehensive webhook system for real-time change tracking from Odoo.

### v1 API - Webhook Operations

```bash
# Check for Updates
GET /api/v1/webhooks/check-updates?limit=50

# List Events
GET /api/v1/webhooks/events?model=sale.order&limit=100

# Push Endpoint (Odoo calls this)
POST /api/v1/webhooks/push
{
    "model": "sale.order",
    "event": "write",
    "record_id": 123,
    "timestamp": "2025-11-21T10:30:00Z"
}
```

### v2 API - Smart Sync

```bash
# Smart Sync Pull
POST /api/v2/sync/pull
{
    "user_id": 1,
    "device_id": "device_123",
    "app_type": "sales_app",
    "limit": 100
}

# Response
{
    "has_updates": true,
    "new_events_count": 25,
    "events": [...],
    "next_sync_token": "1234",
    "last_sync_time": "2025-11-21T10:30:00Z"
}

# Get Sync State
GET /api/v2/sync/state?user_id=1&device_id=device_123

# Reset Sync State
POST /api/v2/sync/reset?user_id=1&device_id=device_123
```

---

## Configuration

### Environment Variables

```env
# Application
APP_NAME=BridgeCore
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=your-secret-key-change-in-production
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/bridgecore_db
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://redis:6379/0
CACHE_TTL=300

# JWT - Tenant Authentication
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# JWT - Admin Authentication
ADMIN_SECRET_KEY=your-admin-secret-key-change-in-production
ADMIN_TOKEN_EXPIRE_HOURS=24

# CORS
CORS_ORIGINS=http://localhost:3000,https://admin.bridgecore.com

# Rate Limiting
RATE_LIMIT_ENABLED=True
DEFAULT_RATE_LIMIT_PER_HOUR=1000
DEFAULT_RATE_LIMIT_PER_DAY=10000

# Celery
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# Monitoring (Optional)
SENTRY_DSN=
PROMETHEUS_ENABLED=True
```

---

## Deployment

### Docker Compose (Production)

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/bridgecore
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  admin-dashboard:
    build: ./admin
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - api

  celery-worker:
    build: .
    command: celery -A app.celery_app worker --loglevel=info
    depends_on:
      - db
      - redis

  celery-beat:
    build: .
    command: celery -A app.celery_app beat --loglevel=info
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=bridgecore
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Production Checklist

- [ ] Change `SECRET_KEY`, `JWT_SECRET_KEY`, and `ADMIN_SECRET_KEY`
- [ ] Set `ENVIRONMENT=production` and `DEBUG=False`
- [ ] Configure proper `CORS_ORIGINS`
- [ ] Set up SSL/TLS certificates
- [ ] Configure database backups
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure log rotation
- [ ] Enable rate limiting
- [ ] Change default admin credentials
- [ ] Set up Sentry for error tracking

---

## Monitoring

### Health Checks

```bash
# API Health
GET /health

# Database Health
GET /health/db

# Redis Health
GET /health/redis
```

### Prometheus Metrics

```bash
GET /metrics
```

Available metrics:
- `bridgecore_requests_total`: Total API requests
- `bridgecore_request_duration_seconds`: Request duration histogram
- `bridgecore_active_tenants`: Number of active tenants
- `bridgecore_errors_total`: Total errors by type

### Background Tasks (Celery)

| Task | Schedule | Description |
|------|----------|-------------|
| `aggregate_hourly_stats` | Every hour at :05 | Aggregate usage logs to hourly stats |
| `aggregate_daily_stats` | Daily at 00:30 | Aggregate hourly stats to daily |
| `cleanup_old_logs` | Daily at 02:00 | Delete logs older than 90 days |

---

## Project Structure

```
BridgeCore/
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── admin/              # Admin API routes
│   │       │   ├── auth.py         # Admin authentication
│   │       │   ├── tenants.py      # Tenant management
│   │       │   ├── analytics.py    # Analytics endpoints
│   │       │   └── logs.py         # Logs endpoints
│   │       ├── auth.py             # Tenant authentication
│   │       ├── odoo.py             # Odoo operations
│   │       └── webhooks.py         # Webhook endpoints
│   ├── middleware/
│   │   ├── usage_tracking.py       # Request logging
│   │   ├── tenant_context.py       # Tenant validation
│   │   └── tenant_rate_limit.py    # Rate limiting
│   ├── models/                     # SQLAlchemy models
│   │   ├── admin.py                # Admin user model
│   │   ├── tenant.py               # Tenant model
│   │   ├── plan.py                 # Subscription plans
│   │   ├── usage_log.py            # Usage logs
│   │   └── error_log.py            # Error logs
│   ├── repositories/               # Data access layer
│   ├── services/                   # Business logic
│   │   ├── admin_service.py        # Admin operations
│   │   ├── tenant_service.py       # Tenant operations
│   │   ├── analytics_service.py    # Analytics
│   │   └── logging_service.py      # Log management
│   ├── tasks/                      # Celery tasks
│   │   └── stats_aggregation.py    # Background jobs
│   ├── core/                       # Core configuration
│   │   ├── config.py               # Settings
│   │   └── security.py             # JWT & passwords
│   ├── celery_app.py               # Celery configuration
│   └── main.py                     # Application entry
├── admin/                          # React Admin Dashboard
│   ├── src/
│   │   ├── components/             # React components
│   │   │   └── Layout/             # Layout components
│   │   ├── pages/                  # Page components
│   │   │   ├── Auth/               # Login page
│   │   │   ├── Dashboard/          # Dashboard page
│   │   │   ├── Tenants/            # Tenant pages
│   │   │   ├── Analytics/          # Analytics page
│   │   │   └── Logs/               # Logs pages
│   │   ├── services/               # API services
│   │   ├── store/                  # Zustand stores
│   │   ├── types/                  # TypeScript types
│   │   └── config/                 # Configuration
│   ├── package.json
│   └── Dockerfile
├── alembic/                        # Database migrations
├── docker/                         # Docker configuration
├── scripts/                        # Utility scripts
│   └── seed_admin.py               # Initial data seed
├── monitoring/                     # Prometheus & Grafana
├── tests/                          # Test suite
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Use TypeScript for React components
- Write tests for new features
- Update documentation
- Add type hints

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Roadmap

- [x] Multi-tenant architecture
- [x] Admin panel with React dashboard
- [x] Per-tenant rate limiting
- [x] Usage tracking and analytics
- [x] Error logging with resolution workflow
- [x] Background tasks with Celery
- [x] Webhook system for real-time sync
- [x] Smart sync for mobile apps
- [ ] SAP integration
- [ ] Salesforce integration
- [ ] Kubernetes deployment configs
- [ ] Advanced reporting and exports
- [ ] Multi-language admin panel

---

<div align="center">

**Made with care by the BridgeCore Team**

[Star on GitHub](https://github.com/geniustep/BridgeCore) | [Documentation](./docs/) | [Report Bug](https://github.com/geniustep/BridgeCore/issues)

</div>
