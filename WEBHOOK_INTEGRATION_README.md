# 🎉 BridgeCore Webhook Integration - Complete Guide

## 📋 Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [API Endpoints](#api-endpoints)
7. [Usage Examples](#usage-examples)
8. [Monitoring](#monitoring)
9. [Troubleshooting](#troubleshooting)
10. [Migration Guide](#migration-guide)

---

## 🎯 Overview

The BridgeCore Webhook Integration provides a comprehensive, real-time change tracking system for Odoo ERP. It combines the functionality of odoo-webhook-corp with advanced features for enterprise-grade monitoring and synchronization.

### Key Capabilities

- ✅ **Real-time Change Detection**: Track all changes in Odoo instantly
- ✅ **Smart Multi-User Sync**: Efficient synchronization for multiple devices/users
- ✅ **Universal Model Discovery**: Automatically discover and monitor all Odoo models
- ✅ **PostgreSQL Triggers**: Database-level change detection
- ✅ **GraphQL API**: Flexible querying with modern GraphQL
- ✅ **WebSocket Support**: Real-time push notifications
- ✅ **Enterprise Monitoring**: Prometheus metrics + Grafana dashboards
- ✅ **Rate Limiting**: Protection against abuse
- ✅ **Multi-tenancy Ready**: Support for multiple Odoo instances

---

## ⭐ Features

### 1. REST API (v1 & v2)

#### v1 Endpoints - Basic Webhook Operations
- `GET /api/v1/webhooks/events` - List webhook events
- `GET /api/v1/webhooks/check-updates` - Check for updates
- `DELETE /api/v1/webhooks/cleanup` - Cleanup old events

#### v2 Endpoints - Smart Sync
- `POST /api/v2/sync/pull` - Smart sync pull (only new changes)
- `GET /api/v2/sync/state` - Get sync state
- `POST /api/v2/sync/reset` - Reset sync state

### 2. GraphQL API

```graphql
query {
  webhookEvents(filter: {model: "sale.order"}, limit: 100) {
    id
    model
    recordId
    event
    timestamp
  }
}
```

### 3. Universal Audit System

- Auto-discovery of all Odoo models
- Classification by importance (critical/important/standard)
- Adaptive monitoring strategies
- PostgreSQL triggers for real-time detection

### 4. Monitoring & Observability

- Prometheus metrics
- Grafana dashboards
- Alert rules for critical issues
- Performance tracking

---

## 🏗️ Architecture

```
Flutter Apps → BridgeCore → Odoo ERP
                    ↓
            PostgreSQL Triggers
                    ↓
            Webhook Events Table
                    ↓
        Redis Cache + Celery Queue
                    ↓
        WebSocket + GraphQL + REST
```

For detailed architecture, see [WEBHOOK_INTEGRATION_ARCHITECTURE.md](./WEBHOOK_INTEGRATION_ARCHITECTURE.md)

---

## 📦 Installation

### 1. Prerequisites

```bash
# System requirements
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (recommended)
```

### 2. Install Dependencies

```bash
cd /path/to/BridgeCore
pip install -r requirements.txt
```

New dependencies added:
- `strawberry-graphql[fastapi]` - GraphQL support
- `aiodataloader` - DataLoader pattern
- `python-socketio` - Enhanced WebSocket
- `aio-pika` - AMQP async support

### 3. Setup PostgreSQL Triggers

```bash
# Connect to your Odoo PostgreSQL database
psql -U odoo_user -d odoo_database -f scripts/setup_triggers.sql
```

This will:
- Create trigger functions
- Apply triggers to critical tables
- Setup notification channels
- Create management functions

### 4. Install Odoo Module

Install the `custom-model-webhook` module in your Odoo instance:

```bash
# Copy module to Odoo addons
cp -r /path/to/odoo-webhook-corp/custom-model-webhook /path/to/odoo/addons/

# Update apps list in Odoo
# Install "Auto Webhook Flutter" module
```

---

## ⚙️ Configuration

### Environment Variables

Add to `.env`:

```env
# Odoo Configuration
ODOO_URL=https://odoo.geniura.com
ODOO_DB=your_database

# Redis
REDIS_URL=redis://localhost:6379/0

# PostgreSQL
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/bridgecore

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=100

# Monitoring
SENTRY_DSN=your_sentry_dsn  # Optional
```

### BridgeCore Configuration

The webhook module is automatically loaded in `main.py`:

```python
from app.modules.webhook import router as webhook_router_v1
from app.modules.webhook import router_v2 as webhook_router_v2

app.include_router(webhook_router_v1.router)  # /api/v1/webhooks/*
app.include_router(webhook_router_v2.router)  # /api/v2/sync/*
```

---

## 🚀 API Endpoints

### Authentication

All endpoints require JWT authentication:

```bash
# Login to get token
POST /auth/login
{
  "username": "your_username",
  "password": "your_password"
}

# Use token in subsequent requests
Authorization: Bearer <your_token>
```

### v1 API Examples

#### 1. List Webhook Events

```bash
GET /api/v1/webhooks/events?model=sale.order&limit=100

Response:
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

#### 2. Check for Updates

```bash
GET /api/v1/webhooks/check-updates?since=2025-11-16T00:00:00Z

Response:
{
  "has_update": true,
  "last_update_at": "2025-11-16T10:30:00Z",
  "summary": [
    {"model": "sale.order", "count": 15},
    {"model": "res.partner", "count": 8}
  ]
}
```

### v2 Smart Sync API

#### Smart Sync Pull

```bash
POST /api/v2/sync/pull
{
  "user_id": 1,
  "device_id": "device_123",
  "app_type": "sales_app",
  "limit": 100
}

Response:
{
  "status": "success",
  "has_updates": true,
  "new_events_count": 25,
  "events": [...],
  "next_sync_token": "1234",
  "last_sync_time": "2025-11-16T10:30:00Z"
}
```

#### Get Sync State

```bash
GET /api/v2/sync/state?user_id=1&device_id=device_123

Response:
{
  "user_id": 1,
  "device_id": "device_123",
  "last_event_id": 1234,
  "last_sync_time": "2025-11-16T10:30:00Z",
  "sync_count": 42,
  "is_active": true
}
```

### GraphQL API

```bash
POST /graphql
{
  "query": "query { webhookEvents(filter: {model: \"sale.order\"}) { id model recordId event timestamp } }"
}
```

---

## 💡 Usage Examples

### Flutter Integration

```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

class WebhookService {
  final String baseUrl = 'https://bridgecore.geniura.com';
  final String token;

  WebhookService(this.token);

  Future<List<WebhookEvent>> syncPull({
    required int userId,
    required String deviceId,
    required String appType,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/v2/sync/pull'),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'user_id': userId,
        'device_id': deviceId,
        'app_type': appType,
        'limit': 100,
      }),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return (data['events'] as List)
          .map((e) => WebhookEvent.fromJson(e))
          .toList();
    }

    throw Exception('Failed to sync');
  }
}
```

### Python Client

```python
import httpx

class BridgeCoreWebhookClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.token = token
        self.headers = {"Authorization": f"Bearer {token}"}

    async def get_events(
        self,
        model: str = None,
        limit: int = 100
    ):
        params = {"limit": limit}
        if model:
            params["model_name"] = model

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/webhooks/events",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return response.json()

    async def smart_sync(
        self,
        user_id: int,
        device_id: str,
        app_type: str
    ):
        payload = {
            "user_id": user_id,
            "device_id": device_id,
            "app_type": app_type,
            "limit": 100
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v2/sync/pull",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
```

---

## 📊 Monitoring

### Prometheus Metrics

Key metrics exposed at `/metrics`:

- `webhook_received_total` - Total webhooks received
- `webhook_processing_seconds` - Processing time histogram
- `websocket_connections_active` - Active WebSocket connections
- `webhook_queue_size` - Current queue size
- `webhook_errors_total` - Total errors

### Grafana Dashboard

Import the dashboard from `monitoring/grafana/dashboards/webhook_dashboard.json`:

1. Open Grafana
2. Go to Dashboards → Import
3. Upload `webhook_dashboard.json`
4. Select Prometheus data source
5. Click Import

### Alert Rules

Prometheus alerts are configured in `monitoring/prometheus/rules/webhook_alerts.yml`:

- High error rate (> 5%)
- Slow processing (> 1s p95)
- Large queue backlog (> 1000)
- Database connection failures
- High memory usage

---

## 🔧 Troubleshooting

### Common Issues

#### 1. No Events Received

**Problem**: Webhook events are not being recorded

**Solutions**:
- Check if Odoo module is installed
- Verify PostgreSQL triggers are created: `SELECT * FROM list_bridgecore_triggers();`
- Check Odoo logs for errors
- Test notification: `SELECT test_bridgecore_notification();`

#### 2. High Latency

**Problem**: Slow webhook processing

**Solutions**:
- Check Redis connection
- Verify database indexes exist
- Monitor queue size
- Check Prometheus metrics for bottlenecks

#### 3. Sync Issues

**Problem**: Smart sync not working

**Solutions**:
- Reset sync state: `POST /api/v2/sync/reset`
- Check `user.sync.state` model in Odoo
- Verify user_id and device_id are correct

### Debug Commands

```bash
# Check PostgreSQL triggers
psql -d odoo_db -c "SELECT * FROM list_bridgecore_triggers();"

# Test notification system
psql -d odoo_db -c "SELECT test_bridgecore_notification();"

# Check webhook queue
redis-cli LLEN webhook_queue

# View recent errors
tail -f logs/app.log | grep ERROR
```

---

## 🔄 Migration Guide

### Migrating from odoo-webhook-corp

#### 1. Update API Endpoints

| Old Endpoint | New Endpoint |
|-------------|-------------|
| `http://webhook-server:8000/api/v1/webhook/events` | `http://bridgecore:8000/api/v1/webhooks/events` |
| `http://webhook-server:8000/api/v2/sync/pull` | `http://bridgecore:8000/api/v2/sync/pull` |

#### 2. Update Authentication

Replace session-based auth with JWT:

```python
# Old (session_id)
headers = {"Cookie": f"session_id={session_id}"}

# New (JWT token)
headers = {"Authorization": f"Bearer {jwt_token}"}
```

#### 3. No Changes to Odoo Module

The `custom-model-webhook` module works as-is. No changes needed.

#### 4. New Features Available

- GraphQL API at `/graphql`
- WebSocket notifications
- Enhanced monitoring
- Better error handling
- Rate limiting

---

## 📚 Additional Resources

- [Architecture Documentation](./WEBHOOK_INTEGRATION_ARCHITECTURE.md)
- [Main BridgeCore Documentation](./DOCUMENTATION.md)
- [API Reference](./docs/api/)
- [odoo-webhook-corp Repository](https://github.com/geniustep/odoo-webhook-corp)

---

## 🤝 Support

For issues and questions:
- GitHub Issues: [BridgeCore Issues](https://github.com/geniustep/BridgeCore/issues)
- Email: support@geniura.com

---

**Status**: ✅ Integration Complete
**Version**: 1.0.0
**Last Updated**: 2025-11-16
