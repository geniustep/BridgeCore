# 🏗️ BridgeCore Webhook Integration Architecture

## 📊 Executive Summary

This document outlines the complete integration of the odoo-webhook-corp system into BridgeCore, implementing a comprehensive Hybrid Smart Detection system for real-time change tracking from Odoo ERP.

### Integration Goals
- ✅ Merge odoo-webhook-server functionality into BridgeCore
- ✅ Implement Hybrid Smart Detection for universal Odoo change tracking
- ✅ Add advanced features: GraphQL, enhanced WebSocket, monitoring
- ✅ Maintain backward compatibility with existing BridgeCore features

---

## 🎯 Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Flutter Apps                             │
│              (gmobile, delivery_app, sales_app, etc.)           │
└────────────┬────────────────────────────────────┬────────────────┘
             │                                     │
             │ REST/GraphQL/WebSocket              │
             ▼                                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                        BridgeCore (Enhanced)                     │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   REST API   │  │   GraphQL    │  │  WebSocket   │          │
│  │   (v1, v2)   │  │   API        │  │  Real-time   │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                   │
│  ┌──────┴──────────────────┴──────────────────┴───────┐         │
│  │           Webhook Module (NEW)                      │         │
│  │  - Event Handling     - Smart Sync                  │         │
│  │  - Update Tracking    - Multi-User State            │         │
│  └─────────────────────────────────────────────────────┘         │
│                                                                   │
│  ┌─────────────────────────────────────────────────────┐         │
│  │     Universal Audit/Detection Module (NEW)          │         │
│  │  - Auto-discovery   - PostgreSQL Triggers            │         │
│  │  - Model Classification  - ORM Interception         │         │
│  │  - Change Streaming      - Log Analysis             │         │
│  └─────────────────────────────────────────────────────┘         │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Caching    │  │    Queue     │  │  Monitoring  │          │
│  │   (Redis)    │  │   (Celery)   │  │ (Prometheus) │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────┬───────────────────────────────────────────────────┘
              │
              │ Odoo API / PostgreSQL Triggers
              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Odoo ERP System                             │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐            │
│  │  custom-model-webhook Module (Installed)        │            │
│  │  - update.webhook model                          │            │
│  │  - webhook.mixin                                 │            │
│  │  - user.sync.state (for multi-user tracking)    │            │
│  └─────────────────────────────────────────────────┘            │
│                                                                   │
│  ┌─────────────────────────────────────────────────┐            │
│  │  PostgreSQL Database                             │            │
│  │  - Business Models (sale.order, res.partner...)  │            │
│  │  - Webhook Events Table (update_webhook)         │            │
│  │  - Database Triggers (for universal tracking)    │            │
│  └─────────────────────────────────────────────────┘            │
└───────────────────────────────────────────────────────────────────┘
```

---

## 📦 Module Structure

### New Directory Structure

```
BridgeCore/
├── app/
│   ├── modules/
│   │   ├── webhook/                    # NEW - Core webhook functionality
│   │   │   ├── __init__.py
│   │   │   ├── service.py             # Business logic
│   │   │   ├── router.py              # REST endpoints (v1)
│   │   │   ├── router_v2.py           # REST endpoints (v2 - smart sync)
│   │   │   ├── graphql_schema.py      # GraphQL types and resolvers
│   │   │   ├── websocket_handler.py   # WebSocket event broadcasting
│   │   │   ├── models.py              # SQLAlchemy models
│   │   │   ├── schemas.py             # Pydantic schemas
│   │   │   └── repository.py          # Data access layer
│   │   │
│   │   └── universal_audit/            # NEW - Universal detection
│   │       ├── __init__.py
│   │       ├── detector.py            # Main detector class
│   │       ├── auto_discovery.py      # Model auto-discovery
│   │       ├── classifier.py          # Model classification
│   │       ├── strategies/
│   │       │   ├── __init__.py
│   │       │   ├── audit_trail.py     # Odoo-level monitoring
│   │       │   ├── database_trigger.py # PostgreSQL triggers
│   │       │   ├── orm_interceptor.py  # ORM method interception
│   │       │   └── polling.py         # Intelligent polling
│   │       └── monitor.py             # Background monitoring service
│   │
│   ├── graphql/                        # NEW - GraphQL support
│   │   ├── __init__.py
│   │   ├── schema.py                  # Main schema
│   │   ├── context.py                 # GraphQL context
│   │   └── dataloaders.py             # DataLoader instances
│   │
│   ├── middleware/
│   │   ├── rate_limit.py              # ENHANCED - Advanced rate limiting
│   │   ├── versioning.py              # NEW - API versioning
│   │   └── tenant.py                  # ENHANCED - Multi-tenancy
│   │
│   └── utils/
│       ├── odoo_client.py             # NEW - Migrated from odoo-webhook-corp
│       └── webhook_helpers.py         # NEW - Webhook utilities
│
├── scripts/
│   ├── setup_triggers.sql             # NEW - PostgreSQL triggers
│   ├── init_webhook_tables.sql        # NEW - Database schema
│   └── migrate_webhook_data.py        # NEW - Data migration script
│
├── monitoring/
│   ├── grafana/
│   │   └── dashboards/
│   │       └── webhook_dashboard.json # NEW - Webhook monitoring
│   └── prometheus/
│       └── rules/
│           └── webhook_alerts.yml     # NEW - Alert rules
│
└── tests/
    ├── integration/
    │   ├── test_webhook_integration.py
    │   └── test_graphql_api.py
    └── unit/
        ├── test_webhook_service.py
        └── test_universal_audit.py
