# BridgeCore - Enterprise Multi-System Middleware Platform

<div align="center">

**A powerful, production-ready multi-system middleware platform built with FastAPI to bridge Flutter applications with multiple external systems (Odoo ERP, Moodle LMS, SAP, Salesforce, and more)**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org)
[![React](https://img.shields.io/badge/React-18.2+-61DAFB.svg)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.2+-3178C6.svg)](https://www.typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7+-red.svg)](https://redis.io)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[Features](#-key-features) | [Quick Start](#-quick-start) | [Documentation](#-documentation) | [API Reference](#-api-reference) | [Examples](#-usage-examples)

</div>

---

## 📚 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Admin Panel](#-admin-panel)
- [Multi-Tenancy](#-multi-tenancy)
- [API Reference](#-api-reference)
- [Usage Examples](#-usage-examples)
- [Webhook System](#-webhook-system)
- [Smart Sync](#-smart-sync)
- [Offline Sync](#-offline-sync)
- [Security](#-security)
- [Configuration](#-configuration)
- [Deployment](#-deployment)
- [Monitoring](#-monitoring)
- [Testing](#-testing)
- [Documentation](#-documentation)
- [Contributing](#-contributing)
- [Support](#-support)
- [License](#-license)

---

## 🌟 Overview

BridgeCore is an enterprise-grade multi-tenant middleware platform that serves as a unified interface between Flutter mobile applications and multiple external systems including **Odoo ERP**, **Moodle LMS**, **SAP**, **Salesforce**, and more. It provides comprehensive tenant management, real-time change tracking, smart synchronization, and a full-featured admin dashboard with multi-system support.

### 🎯 What BridgeCore Does

- **🔌 Multi-System Integration**: Connect to Odoo ERP, Moodle LMS, SAP, Salesforce, and more from a single platform
- **🏢 Multi-Tenant Management**: Manage multiple companies/clients from a single platform with complete data isolation
- **⚡ Real-time Sync**: Track all Odoo changes via webhook system with smart multi-user synchronization
- **📊 Smart Synchronization**: Efficient incremental sync per user/device with automatic conflict resolution
- **📱 Offline-First Sync**: Complete offline sync with push/pull, conflict resolution, and batch processing
- **🎓 Moodle LMS Integration**: Full course, user, and enrolment management for educational platforms
- **🎨 Admin Dashboard**: Full React-based admin panel for comprehensive platform and system management
- **🚦 Rate Limiting**: Per-tenant rate limits with Redis for fair resource allocation
- **📈 Analytics**: Comprehensive usage tracking, reporting, and business intelligence
- **🔒 Secure**: JWT authentication with role-based access control and encryption
- **🔌 Extensible**: Plugin architecture for custom integrations and business logic

### 💡 Use Cases

#### 1. **SaaS Platform**
Offer Odoo integration as a service to multiple clients:
- White-label solution for partners
- Subscription-based pricing models
- Automated billing and usage tracking
- Multi-tenant isolation and security

#### 2. **Mobile Apps**
Connect Flutter apps to multiple systems (Odoo ERP, Moodle LMS) for multiple tenants:
- **Offline-first mobile applications** with complete sync system
- Real-time data synchronization with conflict resolution
- Push notifications for critical changes
- Field service management with offline capabilities
- Multi-device sync per user
- **Educational apps** with Moodle LMS integration

#### 2.1 **Educational Platforms**
Connect educational institutions to Moodle LMS:
- Course management and enrolment
- Student and teacher management
- Grade tracking and reporting
- Assignment submission workflows
- Learning analytics and progress tracking

#### 3. **Enterprise Solutions**
Centralized middleware for large-scale deployments:
- Single API for multiple Odoo instances
- Unified authentication and authorization
- Centralized logging and monitoring
- Compliance and audit trails

#### 4. **Multi-Company Setup**
Single platform managing multiple Odoo instances:
- Holding companies with subsidiaries
- Franchise management systems
- Multi-brand retail operations
- International operations

### 🚀 Why BridgeCore?

| Challenge | BridgeCore Solution |
|-----------|---------------------|
| **Multiple Systems** | Single API for Odoo, Moodle, SAP, Salesforce, and more |
| **Multiple Odoo Versions** | Version-agnostic API with automatic adaptation |
| **LMS Integration** | Full Moodle Web Services integration with 15+ endpoints |
| **Complex Authentication** | Unified JWT-based auth for all tenants and systems |
| **Rate Limiting** | Per-tenant limits with fair resource allocation |
| **Real-time Sync** | Webhook system with smart multi-user sync |
| **Monitoring** | Built-in analytics, logging, and metrics |
| **Scalability** | Async architecture with Redis caching |
| **Security** | Encryption, RBAC, audit logs |
| **Admin Tools** | Full-featured React dashboard with system management |

---

## ✨ Key Features

### 🔌 Multi-System Architecture (NEW!)

#### Supported Systems
- **✅ Odoo ERP**: Full integration with 26+ endpoints
- **✅ Moodle LMS**: Course, user, and enrolment management (15+ endpoints)
- **🔄 SAP ERP**: Coming soon
- **🔄 Salesforce CRM**: Coming soon
- **🔄 Microsoft Dynamics**: Coming soon

#### System Management
- **Flexible Connections**: Each tenant can connect to multiple systems simultaneously
- **Primary System**: Designate a primary system per tenant
- **Connection Testing**: Built-in connection health checks
- **Encrypted Configs**: All system credentials encrypted at rest
- **System Adapters**: Unified interface for all external systems

#### Moodle LMS Integration Features
```
📚 Course Management
  • Create, update, delete courses
  • Get course details and lists
  • Get enrolled users per course

👥 User Management
  • Create and update Moodle users
  • Search users by criteria
  • User profile management

🎓 Enrolment Management
  • Enrol users in courses
  • Manage roles (student, teacher)
  • Track enrolment status

📊 System Information
  • Get site info and version
  • Health checks and monitoring
  • Call any Moodle Web Service function
```

### 🏢 Multi-Tenant Architecture

#### Tenant Isolation
- **Complete Data Isolation**: Each tenant's data is completely isolated
- **Multiple System Connections**: Each tenant connects to their own instances (Odoo, Moodle, etc.)
- **Independent Configuration**: Per-tenant settings and customizations
- **Secure Credentials**: Encrypted storage of all system credentials

#### Subscription Management
- **Multiple Plans**: Free, Starter, Professional, Enterprise
- **Usage-Based Billing**: Track API usage per tenant
- **Flexible Limits**: Configure rate limits per plan
- **Trial Periods**: Automatic trial management

#### Tenant Lifecycle
```
┌──────────┐    ┌──────────┐    ┌───────────┐    ┌──────────┐
│  Trial   │ -> │  Active  │ -> │ Suspended │ -> │ Deleted  │
└──────────┘    └──────────┘    └───────────┘    └──────────┘
     │               │                │                │
     └───────────────┴────────────────┴────────────────┘
              Automatic state management
```

### 🎨 Admin Panel (React Dashboard)

#### Dashboard Overview
- **Real-time Statistics**: Active tenants, API requests, error rates
- **System Health**: Database, Redis, Celery status
- **Quick Actions**: Create tenant, view logs, run reports
- **Performance Metrics**: Response times, throughput

#### Tenant Management
- **CRUD Operations**: Create, Read, Update, Delete tenants
- **Connection Testing**: Verify Odoo connectivity before activation
- **Status Management**: Activate, suspend, or delete tenants
- **User Management**: Manage tenant users with Odoo linking
- **Odoo Version Detection**: Automatic version detection on connection test

#### Analytics Dashboard
- **Requests Over Time**: Line charts showing API usage trends
- **Status Distribution**: Pie charts of HTTP response codes
- **Response Times**: Performance metrics by endpoint
- **Top Tenants**: Most active tenants ranking
- **Top Endpoints**: Most used API endpoints
- **Custom Date Ranges**: Flexible time period selection

#### Logs Management
- **Usage Logs**: Complete API request history with filters
- **Error Logs**: Error tracking with severity levels
- **Error Resolution**: Workflow for marking errors as resolved
- **Export Functionality**: Download logs as CSV
- **Advanced Filtering**: By tenant, method, status, date range

### 🔐 Authentication & Security

#### Dual JWT System
```python
# Admin Authentication
POST /admin/auth/login
-> admin_token (24h expiry)

# Tenant Authentication
POST /api/v1/auth/tenant/login
-> access_token (30min) + refresh_token (7 days)
```

#### Security Features
- **Password Hashing**: bcrypt with configurable rounds
- **Token Refresh**: Automatic token refresh mechanism
- **Role-Based Access**: Super Admin, Admin, Support, User roles
- **Encryption**: AES-256 encryption for sensitive data
- **Audit Logging**: Complete audit trail for all operations
- **IP Whitelisting**: Optional IP-based access control
- **CORS Protection**: Configurable CORS policies

#### Enhanced User Information
The `/me` endpoint provides comprehensive user data:
- **Partner ID**: Odoo partner record ID
- **Employee ID**: Odoo employee record ID (if applicable)
- **Groups**: Complete list of Odoo security groups
- **Permissions**: Admin status, internal user status
- **Companies**: All accessible companies and current company
- **Custom Fields**: Optional Odoo custom fields

### 🔗 Webhook System

#### Real-time Change Detection
- **Instant Notifications**: Receive Odoo changes in real-time
- **Model Discovery**: Automatic discovery of Odoo models
- **Event Types**: Create, update, delete events
- **Batch Processing**: Handle multiple events efficiently

#### Smart Multi-User Sync
```
┌─────────────┐
│ Odoo Change │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Webhook Handler │
└──────┬──────────┘
       │
       ├──> User 1 (Device A)
       ├──> User 1 (Device B)
       ├──> User 2 (Device A)
       └──> User N (Device X)
```

#### Reliability Features
- **Retry Mechanism**: Exponential backoff for failed events
- **Dead Letter Queue**: Handle permanently failed events
- **Event Deduplication**: Prevent duplicate processing
- **Ordered Processing**: Maintain event order per record

### ⚡ Performance

#### Caching Strategy
- **Redis Caching**: Fast data retrieval with TTL
- **Query Optimization**: Indexed database queries
- **Connection Pooling**: Reuse database connections
- **Response Compression**: Gzip compression for large responses

#### Async Architecture
```python
# All I/O operations are async
async def get_partners(tenant_id: str):
    async with db.session() as session:
        result = await session.execute(query)
        return result.scalars().all()
```

#### Background Tasks
- **Celery Workers**: Async task processing
- **Scheduled Jobs**: Hourly/daily statistics aggregation
- **Log Cleanup**: Automatic old log deletion
- **Report Generation**: Scheduled report generation

### 📊 Monitoring & Analytics

#### Prometheus Metrics
```
# Available metrics
bridgecore_requests_total{tenant, endpoint, status}
bridgecore_request_duration_seconds{endpoint}
bridgecore_active_tenants
bridgecore_errors_total{type, severity}
bridgecore_cache_hits_total
bridgecore_cache_misses_total
```

#### Grafana Dashboards
- **System Overview**: Overall platform health
- **Tenant Analytics**: Per-tenant performance
- **Error Tracking**: Error rates and types
- **Performance**: Response times and throughput

#### Built-in Analytics
- **Usage Statistics**: API calls per tenant/endpoint
- **Error Analysis**: Error patterns and trends
- **Performance Metrics**: Response time percentiles
- **Tenant Ranking**: Most active tenants

---

## 🏗️ Architecture

### System Architecture

```
                          BridgeCore Platform
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              Admin Dashboard (React + TypeScript)            │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │   │
│  │  │  Dashboard   │ │   Tenants    │ │     Analytics        │ │   │
│  │  │   Overview   │ │  Management  │ │   & Reporting        │ │   │
│  │  └──────────────┘ └──────────────┘ └──────────────────────┘ │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │   │
│  │  │  Usage Logs  │ │  Error Logs  │ │   User Management    │ │   │
│  │  └──────────────┘ └──────────────┘ └──────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                   Admin API (FastAPI)                        │   │
│  │  /admin/auth/*     /admin/tenants/*    /admin/analytics/*   │   │
│  │  /admin/plans/*    /admin/logs/*       /admin/users/*       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│  ┌───────────────────────────┼───────────────────────────────────┐ │
│  │                    Middleware Layer                           │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │ │
│  │  │   Usage     │ │   Tenant    │ │      Rate Limit         │ │ │
│  │  │  Tracking   │ │   Context   │ │   (Per-Tenant/Redis)    │ │ │
│  │  └─────────────┘ └─────────────┘ └─────────────────────────┘ │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │ │
│  │  │   Error     │ │   Request   │ │      Encryption         │ │ │
│  │  │  Handling   │ │   Logging   │ │      Middleware         │ │ │
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
│  │  ┌────────────────┐ ┌────────────────┐ ┌─────────────────┐  │   │
│  │  │ Hourly Stats   │ │  Daily Stats   │ │   Log Cleanup   │  │   │
│  │  │  Aggregation   │ │  Aggregation   │ │   (90 days)     │  │   │
│  │  └────────────────┘ └────────────────┘ └─────────────────┘  │   │
│  │  ┌────────────────┐ ┌────────────────┐ ┌─────────────────┐  │   │
│  │  │ Report         │ │  Webhook       │ │   Email         │  │   │
│  │  │ Generation     │ │  Retry         │ │   Notifications │  │   │
│  │  └────────────────┘ └────────────────┘ └─────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
│  │ PostgreSQL  │ │    Redis    │ │  Prometheus │ │   Grafana   │   │
│  │ (Database)  │ │   (Cache)   │ │ (Monitoring)│ │ (Analytics) │   │
│  │   Async     │ │  + Celery   │ │             │ │             │   │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Tenant Odoo Instances                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
│  │  Tenant A   │ │  Tenant B   │ │  Tenant C   │ │  Tenant N   │   │
│  │   Odoo 17   │ │   Odoo 16   │ │   Odoo 15   │ │   Odoo 18   │   │
│  │  + Webhooks │ │  + Webhooks │ │  + Webhooks │ │  + Webhooks │   │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Backend API** | FastAPI | 0.104+ | High-performance async API |
| **Admin Dashboard** | React | 18.2+ | Modern UI framework |
| **Language** | TypeScript | 5.2+ | Type-safe frontend |
| **UI Components** | Ant Design | 5.12+ | Enterprise UI components |
| **State Management** | Zustand | 4.4+ | Lightweight state management |
| **Charts** | Recharts | 2.10+ | Data visualization |
| **Database** | PostgreSQL | 15+ | Relational database |
| **DB Driver** | asyncpg | Latest | Async PostgreSQL driver |
| **Cache** | Redis | 7+ | In-memory data store |
| **ORM** | SQLAlchemy | 2.0+ | Async ORM |
| **Migrations** | Alembic | Latest | Database migrations |
| **Background Tasks** | Celery | Latest | Async task queue |
| **Authentication** | JWT | - | Token-based auth |
| **Password Hashing** | bcrypt | - | Secure password storage |
| **Monitoring** | Prometheus | Latest | Metrics collection |
| **Visualization** | Grafana | Latest | Metrics dashboards |
| **Containerization** | Docker | Latest | Application containerization |
| **Orchestration** | Docker Compose | Latest | Multi-container orchestration |
| **Reverse Proxy** | Traefik | Latest | Edge router |
| **Web Server** | Nginx | Latest | Static file serving |

---

## 🚀 Quick Start

### Prerequisites

- **Python**: 3.11 or higher
- **Node.js**: 18 or higher (for Admin Dashboard)
- **PostgreSQL**: 15 or higher
- **Redis**: 7 or higher
- **Docker**: Latest version (recommended)
- **Docker Compose**: Latest version (recommended)

### Option 1: Docker (Recommended) 🐳

```bash
# 1. Clone repository
git clone https://github.com/geniustep/BridgeCore.git
cd BridgeCore

# 2. Setup environment
cp env.example .env

# 3. Edit .env with your configuration
nano .env  # or use your favorite editor

# 4. Start all services
docker-compose up -d

# 5. View logs
docker-compose logs -f

# 6. Check service status
docker-compose ps
```

**Services will be available at:**
- 🌐 **API**: http://localhost:8000
- 📚 **API Docs**: http://localhost:8000/docs
- 🎨 **Admin Dashboard**: http://localhost:3000
- 📊 **Prometheus**: http://localhost:9090
- 📈 **Grafana**: http://localhost:3001

### Option 2: Local Development 💻

#### Quick Installation (Automated)

```bash
# 1. Clone repository
git clone https://github.com/geniustep/BridgeCore.git
cd BridgeCore

# 2. Run automated installation script
bash scripts/install_dependencies.sh

# This script will:
# - Check Python version (requires 3.11+)
# - Create virtual environment
# - Install all dependencies
# - Verify installation
```

#### Manual Installation

```bash
# 1. Clone repository
git clone https://github.com/geniustep/BridgeCore.git
cd BridgeCore

# 2. Setup Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development

# 3. Setup environment
cp env.example .env
# Edit .env with your configuration

# 4. Start PostgreSQL and Redis
# Make sure PostgreSQL and Redis are running

# 5. Run database migrations
alembic upgrade head

# 6. Seed initial data (admin user & plans)
python scripts/seed_admin.py

# 7. Start API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 8. In another terminal, start Celery worker
celery -A app.celery_app worker --loglevel=info

# 9. In another terminal, start Celery beat
celery -A app.celery_app beat --loglevel=info

# 10. In another terminal, start Admin Dashboard
cd admin
npm install
npm run dev
```

### Default Admin Credentials 🔑

After running the seed script:
- **Email**: `admin@bridgecore.local`
- **Password**: `admin123`

**⚠️ Important**: Change these credentials immediately in production!

### First Steps After Installation

1. **Login to Admin Dashboard**: http://localhost:3000
2. **Change Admin Password**: Profile → Change Password
3. **Create First Tenant**: Tenants → Create Tenant
4. **Test Odoo Connection**: Tenant Details → Test Connection
5. **Create Tenant User**: Tenant Users → Create User
6. **Test API**: Use Swagger docs at http://localhost:8000/docs

---

## 🎨 Admin Panel

The BridgeCore Admin Panel is a comprehensive React-based dashboard for managing the entire platform.

### Dashboard Overview

**Key Metrics:**
- 📊 Total Tenants (Active/Suspended/Trial)
- 🔥 API Requests (Last 24 hours)
- ⚠️ Error Rate (Percentage)
- 👥 Total Users
- 💾 Database Size
- 🚀 System Uptime

**Quick Actions:**
- ➕ Create New Tenant
- 👤 Create New User
- 📊 View Analytics
- 📝 View Logs
- ⚙️ System Settings

### Tenant Management

#### List View
```
┌────────────────────────────────────────────────────────────┐
│ Tenants                                    [+ Create]       │
├────────────────────────────────────────────────────────────┤
│ Name          │ Status    │ Plan      │ Users │ Requests  │
├───────────────┼───────────┼───────────┼───────┼───────────┤
│ Company A     │ 🟢 Active │ Pro       │ 45    │ 12.5K     │
│ Company B     │ 🟡 Trial  │ Starter   │ 5     │ 1.2K      │
│ Company C     │ 🔴 Susp.  │ Free      │ 2     │ 0         │
└────────────────────────────────────────────────────────────┘
```

#### Create/Edit Tenant
- **Basic Information**: Name, slug, contact email
- **Odoo Connection**: URL, database, username, password
- **Subscription Plan**: Free, Starter, Professional, Enterprise
- **Rate Limits**: Custom per-tenant limits
- **Allowed Models**: Whitelist Odoo models
- **Features**: Enable/disable features per tenant
- **User Limits**: Maximum users allowed
- **Connection Test**: Verify Odoo connectivity
- **Auto-detect Odoo Version**: Automatic version detection

#### Tenant Users
- **Create User**: Link to Odoo user
- **Select Company**: Choose Odoo company
- **Select Odoo User**: Pick from company users
- **Auto-populate**: Email and name from Odoo
- **User Limits**: Enforce max users per tenant
- **Security**: Unique Odoo user per tenant

### Analytics Dashboard

#### Requests Over Time
```
Line Chart showing API requests per hour/day/week
- Filter by tenant
- Compare multiple tenants
- Export data
```

#### Status Distribution
```
Pie Chart showing HTTP status codes
- 2xx Success (green)
- 4xx Client Errors (yellow)
- 5xx Server Errors (red)
```

#### Response Times
```
Bar Chart showing average response times
- By endpoint
- By hour of day
- Percentiles (p50, p95, p99)
```

#### Top Tenants
```
Table showing most active tenants
- Total requests
- Error rate
- Average response time
- Last activity
```

### Logs Management

#### Usage Logs
```
┌────────────────────────────────────────────────────────────┐
│ Filters: [Tenant ▼] [Method ▼] [Status ▼] [Date Range]    │
├────────────────────────────────────────────────────────────┤
│ Time       │ Tenant   │ Method │ Endpoint     │ Status     │
├────────────┼──────────┼────────┼──────────────┼────────────┤
│ 10:30:45   │ Comp. A  │ POST   │ /odoo/search │ 200 (45ms) │
│ 10:30:43   │ Comp. B  │ GET    │ /auth/me     │ 200 (12ms) │
│ 10:30:40   │ Comp. A  │ POST   │ /odoo/create │ 429 (5ms)  │
└────────────────────────────────────────────────────────────┘
```

#### Error Logs
```
┌────────────────────────────────────────────────────────────┐
│ Severity: [All ▼] Status: [Unresolved ▼]                  │
├────────────────────────────────────────────────────────────┤
│ Time       │ Tenant   │ Error        │ Severity │ Status   │
├────────────┼──────────┼──────────────┼──────────┼──────────┤
│ 10:25:30   │ Comp. A  │ DB Timeout   │ 🔴 High  │ Open     │
│ 10:20:15   │ Comp. B  │ Invalid Auth │ 🟡 Med   │ Resolved │
└────────────────────────────────────────────────────────────┘
```

---

## 🏢 Multi-Tenancy

### Tenant Model

Each tenant represents a company/client using BridgeCore:

```python
{
    "id": "9b230aba-8477-4979-a345-04c9b255cf45",
    "name": "Acme Corporation",
    "slug": "acme-corp",
    "status": "active",  # active, trial, suspended, deleted
    "contact_email": "admin@acme.com",
    
    # Odoo Connection
    "odoo_url": "https://acme.odoo.com",
    "odoo_database": "acme_production",
    "odoo_username": "api_user",
    "odoo_password": "encrypted_password",
    "odoo_version": "18.0",  # Auto-detected
    
    # Subscription
    "plan_id": "uuid",
    "max_requests_per_day": 100000,
    "max_requests_per_hour": 10000,
    "max_users": 100,
    
    # Configuration
    "allowed_models": ["res.partner", "sale.order", "product.product"],
    "allowed_features": ["sync", "webhooks", "batch"],
    
    # Timestamps
    "created_at": "2025-01-15T10:00:00Z",
    "updated_at": "2025-11-22T15:30:00Z",
    "last_activity": "2025-11-22T21:00:00Z"
}
```

### Subscription Plans

| Feature | Free | Starter | Professional | Enterprise |
|---------|------|---------|--------------|------------|
| **Daily Requests** | 1,000 | 10,000 | 100,000 | Unlimited |
| **Hourly Requests** | 100 | 1,000 | 10,000 | Unlimited |
| **Users** | 5 | 25 | 100 | Unlimited |
| **Storage** | 1 GB | 10 GB | 100 GB | Unlimited |
| **Webhooks** | ❌ | ✅ | ✅ | ✅ |
| **Smart Sync** | ❌ | ✅ | ✅ | ✅ |
| **Batch Operations** | ❌ | ❌ | ✅ | ✅ |
| **Priority Support** | ❌ | ❌ | ✅ | ✅ |
| **SLA** | - | 99% | 99.9% | 99.99% |
| **Custom Integration** | ❌ | ❌ | ❌ | ✅ |

### Rate Limiting

Rate limits are enforced at multiple levels:

#### 1. Per-Tenant Rate Limiting (Subscription-based)

Rate limits are enforced per-tenant using Redis based on subscription plan:

```python
# Hourly limit check
hourly_key = f"rate_limit:tenant:{tenant_id}:hour:{current_hour}"
hourly_count = await redis.incr(hourly_key)
await redis.expire(hourly_key, 3600)  # 1 hour TTL

if hourly_count > tenant.max_requests_per_hour:
    raise HTTPException(
        status_code=429,
        detail="Hourly rate limit exceeded"
    )

# Daily limit check
daily_key = f"rate_limit:tenant:{tenant_id}:day:{current_day}"
daily_count = await redis.incr(daily_key)
await redis.expire(daily_key, 86400)  # 24 hours TTL

if daily_count > tenant.max_requests_per_day:
    raise HTTPException(
        status_code=429,
        detail="Daily rate limit exceeded"
    )
```

#### 2. Per-Endpoint Rate Limiting (Operation-based)

Each Odoo endpoint has intelligent rate limiting based on operation cost:

| Operation Type | Rate Limit | Reason |
|----------------|------------|--------|
| Search operations | 100/minute | Lightweight, read-only |
| Read operations | 80/minute | Database reads |
| Create operations | 30/minute | More expensive, writes |
| Write operations | 40/minute | Updates |
| Delete operations | 20/minute | Critical operations |
| Advanced operations | 50/minute | Complex queries |
| Name operations | 100/minute | Lightweight lookups |
| View operations | 60/minute | Metadata retrieval |
| Web operations | 50/minute | Web-optimized |
| Permission checks | 100/minute | Lightweight |
| Utility operations | 80/minute | Field metadata |
| Custom methods | 30/minute | Can be expensive |

**Rate Limit Headers:**
When a rate limit is exceeded, the API returns:
- `429 Too Many Requests` status code
- `Retry-After` header with seconds until retry
- `X-RateLimit-Limit` header with the limit
- `X-RateLimit-Remaining` header with remaining requests

### Tenant Isolation

**Data Isolation:**
- Separate database rows per tenant
- Tenant ID in all queries
- Row-level security policies

**Connection Isolation:**
- Separate Odoo connections per tenant
- Connection pooling per tenant
- Automatic connection cleanup

**Security Isolation:**
- JWT tokens include tenant ID
- Middleware validates tenant access
- Encrypted credentials per tenant

---

## 📡 API Reference

> 📖 **Complete API Documentation**: See [docs/api/](./docs/api/) for detailed API reference

### Admin API Endpoints

#### Authentication

```bash
# Admin Login
POST /admin/auth/login
Content-Type: application/json

{
    "email": "admin@bridgecore.local",
    "password": "admin123"
}

# Response
{
    "access_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 86400,
    "admin": {
        "id": "uuid",
        "email": "admin@bridgecore.local",
        "full_name": "Admin User",
        "role": "super_admin"
    }
}

# Get Current Admin
GET /admin/auth/me
Authorization: Bearer {admin_token}

# Logout
POST /admin/auth/logout
Authorization: Bearer {admin_token}

# Refresh Token
POST /admin/auth/refresh
Authorization: Bearer {admin_token}
```

#### Tenant Management

```bash
# List Tenants
GET /admin/tenants?status=active&skip=0&limit=100
Authorization: Bearer {admin_token}

# Create Tenant
POST /admin/tenants
Authorization: Bearer {admin_token}
Content-Type: application/json

{
    "name": "New Company",
    "slug": "new-company",
    "contact_email": "contact@newcompany.com",
    "odoo_url": "https://newcompany.odoo.com",
    "odoo_database": "newcompany_db",
    "odoo_username": "api_user",
    "odoo_password": "secure_password",
    "plan_id": "uuid",
    "max_users": 50
}

# Get Tenant
GET /admin/tenants/{tenant_id}
Authorization: Bearer {admin_token}

# Update Tenant
PUT /admin/tenants/{tenant_id}
Authorization: Bearer {admin_token}
Content-Type: application/json

{
    "name": "Updated Company Name",
    "max_requests_per_day": 20000
}

# Test Connection (Auto-detects Odoo version)
POST /admin/tenants/{tenant_id}/test-connection
Authorization: Bearer {admin_token}

# Response
{
    "success": true,
    "message": "Connection successful",
    "odoo_version": "18.0",
    "admin_user": {
        "email": "admin@company.bridgecore.internal",
        "password": "generated_password"
    }
}

# Suspend Tenant
POST /admin/tenants/{tenant_id}/suspend
Authorization: Bearer {admin_token}

# Activate Tenant
POST /admin/tenants/{tenant_id}/activate
Authorization: Bearer {admin_token}

# Delete Tenant
DELETE /admin/tenants/{tenant_id}
Authorization: Bearer {admin_token}
```

#### Tenant Users

```bash
# List Tenant Users
GET /admin/tenant-users?tenant_id={tenant_id}
Authorization: Bearer {admin_token}

# Create Tenant User
POST /admin/tenant-users
Authorization: Bearer {admin_token}
Content-Type: application/json

{
    "tenant_id": "uuid",
    "email": "user@company.com",
    "full_name": "John Doe",
    "password": "secure_password",
    "role": "user",
    "odoo_user_id": 6
}

# Get Odoo Companies
GET /admin/odoo-helpers/companies/{tenant_id}
Authorization: Bearer {admin_token}

# Get Odoo Users
GET /admin/odoo-helpers/users/{tenant_id}?company_id=1
Authorization: Bearer {admin_token}
```

### Moodle API Endpoints (NEW!)

#### Course Management

```bash
# Get All Courses
GET /api/v1/moodle/courses
Authorization: Bearer {token}

# Response
[
  {
    "id": 2,
    "fullname": "Introduction to Programming",
    "shortname": "CS101",
    "categoryid": 1,
    "visible": 1,
    "enrolledusercount": 45
  }
]

# Create Course
POST /api/v1/moodle/courses
Authorization: Bearer {token}
Content-Type: application/json

{
  "fullname": "Web Development Basics",
  "shortname": "WEB101",
  "categoryid": 1,
  "summary": "Learn HTML, CSS, and JavaScript",
  "format": "topics",
  "visible": 1
}

# Update Course
PUT /api/v1/moodle/courses/{course_id}
Authorization: Bearer {token}

{
  "fullname": "Advanced Web Development",
  "visible": 1
}

# Delete Course
DELETE /api/v1/moodle/courses/{course_id}
Authorization: Bearer {token}

# Get Enrolled Users
GET /api/v1/moodle/courses/{course_id}/users
Authorization: Bearer {token}

# Enrol User in Course
POST /api/v1/moodle/courses/{course_id}/enrol
Authorization: Bearer {token}

{
  "user_id": 15,
  "role_id": 5  # 5 = Student, 3 = Teacher
}
```

#### User Management

```bash
# Get Users
GET /api/v1/moodle/users?username=john
Authorization: Bearer {token}

# Create User
POST /api/v1/moodle/users
Authorization: Bearer {token}

{
  "username": "newstudent",
  "password": "SecurePass123!",
  "firstname": "Jane",
  "lastname": "Smith",
  "email": "jane@school.com",
  "city": "Boston",
  "country": "US"
}

# Update User
PUT /api/v1/moodle/users/{user_id}
Authorization: Bearer {token}

{
  "email": "newemail@school.com",
  "city": "San Francisco"
}

# Delete User
DELETE /api/v1/moodle/users/{user_id}
Authorization: Bearer {token}
```

#### System Information

```bash
# Get Site Info
GET /api/v1/moodle/site-info
Authorization: Bearer {token}

# Response
{
  "sitename": "Your School LMS",
  "version": "4.1.5",
  "userid": 2,
  "siteurl": "https://lms.school.com"
}

# Check Connection Health
GET /api/v1/moodle/health
Authorization: Bearer {token}

# Response
{
  "status": "connected",
  "latency_ms": 145.32,
  "timestamp": 1701020400
}

# Call Any Moodle Function
POST /api/v1/moodle/call
Authorization: Bearer {token}

{
  "function_name": "core_course_get_categories",
  "params": {}
}
```

### Tenant API Endpoints

#### Authentication

```bash
# Tenant User Login
POST /api/v1/auth/tenant/login
Content-Type: application/json

{
    "email": "user@company.com",
    "password": "password123"
}

# Response
{
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
        "id": "uuid",
        "email": "user@company.com",
        "full_name": "John Doe",
        "role": "user",
        "odoo_user_id": 6
    },
    "tenant": {
        "id": "uuid",
        "name": "Company Name",
        "slug": "company-slug",
        "status": "active",
        "odoo_url": "https://company.odoo.com",
        "odoo_database": "company_db",
        "odoo_version": "18.0"
    }
}

# Login with Custom Fields Check
POST /api/v1/auth/tenant/login
Content-Type: application/json

{
    "email": "user@company.com",
    "password": "password123",
    "odoo_fields_check": {
        "model": "res.users",
        "list_fields": ["shuttle_role", "department_id"]
    }
}

# Get Current User Info
POST /api/v1/auth/tenant/me
Authorization: Bearer {tenant_token}
Content-Type: application/json

{
    "odoo_fields_check": {
        "model": "res.users",
        "list_fields": ["shuttle_role"]
    }
}

# Response
{
    "user": {...},
    "tenant": {...},
    "partner_id": 7,
    "employee_id": null,
    "groups": ["base.group_user", "shuttlebee.group_shuttle_driver"],
    "is_admin": false,
    "is_internal_user": true,
    "company_ids": [1],
    "current_company_id": 1,
    "odoo_fields_data": {
        "shuttle_role": "driver"
    }
}

# Refresh Token
POST /api/v1/auth/tenant/refresh
Content-Type: application/json

{
    "refresh_token": "eyJ..."
}

# Logout
POST /api/v1/auth/tenant/logout
Authorization: Bearer {tenant_token}
```

#### Odoo Operations (26 Complete Operations)

**🔐 Security**: All Odoo operations use tenant JWT tokens. Odoo credentials are automatically fetched from tenant database - **NO credentials needed in requests!**

**🚦 Rate Limiting**: All endpoints have intelligent rate limiting based on operation type:
- Search operations: 100/minute (lightweight)
- Read operations: 80/minute
- Create operations: 30/minute (more expensive)
- Write operations: 40/minute
- Delete operations: 20/minute
- Advanced operations: 50/minute
- Custom methods: 30/minute

**Available Operations:**

**CRUD Operations** (`/api/v1/odoo/`):
- `POST /create` - Create new record(s)
- `POST /read` - Read records by ID
- `POST /write` - Update existing records
- `POST /unlink` - Delete records

**Search Operations** (`/api/v1/odoo/`):
- `POST /search` - Search for records (returns IDs only)
- `POST /search_read` - Search and read in one operation
- `POST /search_count` - Count records matching domain

**Advanced Operations** (`/api/v1/odoo/`):
- `POST /onchange` - Trigger onchange methods
- `POST /read_group` - Group and aggregate data
- `POST /copy` - Duplicate records
- `POST /exists` - Check if records exist

**Name Operations** (`/api/v1/odoo/`):
- `POST /name_get` - Get display names
- `POST /name_search` - Search by name
- `POST /name_create` - Quick create from name

**View Operations** (`/api/v1/odoo/`):
- `POST /fields_view_get` - Get view definition
- `POST /load_views` - Load multiple views
- `POST /get_views` - Get specific views

**Web Operations** (`/api/v1/odoo/`):
- `POST /web_read` - Web-optimized read
- `POST /web_save` - Web-optimized save
- `POST /web_search_read` - Web-optimized search_read

**Permission Operations** (`/api/v1/odoo/`):
- `POST /check_access_rights` - Check access permissions
- `POST /check_field_access` - Check field-level permissions

**Utility Operations** (`/api/v1/odoo/`):
- `POST /fields_get` - Get field definitions
- `POST /default_get` - Get default values
- `POST /get_metadata` - Get record metadata

**Custom Methods** (`/api/v1/odoo/`):
- `POST /call_method` - Call custom model methods
- `POST /call_kw` - Call methods with keyword arguments
- `POST /execute` - Execute arbitrary methods

**Example Requests:**

```bash
# Search & Read
POST /api/v1/odoo/search_read
Authorization: Bearer {tenant_token}
Content-Type: application/json

{
    "model": "res.partner",
    "domain": [["customer_rank", ">", 0]],
    "fields": ["id", "name", "email", "phone"],
    "limit": 100,
    "offset": 0,
    "order": "name ASC"
}

# Create
POST /api/v1/odoo/create
Authorization: Bearer {tenant_token}
Content-Type: application/json

{
    "model": "res.partner",
    "values": {
        "name": "New Customer",
        "email": "customer@example.com",
        "phone": "+1234567890",
        "is_company": true
    }
}

# Update
POST /api/v1/odoo/write
Authorization: Bearer {tenant_token}
Content-Type: application/json

{
    "model": "res.partner",
    "ids": [1, 2, 3],
    "values": {
        "phone": "+1234567890",
        "mobile": "+0987654321"
    }
}

# Delete
POST /api/v1/odoo/unlink
Authorization: Bearer {tenant_token}
Content-Type: application/json

{
    "model": "res.partner",
    "ids": [1, 2, 3]
}
```

---

## 💡 Usage Examples

### Example 1: Complete Authentication Flow

```python
import requests

# 1. Tenant User Login
login_response = requests.post(
    "https://api.bridgecore.com/api/v1/auth/tenant/login",
    json={
        "email": "user@company.com",
        "password": "password123"
    }
)

tokens = login_response.json()
access_token = tokens["access_token"]
refresh_token = tokens["refresh_token"]

# 2. Get User Info
me_response = requests.post(
    "https://api.bridgecore.com/api/v1/auth/tenant/me",
    headers={"Authorization": f"Bearer {access_token}"}
)

user_info = me_response.json()
print(f"Partner ID: {user_info['partner_id']}")
print(f"Is Admin: {user_info['is_admin']}")
print(f"Groups: {user_info['groups']}")

# 3. Refresh Token (when access token expires)
refresh_response = requests.post(
    "https://api.bridgecore.com/api/v1/auth/tenant/refresh",
    json={"refresh_token": refresh_token}
)

new_tokens = refresh_response.json()
access_token = new_tokens["access_token"]

# 4. Logout
requests.post(
    "https://api.bridgecore.com/api/v1/auth/tenant/logout",
    headers={"Authorization": f"Bearer {access_token}"}
)
```

### Example 2: CRUD Operations on Odoo

```python
import requests

BASE_URL = "https://api.bridgecore.com"
headers = {"Authorization": f"Bearer {access_token}"}

# Create a new partner
create_response = requests.post(
    f"{BASE_URL}/api/v1/odoo/create",
    headers=headers,
    json={
        "model": "res.partner",
        "values": {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "is_company": False
        }
    }
)

partner_id = create_response.json()["id"]
print(f"Created partner with ID: {partner_id}")

# Read partners
search_response = requests.post(
    f"{BASE_URL}/api/v1/odoo/search_read",
    headers=headers,
    json={
        "model": "res.partner",
        "domain": [["email", "=", "john@example.com"]],
        "fields": ["id", "name", "email", "phone"]
    }
)

partners = search_response.json()
print(f"Found {len(partners)} partner(s)")

# Update partner
update_response = requests.post(
    f"{BASE_URL}/api/v1/odoo/write",
    headers=headers,
    json={
        "model": "res.partner",
        "ids": [partner_id],
        "values": {
            "phone": "+9876543210"
        }
    }
)

print("Partner updated successfully")

# Delete partner
delete_response = requests.post(
    f"{BASE_URL}/api/v1/odoo/unlink",
    headers=headers,
    json={
        "model": "res.partner",
        "ids": [partner_id]
    }
)

print("Partner deleted successfully")
```

### Example 3: Flutter Integration

```dart
import 'package:bridgecore_flutter/bridgecore_flutter.dart';

void main() async {
  // Initialize BridgeCore
  BridgeCore.initialize(
    baseUrl: 'https://api.bridgecore.com',
    debugMode: true,
  );

  // Login
  final loginResponse = await BridgeCore.instance.auth.login(
    email: 'user@company.com',
    password: 'password123',
  );

  print('Logged in as: ${loginResponse.user.fullName}');

  // Get user info
  final userInfo = await BridgeCore.instance.auth.me();
  print('Partner ID: ${userInfo.partnerId}');
  print('Is Admin: ${userInfo.isAdmin}');
  print('Groups: ${userInfo.groups}');

  // Search partners
  final partners = await BridgeCore.instance.odoo.searchRead(
    model: 'res.partner',
    domain: [['customer_rank', '>', 0]],
    fields: ['id', 'name', 'email'],
    limit: 50,
  );

  print('Found ${partners.length} customers');

  // Create partner
  final partnerId = await BridgeCore.instance.odoo.create(
    model: 'res.partner',
    values: {
      'name': 'New Customer',
      'email': 'customer@example.com',
    },
  );

  print('Created partner with ID: $partnerId');

  // Logout
  await BridgeCore.instance.auth.logout();
}
```

### Example 4: Admin Dashboard Integration

```typescript
import { apiClient } from './services/api';

// Admin login
const adminLogin = async (email: string, password: string) => {
  const response = await apiClient.post('/admin/auth/login', {
    email,
    password,
  });
  
  localStorage.setItem('admin_token', response.data.access_token);
  return response.data;
};

// Get tenants
const getTenants = async () => {
  const response = await apiClient.get('/admin/tenants', {
    params: {
      status: 'active',
      limit: 100,
    },
  });
  
  return response.data;
};

// Create tenant
const createTenant = async (tenantData: TenantCreate) => {
  const response = await apiClient.post('/admin/tenants', tenantData);
  return response.data;
};

// Test connection
const testConnection = async (tenantId: string) => {
  const response = await apiClient.post(
    `/admin/tenants/${tenantId}/test-connection`
  );
  
  return response.data;
};

// Get analytics
const getAnalytics = async (tenantId: string, days: number = 30) => {
  const response = await apiClient.get(
    `/admin/analytics/tenants/${tenantId}`,
    {
      params: { days },
    }
  );
  
  return response.data;
};
```

---

## 🔗 Webhook System

BridgeCore includes a comprehensive webhook system for real-time change tracking from Odoo.

### Architecture

```
┌──────────────┐
│ Odoo Change  │ (Create/Update/Delete)
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│ Odoo Webhook     │ (Configured in Odoo)
│ Module           │
└──────┬───────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ BridgeCore Webhook Handler          │
│ POST /api/v1/webhooks/push           │
└──────┬───────────────────────────────┘
       │
       ├──> Validate Tenant
       ├──> Store Event
       ├──> Update Sync States
       └──> Trigger Notifications
              │
              ├──> User 1 (Device A)
              ├──> User 1 (Device B)
              ├──> User 2 (Device A)
              └──> User N (Device X)
```

### Webhook Operations

```bash
# Push Endpoint (Odoo calls this)
POST /api/v1/webhooks/push
Authorization: Bearer {tenant_token}
Content-Type: application/json

{
    "model": "sale.order",
    "event": "write",
    "record_id": 123,
    "timestamp": "2025-11-22T10:30:00Z",
    "data": {
        "id": 123,
        "name": "SO001",
        "state": "sale"
    }
}

# Check for Updates
GET /api/v1/webhooks/check-updates?limit=50
Authorization: Bearer {tenant_token}

# Response
{
    "has_updates": true,
    "events_count": 25,
    "events": [
        {
            "id": "uuid",
            "model": "sale.order",
            "event": "write",
            "record_id": 123,
            "timestamp": "2025-11-22T10:30:00Z"
        }
    ]
}

# List Events
GET /api/v1/webhooks/events?model=sale.order&limit=100
Authorization: Bearer {tenant_token}

# Mark Events as Processed
POST /api/v1/webhooks/events/mark-processed
Authorization: Bearer {tenant_token}
Content-Type: application/json

{
    "event_ids": ["uuid1", "uuid2", "uuid3"]
}
```

### Smart Sync (v2 API)

```bash
# Smart Sync Pull
POST /api/v2/sync/pull
Authorization: Bearer {tenant_token}
Content-Type: application/json

{
    "user_id": 1,
    "device_id": "device_123",
    "app_type": "sales_app",
    "limit": 100,
    "models": ["sale.order", "res.partner"]
}

# Response
{
    "has_updates": true,
    "new_events_count": 25,
    "events": [
        {
            "model": "sale.order",
            "event": "write",
            "record_id": 123,
            "timestamp": "2025-11-22T10:30:00Z",
            "data": {...}
        }
    ],
    "next_sync_token": "1234",
    "last_sync_time": "2025-11-22T10:30:00Z",
    "sync_state": {
        "user_id": 1,
        "device_id": "device_123",
        "last_event_id": "uuid",
        "last_sync_time": "2025-11-22T10:30:00Z"
    }
}

# Get Sync State
GET /api/v2/sync/state?user_id=1&device_id=device_123
Authorization: Bearer {tenant_token}

# Reset Sync State
POST /api/v2/sync/reset?user_id=1&device_id=device_123
Authorization: Bearer {tenant_token}
```

---

## 📱 Offline Sync

**NEW!** BridgeCore now includes a comprehensive offline-first synchronization system for mobile and web applications.

### Features

✅ **Push/Pull Architecture**: Upload local changes and download server updates
✅ **Conflict Detection**: Automatic conflict detection with multiple resolution strategies
✅ **Dependency Resolution**: Handles complex relationships between records
✅ **Batch Processing**: Efficient processing of multiple changes
✅ **Incremental Sync**: Only sync what changed since last time
✅ **Multi-Device Support**: Each device maintains independent sync state
✅ **Model Filtering**: Sync only relevant data for each app type
✅ **Tenant Isolation**: Complete data isolation per tenant

### Use Cases

- **Mobile Sales App**: Work offline, sync when back online
- **Delivery App**: Update deliveries offline, sync at end of day
- **Warehouse App**: Inventory updates in areas with poor connectivity
- **Field Service**: Work at remote locations without internet
- **CRM App**: Update leads and opportunities offline

### API Endpoints

```bash
# Push local changes to server
POST /api/v1/offline-sync/push
Authorization: Bearer {token}

{
  "device_id": "iphone-abc123",
  "changes": [
    {
      "local_id": "local_uuid_1",
      "action": "create",
      "model": "sale.order",
      "data": {
        "partner_id": 42,
        "order_line": []
      },
      "local_timestamp": "2025-11-24T10:30:00Z"
    }
  ],
  "conflict_strategy": "server_wins"
}

# Pull server changes
POST /api/v1/offline-sync/pull
Authorization: Bearer {token}

{
  "device_id": "iphone-abc123",
  "app_type": "sales_app",
  "last_event_id": 1250,
  "limit": 100
}

# Resolve conflicts
POST /api/v1/offline-sync/resolve-conflicts
Authorization: Bearer {token}

{
  "device_id": "iphone-abc123",
  "resolutions": [
    {
      "local_id": "local_uuid_5",
      "strategy": "client_wins"
    }
  ]
}

# Get sync state
GET /api/v1/offline-sync/state?device_id=iphone-abc123
Authorization: Bearer {token}

# Reset sync state (force full sync)
POST /api/v1/offline-sync/reset?device_id=iphone-abc123
Authorization: Bearer {token}
```

### Conflict Resolution Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| **server_wins** | Server data takes precedence (default) | Settings, configurations |
| **client_wins** | Client data overwrites server | User preferences, drafts |
| **manual** | Return conflict for user to resolve | Critical business data |
| **merge** | Merge both versions | Non-overlapping field changes |
| **newest_wins** | Most recent change wins | Time-sensitive data |

### Complete Sync Flow

```typescript
// 1. Initialize sync service
const syncService = new OfflineSyncService({
  baseUrl: 'https://api.bridgecore.com',
  deviceId: 'iphone-abc123',
  appType: 'sales_app',
});

// 2. Authenticate
await syncService.login(email, password);

// 3. Start background sync
syncService.startBackgroundSync();

// 4. Manual sync
async function manualSync() {
  // Push local changes
  const pushResult = await syncService.push();

  // Handle conflicts
  if (pushResult.conflicts > 0) {
    await handleConflicts(pushResult);
  }

  // Pull server changes
  const pullResult = await syncService.pull();

  // Apply to local database
  await applyEventsToDatabase(pullResult.events);
}
```

### Documentation

📖 **Complete Offline Sync Guide**: [docs/guides/OFFLINE_SYNC_GUIDE.md](./docs/guides/OFFLINE_SYNC_GUIDE.md)
🌍 **دليل باللغة العربية**: [docs/guides/OFFLINE_SYNC_GUIDE_AR.md](./docs/guides/OFFLINE_SYNC_GUIDE_AR.md)
💻 **Flutter Example**: [examples/flutter/offline_sync_service.dart](./examples/flutter/offline_sync_service.dart)

---

## 🔒 Security

### Authentication

**Dual JWT System:**
- **Admin Tokens**: 24-hour expiry for admin operations
- **Tenant Tokens**: 30-minute access token + 7-day refresh token

**Token Structure:**
```json
{
  "sub": "user_id",
  "tenant_id": "tenant_uuid",
  "role": "user",
  "exp": 1732300000,
  "iat": 1732298200
}
```

### Encryption

- **Password Hashing**: bcrypt with 12 rounds
- **Sensitive Data**: AES-256 encryption for Odoo credentials
- **Tokens**: HMAC-SHA256 for JWT signing

### Security Best Practices

1. **Change Default Credentials**: Immediately after installation
2. **Use HTTPS**: Always use SSL/TLS in production
3. **Rotate Secrets**: Regularly rotate JWT secrets
4. **Rate Limiting**: Enable per-tenant rate limits
5. **Audit Logs**: Monitor admin actions
6. **IP Whitelisting**: Restrict admin access by IP
7. **Database Backups**: Regular encrypted backups
8. **Security Updates**: Keep dependencies updated

### RBAC (Role-Based Access Control)

| Role | Admin Panel | Tenant API | Create Tenant | Suspend Tenant | View Logs |
|------|-------------|------------|---------------|----------------|-----------|
| **Super Admin** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Admin** | ✅ | ❌ | ✅ | ✅ | ✅ |
| **Support** | ✅ (Read) | ❌ | ❌ | ❌ | ✅ |
| **Tenant User** | ❌ | ✅ | ❌ | ❌ | ❌ (Own only) |

---

## ⚙️ Configuration

### Environment Variables

```env
# ============================================
# Application Settings
# ============================================
APP_NAME=BridgeCore
ENVIRONMENT=production  # development, staging, production
DEBUG=False
SECRET_KEY=your-secret-key-change-in-production-min-32-chars
HOST=0.0.0.0
PORT=8000
WORKERS=4

# ============================================
# Database Configuration
# ============================================
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/bridgecore_db
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# ============================================
# Redis Configuration
# ============================================
REDIS_URL=redis://redis:6379/0
CACHE_TTL=300
REDIS_MAX_CONNECTIONS=50

# ============================================
# JWT - Tenant Authentication
# ============================================
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ============================================
# JWT - Admin Authentication
# ============================================
ADMIN_SECRET_KEY=your-admin-secret-key-change-in-production-min-32-chars
ADMIN_TOKEN_EXPIRE_HOURS=24

# ============================================
# CORS Configuration
# ============================================
CORS_ORIGINS=http://localhost:3000,https://admin.bridgecore.com
CORS_ALLOW_CREDENTIALS=True
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_ALLOW_HEADERS=*

# ============================================
# Rate Limiting
# ============================================
RATE_LIMIT_ENABLED=True
DEFAULT_RATE_LIMIT_PER_HOUR=1000
DEFAULT_RATE_LIMIT_PER_DAY=10000

# ============================================
# Celery Configuration
# ============================================
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_ACCEPT_CONTENT=json
CELERY_TIMEZONE=UTC

# ============================================
# Monitoring (Optional)
# ============================================
SENTRY_DSN=
PROMETHEUS_ENABLED=True
PROMETHEUS_PORT=9090

# ============================================
# Logging
# ============================================
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=json  # json, text
LOG_FILE=/app/logs/bridgecore.log

# ============================================
# File Upload
# ============================================
MAX_UPLOAD_SIZE=10485760  # 10MB in bytes
ALLOWED_EXTENSIONS=pdf,jpg,jpeg,png,xlsx,csv

# ============================================
# Email (Optional)
# ============================================
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@bridgecore.com
```

---

## 🚀 Deployment

### Docker Compose (Production)

```yaml
version: '3.8'

services:
  # FastAPI Backend
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: bridgecore-api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:${DB_PASSWORD}@db:5432/bridgecore
      - REDIS_URL=redis://redis:6379/0
      - ENVIRONMENT=production
      - DEBUG=False
    depends_on:
      - db
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Admin Dashboard
  admin-dashboard:
    build:
      context: ./admin
      dockerfile: Dockerfile
    container_name: bridgecore-admin
    ports:
      - "3000:80"
    environment:
      - VITE_API_URL=https://api.bridgecore.com
    depends_on:
      - api
    restart: unless-stopped

  # Celery Worker
  celery-worker:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: bridgecore-celery-worker
    command: celery -A app.celery_app worker --loglevel=info --concurrency=4
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:${DB_PASSWORD}@db:5432/bridgecore
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    restart: unless-stopped

  # Celery Beat (Scheduler)
  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: bridgecore-celery-beat
    command: celery -A app.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:${DB_PASSWORD}@db:5432/bridgecore
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    restart: unless-stopped

  # PostgreSQL Database
  db:
    image: postgres:15-alpine
    container_name: bridgecore-db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=bridgecore
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: bridgecore-redis
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Prometheus (Monitoring)
  prometheus:
    image: prom/prometheus:latest
    container_name: bridgecore-prometheus
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    restart: unless-stopped

  # Grafana (Visualization)
  grafana:
    image: grafana/grafana:latest
    container_name: bridgecore-grafana
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  default:
    name: bridgecore-network
```

### Production Checklist

- [ ] **Security**
  - [ ] Change `SECRET_KEY`, `JWT_SECRET_KEY`, and `ADMIN_SECRET_KEY`
  - [ ] Set `ENVIRONMENT=production` and `DEBUG=False`
  - [ ] Configure proper `CORS_ORIGINS`
  - [ ] Set up SSL/TLS certificates (Let's Encrypt recommended)
  - [ ] Change default admin credentials
  - [ ] Enable firewall rules
  - [ ] Set up IP whitelisting for admin panel

- [ ] **Database**
  - [ ] Configure automated backups (daily recommended)
  - [ ] Set up replication for high availability
  - [ ] Optimize PostgreSQL configuration
  - [ ] Enable connection pooling

- [ ] **Monitoring**
  - [ ] Set up Prometheus/Grafana dashboards
  - [ ] Configure Sentry for error tracking
  - [ ] Set up log aggregation (ELK stack recommended)
  - [ ] Configure alerts for critical errors

- [ ] **Performance**
  - [ ] Enable Redis caching
  - [ ] Configure rate limiting
  - [ ] Set up CDN for static files
  - [ ] Optimize database indexes

- [ ] **Reliability**
  - [ ] Configure log rotation
  - [ ] Set up health checks
  - [ ] Configure automatic restarts
  - [ ] Set up load balancing (if needed)

---

## 📊 Monitoring

### Health Checks

```bash
# API Health
GET /health
# Response: {"status": "healthy", "timestamp": "2025-11-22T21:00:00Z"}

# Database Health
GET /health/db
# Response: {"status": "healthy", "latency_ms": 5}

# Redis Health
GET /health/redis
# Response: {"status": "healthy", "latency_ms": 2}

# Full System Health
GET /health/full
# Response: {
#   "api": "healthy",
#   "database": "healthy",
#   "redis": "healthy",
#   "celery": "healthy",
#   "timestamp": "2025-11-22T21:00:00Z"
# }
```

### Prometheus Metrics

```bash
GET /metrics
```

**Available Metrics:**

| Metric | Type | Description |
|--------|------|-------------|
| `bridgecore_requests_total` | Counter | Total API requests by tenant, endpoint, status |
| `bridgecore_request_duration_seconds` | Histogram | Request duration distribution |
| `bridgecore_active_tenants` | Gauge | Number of active tenants |
| `bridgecore_errors_total` | Counter | Total errors by type and severity |
| `bridgecore_cache_hits_total` | Counter | Redis cache hits |
| `bridgecore_cache_misses_total` | Counter | Redis cache misses |
| `bridgecore_db_connections` | Gauge | Active database connections |
| `bridgecore_celery_tasks_total` | Counter | Celery tasks by status |

### Background Tasks (Celery)

| Task | Schedule | Description |
|------|----------|-------------|
| `aggregate_hourly_stats` | Every hour at :05 | Aggregate usage logs to hourly statistics |
| `aggregate_daily_stats` | Daily at 00:30 | Aggregate hourly stats to daily |
| `cleanup_old_logs` | Daily at 02:00 | Delete logs older than 90 days |
| `generate_reports` | Weekly on Monday at 08:00 | Generate weekly reports |
| `retry_failed_webhooks` | Every 15 minutes | Retry failed webhook deliveries |

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run unit tests only
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v

# Run specific test file
pytest tests/unit/test_auth.py -v

# Run specific test
pytest tests/unit/test_auth.py::test_tenant_login -v

# Run with verbose output
pytest -v

# Run and stop on first failure
pytest -x
```

### Integration Tests with Real Odoo

Integration tests require a running Odoo instance. Set environment variables:

```bash
export ODOO_URL="https://demo.odoo.com"
export ODOO_DATABASE="demo"
export ODOO_USERNAME="admin"
export ODOO_PASSWORD="admin"

# Run integration tests
pytest tests/integration/odoo/test_odoo_integration.py -v

# Skip integration tests if Odoo not available
pytest tests/integration/odoo/test_odoo_integration.py -v -m "not integration"
```

**Integration Tests Coverage:**
- ✅ CRUD operations (create, read, update, delete)
- ✅ Search operations (search, search_read, search_count)
- ✅ Utility operations (fields_get, default_get, get_metadata)
- ✅ Advanced operations (onchange, read_group)
- ✅ Name operations (name_search, name_get)

### Test Structure

```
tests/
├── unit/                       # Unit tests
│   ├── odoo/                   # Odoo operations unit tests
│   │   ├── test_crud_ops.py
│   │   ├── test_search_ops.py
│   │   └── test_advanced_ops.py
│   ├── test_auth.py            # Authentication tests
│   ├── test_tenants.py         # Tenant management tests
│   └── test_rate_limiting.py   # Rate limiting tests
├── integration/                # Integration tests
│   └── odoo/                   # Odoo integration tests
│       └── test_odoo_integration.py
└── conftest.py                 # Pytest fixtures
```

---

## 📚 Documentation

### Documentation Structure

```
docs/
├── api/                        # API Documentation
│   ├── AUTHENTICATION_GUIDE.md
│   ├── ODOO_FIELDS_CHECK.md
│   ├── TENANT_ME_ENDPOINT.md
│   ├── TENANT_USERS_API.md
│   └── API_DOCUMENTATION.md
├── guides/                     # User Guides
│   ├── INTEGRATION_GUIDE.md
│   ├── QUICK_START.md
│   └── LOGIN_CREDENTIALS.md
├── setup/                      # Setup Documentation
│   ├── SETUP_AR.md
│   ├── ADMIN_DASHBOARD_SETUP.md
│   ├── DEPLOYMENT_GUIDE.md
│   └── ENVIRONMENT_VARIABLES.md
├── admin/                      # Admin Documentation
│   ├── ADMIN_ACCESS.md
│   └── ADMIN_USER_GUIDE.md
├── architecture/               # Architecture Documentation
│   ├── SMART_SYNC_IMPLEMENTATION.md
│   ├── SYNC_ARCHITECTURE.md
│   ├── WEBHOOK_INTEGRATION_ARCHITECTURE.md
│   └── WEBHOOK_INTEGRATION_README.md
├── security/                   # Security Documentation
│   ├── SECURITY_UNIQUE_ODOO_USER.md
│   └── TENANT_USER_MANAGEMENT_FIX.md
└── examples/                   # Examples
    └── FLUTTER_SDK_IMPROVEMENTS.md
```

### Key Documentation Files

- **[AUTHENTICATION_GUIDE.md](./docs/api/AUTHENTICATION_GUIDE.md)**: Complete authentication guide
- **[TENANT_ME_ENDPOINT.md](./docs/api/TENANT_ME_ENDPOINT.md)**: Enhanced /me endpoint documentation
- **[QUICK_START.md](./docs/guides/QUICK_START.md)**: Quick start guide
- **[INTEGRATION_GUIDE.md](./docs/guides/INTEGRATION_GUIDE.md)**: Integration guide for Flutter/React
- **[DEPLOYMENT_GUIDE.md](./docs/setup/DEPLOYMENT_GUIDE.md)**: Production deployment guide

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### Development Setup

#### Quick Setup (Recommended)

```bash
# 1. Fork and clone
git clone https://github.com/yourusername/BridgeCore.git
cd BridgeCore

# 2. Run automated installation
bash scripts/install_dependencies.sh

# 3. Setup environment
cp env.example .env
# Edit .env with your configuration

# 4. Run database migrations
alembic upgrade head

# 5. Seed initial data
python scripts/seed_admin.py

# 6. Setup pre-commit hooks
pre-commit install

# 7. Create feature branch
git checkout -b feature/amazing-feature

# 8. Make changes and test
pytest

# 9. Commit and push
git commit -m 'Add amazing feature'
git push origin feature/amazing-feature

# 10. Open Pull Request
```

#### Manual Setup

```bash
# 1. Fork and clone
git clone https://github.com/yourusername/BridgeCore.git
cd BridgeCore

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Setup pre-commit hooks
pre-commit install

# 5. Create feature branch
git checkout -b feature/amazing-feature

# 6. Make changes and test
pytest

# 7. Commit and push
git commit -m 'Add amazing feature'
git push origin feature/amazing-feature

# 8. Open Pull Request
```

### Development Guidelines

- **Code Style**: Follow PEP 8 for Python, ESLint for TypeScript
- **Type Hints**: Use type hints for all Python functions
- **Documentation**: Update docs for new features
- **Tests**: Write tests for new features (aim for 80%+ coverage)
- **Commits**: Use conventional commits (feat:, fix:, docs:, etc.)
- **PR Description**: Clearly describe changes and motivation

### Code Review Process

1. All PRs require at least one approval
2. All tests must pass
3. Code coverage must not decrease
4. Documentation must be updated
5. No merge conflicts

---

## 💬 Support

### Getting Help

- **📖 Documentation**: Check [docs/](./docs/) folder
- **🐛 Bug Reports**: [GitHub Issues](https://github.com/geniustep/BridgeCore/issues)
- **💡 Feature Requests**: [GitHub Discussions](https://github.com/geniustep/BridgeCore/discussions)
- **📧 Email**: support@bridgecore.com
- **💬 Discord**: [Join our community](https://discord.gg/bridgecore)

### Reporting Bugs

When reporting bugs, please include:
- BridgeCore version
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages/logs

### Feature Requests

When requesting features, please include:
- Use case description
- Expected behavior
- Why this feature is important
- Proposed implementation (optional)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 BridgeCore Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🗺️ Roadmap

### ✅ Completed

- [x] Multi-tenant architecture with complete isolation
- [x] Admin panel with React dashboard
- [x] Per-tenant rate limiting with Redis
- [x] **26 Complete Odoo API Operations** (CRUD, Search, Advanced, Name, View, Web, Permission, Utility, Custom)
- [x] **Intelligent Rate Limiting** per operation type
- [x] **Integration Tests** with real Odoo instances
- [x] **Automated Installation Script** for easy setup
- [x] Usage tracking and analytics
- [x] Error logging with resolution workflow
- [x] Background tasks with Celery
- [x] Webhook system for real-time sync
- [x] Smart sync for mobile apps
- [x] Enhanced /me endpoint with Odoo data
- [x] Tenant user management with Odoo linking
- [x] Automatic Odoo version detection
- [x] Comprehensive documentation

### 🚧 In Progress

- [ ] Advanced reporting and exports
- [ ] Multi-language admin panel (i18n)
- [ ] Tenant-specific customizations
- [ ] Advanced analytics dashboards

### 📅 Planned

- [ ] SAP integration
- [ ] Salesforce integration
- [ ] Microsoft Dynamics integration
- [ ] Kubernetes deployment configs
- [ ] GraphQL API
- [ ] WebSocket support for real-time updates
- [ ] Mobile admin app (Flutter)
- [ ] Plugin system for custom integrations
- [ ] AI-powered analytics and insights
- [ ] Multi-region deployment support

---

## 🌟 Acknowledgments

- **FastAPI**: For the amazing async web framework
- **React**: For the powerful UI library
- **Ant Design**: For beautiful UI components
- **PostgreSQL**: For reliable data storage
- **Redis**: For fast caching
- **Odoo**: For the ERP/CRM platform
- **Contributors**: Thank you to all contributors!

---

<div align="center">

**Made with ❤️ by the BridgeCore Team**

[⭐ Star on GitHub](https://github.com/geniustep/BridgeCore) | [📖 Documentation](./docs/) | [🐛 Report Bug](https://github.com/geniustep/BridgeCore/issues) | [💡 Request Feature](https://github.com/geniustep/BridgeCore/discussions)

**BridgeCore** - Bridging the gap between mobile apps and enterprise systems

</div>
