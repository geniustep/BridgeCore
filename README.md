# 🚀 BridgeCore - Enterprise Middleware API

<div align="center">

**A powerful, production-ready middleware API built with FastAPI to bridge Flutter applications with external ERP/CRM systems**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Webhook System](#webhook-system)
- [Configuration](#configuration)
- [Development](#development)
- [Deployment](#deployment)
- [Contributing](#contributing)

---

## 🎯 Overview

BridgeCore is an enterprise-grade middleware API that serves as a unified interface between Flutter mobile applications and external ERP/CRM systems (Odoo, SAP, Salesforce). It provides real-time change tracking, smart synchronization, and comprehensive data management capabilities.

### What BridgeCore Does

- **🔗 Connects** Flutter apps to Odoo ERP systems seamlessly
- **📊 Tracks** all changes in real-time via webhook system
- **🔄 Syncs** data efficiently with smart incremental sync
- **🛡️ Secures** all operations with JWT authentication
- **⚡ Optimizes** performance with Redis caching and connection pooling
- **📝 Audits** every operation for compliance and debugging

---

## ✨ Key Features

### 🔐 Authentication & Security
- JWT-based authentication with refresh tokens
- Password hashing with bcrypt
- SQL injection prevention
- CORS configuration
- Rate limiting
- Secure headers

### 🔄 Webhook System (NEW)
- **Real-time Change Detection**: Track all changes in Odoo instantly
- **Smart Multi-User Sync**: Efficient synchronization for multiple devices/users
- **Universal Model Discovery**: Automatically discover and monitor all Odoo models
- **ORM-based Detection**: Odoo-native change tracking
- **Retry Mechanism**: Automatic retry with exponential backoff
- **Dead Letter Queue**: Handle failed events gracefully
- **Priority System**: Classify events by importance (high/medium/low)

### 🎯 Multi-System Support
- **Odoo** (13/16/18+): Full CRUD operations
- **SAP**: Ready for integration
- **Salesforce**: Ready for integration
- **Adapter Pattern**: Easy integration with new systems

### ⚡ Performance
- **Redis Caching**: Fast data retrieval
- **Connection Pooling**: Optimized database connections
- **Async/Await**: Non-blocking I/O operations
- **Query Optimization**: Eager loading, bulk operations
- **Background Tasks**: Non-blocking operation execution

### 📊 Advanced Features
- **Batch Operations**: Execute multiple CRUD operations in one request
- **File Management**: Upload/download files with attachment support
- **Barcode Integration**: Product lookup and inventory management
- **Report Generation**: PDF, Excel, and CSV reports
- **Multi-Language Support**: English, Arabic, French
- **Version Migration**: Automatic data transformation between system versions

### 📝 Monitoring & Observability
- **Prometheus Metrics**: Real-time performance monitoring
- **Grafana Dashboards**: Visual analytics
- **Structured Logging**: JSON logging with Loguru
- **Audit Trail**: Complete operation logging
- **Health Checks**: Database, Redis, and API health monitoring

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Flutter Applications                      │
│         (gmobile, delivery_app, sales_app, etc.)           │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
               │ REST/GraphQL/WebSocket       │
               ▼                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      BridgeCore API                          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   REST API   │  │   GraphQL    │  │  WebSocket   │     │
│  │   (v1, v2)   │  │   API        │  │  Real-time   │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │              │
│  ┌──────┴──────────────────┴──────────────────┴───────┐    │
│  │           Webhook Module (NEW)                      │    │
│  │  - Event Handling     - Smart Sync                  │    │
│  │  - Update Tracking    - Multi-User State            │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │     Universal Audit/Detection Module (NEW)          │    │
│  │  - Auto-discovery   - Model Classification          │    │
│  │  - ORM Interception - Change Streaming             │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Caching    │  │    Queue     │  │  Monitoring  │     │
│  │   (Redis)    │  │   (Celery)   │  │ (Prometheus) │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────┬───────────────────────────────────────────────┘
              │
              │ Odoo API / PostgreSQL
              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Odoo ERP System                         │
│  - Enhanced Webhook Module (ORM-based detection)            │
│  - update.webhook model (stores all change events)         │
│  - user.sync.state (tracks sync state per user/device)      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

### Installation

#### Option 1: Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/geniustep/BridgeCore.git
cd BridgeCore

# Setup environment
cp env.example .env
# Edit .env with your configuration

# Start all services
cd docker
docker-compose up -d

# View logs
docker-compose logs -f api
```

The API will be available at:
- **API**: `https://bridgecore.geniura.com` (or your configured domain)
- **Docs**: `https://bridgecore.geniura.com/docs`
- **ReDoc**: `https://bridgecore.geniura.com/redoc`

#### Option 2: Local Development

```bash
# Clone repository
git clone https://github.com/yourusername/BridgeCore.git
cd BridgeCore

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📚 API Documentation

### Authentication

All API endpoints (except `/health` and `/docs`) require JWT authentication.

#### 1. Login

```bash
curl -X POST 'https://bridgecore.geniura.com/api/v1/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "your_username",
    "password": "your_password",
    "database": "your_database"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "system_id": "odoo-your_username",
  "user": {
    "id": 1,
    "username": "your_username",
    "name": "Your Name"
  }
}
```

#### 2. Use Token

```bash
curl -X GET 'https://bridgecore.geniura.com/api/v1/auth/me' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

### Core Endpoints

#### Connect to Odoo System

```bash
curl -X POST 'https://bridgecore.geniura.com/systems/odoo-prod/connect' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "url": "https://app.propanel.ma",
    "database": "your_database",
    "username": "your_username",
    "password": "your_password",
    "system_type": "odoo"
  }'
```

#### CRUD Operations

**Create:**
```bash
curl -X POST 'https://bridgecore.geniura.com/systems/odoo-prod/create?model=res.partner' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Ahmed Ali",
    "email": "ahmed@example.com",
    "phone": "+966501234567"
  }'
```

**Read:**
```bash
curl -X GET 'https://bridgecore.geniura.com/systems/odoo-prod/read?model=res.partner&limit=10' \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

**Update:**
```bash
curl -X PUT 'https://bridgecore.geniura.com/systems/odoo-prod/update/42?model=res.partner' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{"phone": "+966502222222"}'
```

**Delete:**
```bash
curl -X DELETE 'https://bridgecore.geniura.com/systems/odoo-prod/delete/42?model=res.partner' \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

---

## 🔔 Webhook System

BridgeCore includes a comprehensive webhook system for real-time change tracking from Odoo.

### v1 API - Webhook Operations

#### Check for Updates

```bash
curl -X GET 'https://bridgecore.geniura.com/api/v1/webhooks/check-updates?limit=50' \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

**Response:**
```json
{
  "has_update": true,
  "last_update_at": "2025-11-16 12:30:00",
  "summary": [
    {"model": "sale.order", "count": 15},
    {"model": "res.partner", "count": 8}
  ]
}
```

#### List Events

```bash
curl -X GET 'https://bridgecore.geniura.com/api/v1/webhooks/events?model=sale.order&limit=100' \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

**Response:**
```json
{
  "status": "success",
  "count": 10,
  "data": [
    {
      "id": 123,
      "model": "sale.order",
      "record_id": 456,
      "event": "create",
      "occurred_at": "2025-11-16T10:30:00Z"
    }
  ]
}
```

#### Enhanced Events (with Priority/Category)

```bash
curl -X GET 'https://bridgecore.geniura.com/api/v1/webhooks/events/enhanced?priority=high&limit=50' \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

### v2 API - Smart Sync

#### Smart Sync Pull (Recommended for Apps)

```bash
curl -X POST 'https://bridgecore.geniura.com/api/v2/sync/pull' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": 1,
    "device_id": "device_123",
    "app_type": "sales_app",
    "limit": 100
  }'
```

**Response:**
```json
{
  "has_updates": true,
  "new_events_count": 25,
  "events": [
    {
      "id": 123,
      "model": "sale.order",
      "record_id": 456,
      "event": "write",
      "timestamp": "2025-11-16T10:30:00Z"
    }
  ],
  "next_sync_token": "1234",
  "last_sync_time": "2025-11-16T10:30:00Z"
}
```

**Features:**
- ✅ Returns only NEW events since last sync
- ✅ Filters by app type (sales_app, delivery_app, etc.)
- ✅ Tracks sync state per user/device
- ✅ Automatic state management

#### Get Sync State

```bash
curl -X GET 'https://bridgecore.geniura.com/api/v2/sync/state?user_id=1&device_id=device_123' \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

#### Reset Sync State

```bash
curl -X POST 'https://bridgecore.geniura.com/api/v2/sync/reset?user_id=1&device_id=device_123' \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

### App Type Models

The system automatically filters events based on app type:

- **sales_app**: `sale.order`, `sale.order.line`, `res.partner`, `product.*`
- **delivery_app**: `stock.picking`, `stock.move`, `stock.move.line`, `res.partner`
- **warehouse_app**: `stock.*`, `product.product`, `stock.location`
- **manager_app**: `sale.order`, `purchase.order`, `account.move`, `hr.expense`
- **mobile_app**: `sale.order`, `res.partner`, `product.*`

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file from `env.example`:

```env
# Application
APP_NAME=FastAPI Middleware
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=your-secret-key-here-change-in-production
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/middleware_db
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://redis:6379/0
CACHE_TTL=300

# JWT
JWT_SECRET_KEY=your-jwt-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=https://bridgecore.geniura.com,http://bridgecore.geniura.com

# Rate Limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_PER_MINUTE=60

# Odoo
ODOO_URL=https://app.propanel.ma

# Monitoring (Optional)
SENTRY_DSN=
```

### Odoo Webhook Module Setup

BridgeCore requires the `update.webhook` model in Odoo. This can be provided by:

1. **Odoo Module** (Recommended): Install `custom-model-webhook` module in Odoo
2. **PostgreSQL Triggers** (Alternative): Use `scripts/setup_triggers.sql` for database-level tracking

See `WEBHOOK_INTEGRATION_README.md` for detailed setup instructions.

---

## 🛠️ Development

### Project Structure

```
BridgeCore/
├── app/
│   ├── api/
│   │   └── routes/          # API endpoints
│   │       ├── auth.py      # Authentication
│   │       ├── systems.py   # System management
│   │       ├── odoo.py      # Odoo operations
│   │       ├── batch.py     # Batch operations
│   │       ├── barcode.py   # Barcode operations
│   │       ├── files.py     # File management
│   │       └── websocket.py # WebSocket support
│   ├── modules/
│   │   ├── webhook/         # Webhook system (NEW)
│   │   │   ├── router.py    # v1 REST API
│   │   │   ├── router_v2.py # v2 Smart Sync API
│   │   │   ├── service.py   # Business logic
│   │   │   └── schemas.py   # Pydantic schemas
│   │   └── universal_audit/ # Universal detection (NEW)
│   ├── core/                # Core configuration
│   ├── db/                  # Database setup
│   ├── models/              # SQLAlchemy models
│   ├── services/            # Business logic
│   ├── utils/               # Utilities
│   │   └── odoo_client.py    # Odoo client (NEW)
│   └── main.py              # Application entry point
├── docker/                  # Docker configuration
├── scripts/                 # Utility scripts
├── monitoring/              # Prometheus & Grafana
├── tests/                   # Test suite
├── alembic/                 # Database migrations
└── requirements.txt         # Dependencies
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py
```

### Code Quality

```bash
# Lint code
ruff check app/

# Format code
ruff format app/

# Type checking
mypy app/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

---

## 🚢 Deployment

### Docker Deployment

```bash
# Build and start
cd docker
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

### Production Checklist

- [ ] Update `SECRET_KEY` and `JWT_SECRET_KEY` in `.env`
- [ ] Set `ENVIRONMENT=production` and `DEBUG=False`
- [ ] Configure proper `CORS_ORIGINS`
- [ ] Set up SSL/TLS certificates
- [ ] Configure database backups
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure log rotation
- [ ] Set up rate limiting
- [ ] Enable Sentry for error tracking (optional)

---

## 📊 Monitoring

### Health Checks

```bash
# API health
curl https://bridgecore.geniura.com/health

# Database health
curl https://bridgecore.geniura.com/health/db

# Redis health
curl https://bridgecore.geniura.com/health/redis
```

### Prometheus Metrics

```bash
curl https://bridgecore.geniura.com/metrics
```

### Grafana Dashboards

Grafana dashboards are available in `monitoring/grafana/dashboards/`:
- Webhook Dashboard
- API Performance Dashboard
- System Health Dashboard

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Write tests for new features
- Update documentation
- Add type hints
- Write clear commit messages

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🆘 Support

- **Documentation**: See `WEBHOOK_INTEGRATION_README.md` for webhook system details
- **Issues**: [GitHub Issues](https://github.com/geniustep/BridgeCore/issues)
- **Email**: support@geniura.com

---

## 🗺️ Roadmap

- [x] Webhook system with real-time change tracking
- [x] Smart sync for multi-user/multi-device scenarios
- [x] Universal audit system with auto-discovery
- [x] GraphQL API support
- [x] WebSocket support for real-time updates
- [x] Prometheus metrics and Grafana dashboards
- [ ] SAP integration
- [ ] Salesforce integration
- [ ] Advanced field mapping UI
- [ ] Multi-tenancy support
- [ ] Kubernetes deployment configs

---

## 🙏 Acknowledgments

- FastAPI framework
- SQLAlchemy team
- Python community
- Odoo community

---

<div align="center">

**Made with ❤️ by the BridgeCore Team**

[⭐ Star us on GitHub](https://github.com/geniustep/BridgeCore) | [📖 Documentation](./WEBHOOK_INTEGRATION_README.md) | [🐛 Report Bug](https://github.com/geniustep/BridgeCore/issues)

</div>