```

---

## 🔄 Data Flow

### 1. Change Detection Flow

```
Odoo Model Change (create/write/unlink)
         │
         ├─→ webhook.mixin intercepts
         │        │
         │        ▼
         │   Creates update.webhook record
         │        │
         │        ▼
         │   PostgreSQL Trigger fires
         │        │
         └────────┴─→ Sends to BridgeCore
                       │
                       ▼
                BridgeCore Webhook Module
                       │
                       ├─→ Stores in local cache (Redis)
                       ├─→ Broadcasts via WebSocket
                       ├─→ Publishes to queue (Celery)
                       └─→ Updates metrics (Prometheus)
                       │
                       ▼
                Flutter Apps receive real-time updates
```

### 2. Smart Sync Flow (Multi-User)

```
User opens app
     │
     ▼
Sends sync request with:
  - user_id
  - device_id
  - app_type
  - last_sync_token
     │
     ▼
BridgeCore checks user.sync.state
     │
     ├─→ Gets last_event_id for this user/device
     ├─→ Queries events > last_event_id
     ├─→ Filters by app_type (sales_app, delivery_app, etc.)
     └─→ Returns only relevant changes
     │
     ▼
Updates user.sync.state:
  - new last_event_id
  - last_sync_time
  - sync_count++
     │
     ▼
App receives only new changes since last sync
```

---

## 🛠️ Implementation Details

### Phase 1: Core Integration (Week 1-2)

#### 1.1 Dependencies
```python
# requirements.txt additions
strawberry-graphql==0.218.0  # GraphQL
strawberry-graphql[fastapi]
aiodataloader==0.2.1         # DataLoader pattern
```

#### 1.2 Webhook Module

**app/modules/webhook/service.py**
```python
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.utils.odoo_client import OdooClient
from app.core.cache_service import CacheService
from app.modules.webhook.models import WebhookEvent
from app.modules.webhook.schemas import (
    WebhookEventOut,
    SyncRequest,
    SyncResponse
)

class WebhookService:
    """Core webhook business logic"""

    def __init__(
        self,
        odoo_client: OdooClient,
        cache: CacheService
    ):
        self.odoo = odoo_client
        self.cache = cache

    async def get_events(
        self,
        model_name: Optional[str] = None,
        record_id: Optional[int] = None,
        event: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[WebhookEventOut]:
        """Get webhook events with filtering and caching"""

        # Build cache key
        cache_key = f"webhook:events:{model_name}:{record_id}:{event}:{since}:{limit}:{offset}"

        # Try cache first
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        # Build domain
        domain = []
        if model_name:
            domain.append(["model", "=", model_name])
        if record_id is not None:
            domain.append(["record_id", "=", record_id])
        if event:
            domain.append(["event", "=", event])
        if since:
            domain.append(["timestamp", ">=", since.isoformat()])

        # Fetch from Odoo
        rows = self.odoo.search_read(
            "update.webhook",
            domain=domain,
            fields=["id", "model", "record_id", "event", "timestamp"],
            limit=limit,
            offset=offset,
            order="timestamp desc"
        )

        # Transform to Pydantic models
        events = [
            WebhookEventOut(
                id=r["id"],
                model=r.get("model", ""),
                record_id=r.get("record_id", 0),
                event=r.get("event", "manual"),
                occurred_at=r.get("timestamp", "")
            )
            for r in rows
        ]

        # Cache for 60 seconds
        await self.cache.set(cache_key, events, ttl=60)

        return events

    async def smart_sync(
        self,
        sync_request: SyncRequest
    ) -> SyncResponse:
        """Smart sync for multi-user apps"""

        # Get or create sync state
        sync_state = self.odoo.call_kw(
            "user.sync.state",
            "get_or_create_state",
            [
                sync_request.user_id,
                sync_request.device_id,
                sync_request.app_type
            ]
        )

        last_event_id = sync_state.get("last_event_id", 0)

        # Build domain
        domain = [
            ("id", ">", last_event_id),
            ("is_archived", "=", False)
        ]

        # Filter by app type
        app_models = self._get_app_models(sync_request.app_type)
        if app_models:
            domain.append(("model", "in", app_models))

        # Fetch events
        events = self.odoo.search_read(
            "update.webhook",
            domain=domain,
            fields=["id", "model", "record_id", "event", "timestamp"],
            limit=sync_request.limit,
            order="id asc"
        )

        if not events:
            return SyncResponse(
                has_updates=False,
                new_events_count=0,
                events=[],
                next_sync_token=str(last_event_id),
                last_sync_time=sync_state.get("last_sync_time", "")
            )

        # Update sync state
        new_last_event_id = events[-1]["id"]
        self.odoo.call_kw(
            "user.sync.state",
            "write",
            [[sync_state["id"]], {
                "last_event_id": new_last_event_id,
                "last_sync_time": datetime.utcnow().isoformat(),
                "sync_count": sync_state.get("sync_count", 0) + 1
            }]
        )

        return SyncResponse(
            has_updates=True,
            new_events_count=len(events),
            events=events,
            next_sync_token=str(new_last_event_id),
            last_sync_time=sync_state.get("last_sync_time", "")
        )
```

#### 1.3 GraphQL Schema

**app/graphql/schema.py**
```python
import strawberry
from typing import List, Optional
from datetime import datetime
from app.modules.webhook.service import WebhookService

@strawberry.type
class WebhookEvent:
    id: int
    model: str
    record_id: int
    event: str
    timestamp: datetime

@strawberry.type
class Query:
    @strawberry.field
    async def webhook_events(
        self,
        model: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[WebhookEvent]:
        """Query webhook events"""
        service = WebhookService(...)  # Inject dependencies
        events = await service.get_events(
            model_name=model,
            since=since,
            limit=limit
        )
        return events

@strawberry.type
class Subscription:
    @strawberry.subscription
    async def webhook_event_stream(
        self,
        models: Optional[List[str]] = None
    ) -> WebhookEvent:
        """Real-time webhook event stream"""
        # WebSocket subscription implementation
        async for event in event_stream:
            if models is None or event.model in models:
                yield event

schema = strawberry.Schema(query=Query, subscription=Subscription)
```

### Phase 2: Universal Audit System (Week 3-4)

#### 2.1 Auto-Discovery

**app/modules/universal_audit/auto_discovery.py**
```python
from typing import List, Dict, Any
from app.utils.odoo_client import OdooClient

class ModelDiscovery:
    """Auto-discover all Odoo models"""

    def __init__(self, odoo_client: OdooClient):
        self.odoo = odoo_client

    async def discover_all_models(self) -> List[Dict[str, Any]]:
        """Discover all models from multiple sources"""

        models = {}

        # 1. From Odoo API (ir.model)
        odoo_models = self.odoo.search_read(
            "ir.model",
            domain=[],
            fields=["id", "model", "name", "transient", "field_id"]
        )

        for model in odoo_models:
            models[model["model"]] = {
                "name": model["model"],
                "display_name": model["name"],
                "is_transient": model.get("transient", False),
                "field_count": len(model.get("field_id", [])),
                "source": "ir.model"
            }

        # 2. From Database (information_schema)
        # This would require direct PostgreSQL access
        # Implemented in database_trigger strategy

        return list(models.values())

    async def classify_models(
        self,
        models: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """Classify models by importance/priority"""

        classification = {
            "critical": [],      # High-priority, real-time tracking
            "important": [],     # Medium-priority, frequent polling
            "standard": [],      # Low-priority, periodic polling
            "transient": []      # Temporary models, no tracking
        }

        critical_patterns = [
            "sale.order",
            "purchase.order",
            "account.move",
            "stock.picking",
            "res.partner"
        ]

        for model in models:
            name = model["name"]

            if model.get("is_transient"):
                classification["transient"].append(name)
            elif name in critical_patterns:
                classification["critical"].append(name)
            elif name.startswith(("sale.", "purchase.", "stock.")):
                classification["important"].append(name)
            else:
                classification["standard"].append(name)

        return classification
```

#### 2.2 PostgreSQL Triggers

**scripts/setup_triggers.sql**
```sql
-- Universal trigger function for all tables
CREATE OR REPLACE FUNCTION notify_bridgecore_changes()
RETURNS TRIGGER AS $$
DECLARE
    payload JSON;
    channel TEXT;
    table_priority TEXT;
BEGIN
    -- Determine priority based on table name
    IF TG_TABLE_NAME IN ('sale_order', 'account_move', 'stock_picking', 'res_partner') THEN
        table_priority := 'high';
        channel := 'bridgecore_changes_high';
    ELSIF TG_TABLE_NAME LIKE 'sale_%' OR TG_TABLE_NAME LIKE 'stock_%' THEN
        table_priority := 'medium';
        channel := 'bridgecore_changes_medium';
    ELSE
        table_priority := 'low';
        channel := 'bridgecore_changes_low';
    END IF;

    -- Build payload with complete information
    payload := json_build_object(
        'operation', TG_OP,
        'table', TG_TABLE_NAME,
        'schema', TG_TABLE_SCHEMA,
        'priority', table_priority,
        'timestamp', CURRENT_TIMESTAMP,
        'user', current_user,
        'old_data', CASE WHEN TG_OP = 'DELETE' OR TG_OP = 'UPDATE'
                        THEN row_to_json(OLD)
                        ELSE NULL END,
        'new_data', CASE WHEN TG_OP = 'INSERT' OR TG_OP = 'UPDATE'
                        THEN row_to_json(NEW)
                        ELSE NULL END,
        'changed_fields', CASE WHEN TG_OP = 'UPDATE'
                              THEN (
                                  SELECT json_object_agg(key, value)
                                  FROM json_each(row_to_json(NEW))
                                  WHERE value IS DISTINCT FROM (row_to_json(OLD) ->> key)::json
                              )
                              ELSE NULL END
    );

    -- Send notification
    PERFORM pg_notify(channel, payload::text);

    -- Return appropriate value
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to critical tables
DO $$
DECLARE
    t TEXT;
    critical_tables TEXT[] := ARRAY[
        'sale_order', 'sale_order_line',
        'purchase_order', 'purchase_order_line',
        'account_move', 'account_move_line',
        'stock_picking', 'stock_move',
        'res_partner', 'res_users',
        'product_product', 'product_template'
    ];
BEGIN
    FOREACH t IN ARRAY critical_tables
    LOOP
        -- Check if table exists
        IF EXISTS (SELECT 1 FROM information_schema.tables
                   WHERE table_name = t AND table_schema = 'public') THEN

            -- Drop existing trigger if exists
            EXECUTE format('DROP TRIGGER IF EXISTS bridgecore_audit_trigger ON %I', t);

            -- Create new trigger
            EXECUTE format('
                CREATE TRIGGER bridgecore_audit_trigger
                AFTER INSERT OR UPDATE OR DELETE ON %I
                FOR EACH ROW
                EXECUTE FUNCTION notify_bridgecore_changes()
            ', t);

            RAISE NOTICE 'Created trigger for table: %', t;
        END IF;
    END LOOP;
END $$;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_update_webhook_timestamp
    ON update_webhook(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_update_webhook_model_timestamp
    ON update_webhook(model, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_update_webhook_model_record
    ON update_webhook(model, record_id);
```

---

## 🔐 Security & Performance

### Rate Limiting Strategy

```python
# app/middleware/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address
from redis import Redis

# Different limits for different user tiers
RATE_LIMITS = {
    'free': {
        'webhook_events': '100/hour',
        'sync_pull': '50/hour',
        'graphql': '200/hour'
    },
    'premium': {
        'webhook_events': '1000/hour',
        'sync_pull': '500/hour',
        'graphql': '2000/hour'
    },
    'enterprise': {
        'webhook_events': '10000/hour',
        'sync_pull': '5000/hour',
        'graphql': '20000/hour'
    }
}

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379/0",
    strategy="moving-window"
)
```

### Caching Strategy

```python
# Multi-level caching
1. Redis L1 Cache (TTL: 60s) - Hot data
2. Redis L2 Cache (TTL: 300s) - Warm data
3. Database - Cold data

# Cache invalidation on webhook events
- Invalidate specific model caches
- Broadcast cache invalidation via Redis pub/sub
- Version-based cache keys
```

---

## 📊 Monitoring & Observability

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

# Webhook metrics
webhook_received_total = Counter(
    'webhook_received_total',
    'Total webhooks received',
    ['model', 'operation']
)

webhook_processing_seconds = Histogram(
    'webhook_processing_seconds',
    'Webhook processing time',
    ['model']
)

active_websocket_connections = Gauge(
    'websocket_connections_active',
    'Active WebSocket connections'
)

webhook_queue_size = Gauge(
    'webhook_queue_size',
    'Current webhook queue size'
)
```

### Grafana Dashboard Panels

1. **Webhook Activity**
   - Events per second (by model)
   - Processing latency (p50, p95, p99)
   - Error rate

2. **Sync Performance**
   - Sync requests per minute
   - Average sync duration
   - Data transferred per sync

3. **System Health**
   - Database connection pool
   - Redis memory usage
   - Queue depth
   - WebSocket connections

---

## 🧪 Testing Strategy

### Integration Tests

```python
# tests/integration/test_webhook_integration.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_webhook_event_flow():
    """Test complete webhook event flow"""

    # 1. Create event in Odoo
    # 2. Verify webhook recorded in update.webhook
    # 3. Query via BridgeCore API
    # 4. Verify WebSocket broadcast
    # 5. Test GraphQL query
    pass

@pytest.mark.asyncio
async def test_smart_sync_multi_user():
    """Test smart sync with multiple users"""

    # 1. Create events
    # 2. User A syncs - gets events
    # 3. User B syncs - gets same events
    # 4. New event created
    # 5. User A syncs - gets only new event
    # 6. User B syncs - gets only new event
    pass
```

---

## 📅 Implementation Timeline

### Week 1-2: Core Integration
- [x] Project analysis
- [ ] Migrate webhook module
- [ ] Setup database schemas
- [ ] Implement REST endpoints (v1, v2)
- [ ] Basic testing

### Week 3-4: Universal Audit
- [ ] Auto-discovery implementation
- [ ] PostgreSQL triggers
- [ ] Model classification
- [ ] Background monitoring service

### Week 5-6: Advanced Features
- [ ] GraphQL API
- [ ] Enhanced WebSocket
- [ ] Grafana dashboards
- [ ] Comprehensive testing
- [ ] Documentation

---

## 🎓 Migration Guide

### For Existing odoo-webhook-corp Users

1. **Update Odoo Module**: No changes needed - custom-model-webhook continues to work
2. **Update API Endpoints**: Change base URL from odoo-webhook-server to BridgeCore
3. **Update Authentication**: Use BridgeCore JWT tokens instead of session_id
4. **New Features**: Access GraphQL API, real-time WebSocket, enhanced monitoring

### API Endpoint Migration

```
OLD: http://webhook-server:8000/api/v1/webhook/events
NEW: http://bridgecore:8000/api/v1/webhooks/events

OLD: http://webhook-server:8000/api/v2/sync/pull
NEW: http://bridgecore:8000/api/v2/sync/pull

NEW: http://bridgecore:8000/graphql  (GraphQL endpoint)
NEW: ws://bridgecore:8000/ws/webhooks  (WebSocket)
```

---

## 🔗 References

- [BridgeCore Documentation](../README.md)
- [odoo-webhook-corp Repository](https://github.com/geniustep/odoo-webhook-corp)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Strawberry GraphQL](https://strawberry.rocks/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)

---

**Status**: ✅ Architecture Design Complete - Ready for Implementation
**Last Updated**: 2025-11-16
**Version**: 1.0.0
