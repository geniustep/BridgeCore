# BridgeCore Smart Sync Architecture

## Table of Contents

- [Overview](#overview)
- [Architecture Diagram](#architecture-diagram)
- [Core Components](#core-components)
- [Data Flow](#data-flow)
- [Sync Strategies](#sync-strategies)
- [Implementation Details](#implementation-details)
- [Performance Optimization](#performance-optimization)
- [Error Handling](#error-handling)
- [Security](#security)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

---

## Overview

BridgeCore Smart Sync is an intelligent, incremental synchronization system designed for multi-user, multi-device scenarios. It enables Flutter mobile applications to efficiently sync data with Odoo ERP by:

- ✅ Tracking sync state per user/device
- ✅ Pulling only NEW events since last sync
- ✅ Filtering events by app type
- ✅ Caching for performance
- ✅ Supporting real-time critical events via WebSocket
- ✅ Handling network failures gracefully

**Key Benefits:**
- **Reduced Data Transfer**: Only sync what changed
- **Battery Efficient**: Fewer network requests
- **Offline Support**: Sync when back online
- **Multi-Device**: Each device syncs independently
- **Real-Time**: Critical events pushed via WebSocket

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Flutter Mobile App                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  Sales App   │  │ Delivery App │  │  Manager App │        │
│  │  (iPhone)    │  │  (Android)   │  │  (iPad)      │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
│         │                  │                  │                 │
│         │ Background Sync  │                  │                 │
│         │ (Every 30s)      │                  │                 │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          │ HTTP/2           │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BridgeCore API                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            Smart Sync Routes (/api/v2/sync/*)            │  │
│  │  - POST /pull   (incremental sync)                       │  │
│  │  - GET /state   (get sync state)                         │  │
│  │  - POST /reset  (force full sync)                        │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                         │
│  ┌────────────────────▼─────────────────────────────────────┐  │
│  │                WebhookService                            │  │
│  │  - smart_sync()                                          │  │
│  │  - get_sync_state()                                      │  │
│  │  - reset_sync_state()                                    │  │
│  │  - check_updates()                                       │  │
│  └───────┬──────────────────────┬───────────────────────────┘  │
│          │                      │                               │
│  ┌───────▼──────────┐  ┌────────▼─────────┐                   │
│  │  OdooClient      │  │  CacheService    │                   │
│  │  - pull_events() │  │  (Redis)         │                   │
│  │  - get/create    │  │  - TTL: 60s      │                   │
│  │    sync_state()  │  │  - Cache key:    │                   │
│  │  - update_state()│  │    sync:user:dev │                   │
│  └───────┬──────────┘  └──────────────────┘                   │
│          │                                                      │
└──────────┼──────────────────────────────────────────────────────┘
           │ XML-RPC / JSON-RPC
           ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Odoo ERP System                           │
│  ┌──────────────────┐  ┌────────────────────────────────────┐  │
│  │ user.sync.state  │  │      update.webhook                │  │
│  │                  │  │                                    │  │
│  │ - user_id        │  │  - id                              │  │
│  │ - device_id      │  │  - model                           │  │
│  │ - app_type       │  │  - record_id                       │  │
│  │ - last_event_id  │  │  - event (create/write/unlink)     │  │
│  │ - last_sync_time │  │  - timestamp                       │  │
│  │ - sync_count     │  │  - payload                         │  │
│  │ - is_active      │  │  - priority (high/medium/low)      │  │
│  └──────────────────┘  └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

Optional: WebSocket for Real-Time Critical Events
┌─────────────────────┐
│  Flutter App (WS)   │
└──────────┬──────────┘
           │ ws://api.bridgecore.ma/ws/{user_id}
           ▼
┌─────────────────────┐    ┌──────────────┐
│ WebSocket Manager   │◄───│ Redis PubSub │
│ - critical_events   │    │ - Distributed│
│ - urgent_updates    │    │   Events     │
│ - sync_events       │    └──────────────┘
└─────────────────────┘
```

---

## Core Components

### 1. user.sync.state (Odoo Model)

Tracks synchronization state for each user/device combination.

**Fields:**
- `user_id`: Odoo user
- `device_id`: Unique device identifier
- `app_type`: Application type (sales_app, delivery_app, etc.)
- `last_event_id`: ID of last synced webhook event
- `last_sync_time`: Timestamp of last sync
- `sync_count`: Total sync operations performed
- `is_active`: Active status

**Key Methods:**
- `get_or_create_state(user_id, device_id, app_type)`: Get or create sync state
- `update_sync_state(last_event_id, event_count)`: Update after successful sync
- `reset_sync_state()`: Reset to force full sync

**Location:** `auto-webhook-odoo/models/user_sync_state.py` (الإصدار 2.1.0+)

### 2. WebhookService (BridgeCore)

Business logic for smart sync operations.

**Key Methods:**

#### `smart_sync(sync_request: SyncRequest) -> SyncResponse`
Main sync method:
1. Get/create sync state for user/device
2. Fetch events where `id > last_event_id`
3. Filter by app type models
4. Update sync state
5. Return new events

#### `get_sync_state(user_id, device_id) -> SyncStatsResponse`
Get current sync state.

#### `reset_sync_state(user_id, device_id) -> dict`
Reset sync state (force full sync).

#### `check_updates(since) -> CheckUpdatesOut`
Quick check for new updates.

**Location:** `app/modules/webhook/service.py`

### 3. OdooClient

Enhanced Odoo client with sync-specific methods.

**New Methods:**
- `pull_events(last_event_id, models, limit)`: Pull webhook events
- `get_or_create_sync_state(user_id, device_id, app_type)`: Manage sync state
- `update_sync_state(state_id, last_event_id, event_count)`: Update state
- `reset_sync_state(user_id, device_id)`: Reset state

**Location:** `app/utils/odoo_client.py`

### 4. CacheService

Redis-based caching for performance.

**Strategy:**
- Cache key format: `sync:{user_id}:{device_id}:{last_event_id}`
- TTL: 60 seconds
- Cache events for repeated requests

**Location:** `app/services/cache_service.py`

### 5. API Routes (/api/v2/sync/*)

FastAPI routes for sync operations.

**Endpoints:**

#### `POST /api/v2/sync/pull`
Pull new events since last sync.

**Request:**
```json
{
  "user_id": 1,
  "device_id": "iphone-abc123",
  "app_type": "sales_app",
  "limit": 100,
  "models_filter": ["sale.order"]  // Optional
}
```

**Response:**
```json
{
  "status": "success",
  "has_updates": true,
  "new_events_count": 25,
  "events": [
    {
      "id": 501,
      "model": "sale.order",
      "record_id": 456,
      "event": "write",
      "timestamp": "2025-11-16T10:30:00Z"
    }
  ],
  "next_sync_token": "525",
  "last_sync_time": "2025-11-16T10:25:00Z"
}
```

#### `GET /api/v2/sync/state?user_id=1&device_id=...`
Get sync state.

#### `POST /api/v2/sync/reset?user_id=1&device_id=...`
Reset sync state.

**Location:** `app/modules/webhook/router_v2.py`

---

## Data Flow

### First-Time Sync

```
1. Flutter App → POST /api/v2/sync/pull
   {user_id: 1, device_id: "iphone-123", app_type: "sales_app"}

2. WebhookService → get_or_create_sync_state()
   Returns: {last_event_id: 0, sync_count: 0} (new state)

3. WebhookService → pull_events(last_event_id=0, models=[...], limit=100)
   Odoo Query: SELECT * FROM update.webhook
               WHERE id > 0 AND model IN ('sale.order', ...)
               ORDER BY id ASC LIMIT 100

4. Odoo → Returns 100 events (id: 1-100)

5. WebhookService → update_sync_state(state_id=42, last_event_id=100)

6. Flutter App ← Response
   {has_updates: true, events: [...100 events...], next_sync_token: "100"}

7. Flutter App → Applies events to local database
```

### Incremental Sync (30 seconds later)

```
1. Flutter App → POST /api/v2/sync/pull
   {user_id: 1, device_id: "iphone-123", app_type: "sales_app"}

2. WebhookService → get_sync_state()
   Returns: {last_event_id: 100, sync_count: 1}

3. WebhookService → pull_events(last_event_id=100, models=[...], limit=100)
   Odoo Query: SELECT * FROM update.webhook
               WHERE id > 100 AND model IN ('sale.order', ...)
               ORDER BY id ASC LIMIT 100

4. Odoo → Returns 3 new events (id: 101-103)

5. WebhookService → update_sync_state(state_id=42, last_event_id=103)

6. Flutter App ← Response
   {has_updates: true, events: [...3 events...], next_sync_token: "103"}

7. Flutter App → Applies only 3 new events (incremental!)
```

### No Updates

```
1. Flutter App → POST /api/v2/sync/pull

2. WebhookService → pull_events(last_event_id=103, ...)
   Odoo Query: SELECT * ... WHERE id > 103 ...

3. Odoo → Returns empty array []

4. Flutter App ← Response
   {has_updates: false, events: [], next_sync_token: "103"}

5. Flutter App → No changes, skips database update
```

---

## Sync Strategies

### 1. Incremental Sync (Default)

Pull only events since last sync.

**Advantages:**
- Minimal data transfer
- Fast sync (< 200ms with cache)
- Battery efficient

**Use When:**
- Regular background sync
- User opens app
- Network restored after offline period

### 2. Full Sync (Force Reset)

Reset sync state and sync everything.

**When to Use:**
- First install
- After app data clear
- Database corruption recovery
- User requests "Refresh All"

**API:**
```bash
POST /api/v2/sync/reset?user_id=1&device_id=iphone-123
```

### 3. Real-Time Sync (WebSocket)

For critical events that need immediate delivery.

**Use Cases:**
- Urgent sale orders
- Critical stock alerts
- Important customer updates

**Flow:**
```
1. Flutter App connects: ws://api.bridgecore.ma/ws/{user_id}

2. Odoo creates high-priority event → triggers webhook

3. BridgeCore → publish to Redis channel "critical_events"

4. WebSocket Manager → send to user's WebSocket

5. Flutter App receives event → apply immediately

6. Flutter App triggers background sync for full update
```

---

## Implementation Details

### App Type Model Filtering

Each app type syncs only relevant models:

```python
APP_TYPE_MODELS = {
    "sales_app": [
        "sale.order",
        "sale.order.line",
        "res.partner",
        "product.template",
        "product.product"
    ],
    "delivery_app": [
        "stock.picking",
        "stock.move",
        "stock.move.line",
        "res.partner"
    ],
    "warehouse_app": [
        "stock.picking",
        "stock.move",
        "stock.quant",
        "product.product",
        "stock.location"
    ],
    "manager_app": [
        "sale.order",
        "purchase.order",
        "account.move",
        "hr.expense",
        "project.project"
    ]
}
```

**Benefits:**
- Reduced payload size
- Faster sync
- Lower battery usage

### Multi-Device Support

Each device maintains independent sync state:

```
User 1:
  - iPhone (device_id: "iphone-abc123")  → last_event_id: 100
  - iPad (device_id: "ipad-xyz789")     → last_event_id: 50

User 2:
  - Android (device_id: "android-123")   → last_event_id: 200
```

**Benefits:**
- Users can switch devices seamlessly
- Device-specific sync positions
- No interference between devices

### Caching Strategy

```python
# Cache key format
cache_key = f"sync:{user_id}:{device_id}:{last_event_id}"

# TTL
ttl = 60  # seconds

# Example
"sync:1:iphone-abc123:100" → [...events...]
```

**Cache Hit Scenarios:**
1. Multiple sync requests within 60s (e.g., app backgrounded/foregrounded)
2. Network retry after temporary failure
3. User manually triggers sync multiple times

**Cache Miss Scenarios:**
1. First sync
2. After 60s TTL expires
3. Different user/device
4. Different last_event_id (new events synced)

---

## Performance Optimization

### Benchmarks

| Scenario | Response Time | Data Transfer |
|----------|--------------|---------------|
| Cache Hit | < 50ms | ~2KB (metadata) |
| Cache Miss (No events) | < 200ms | ~2KB |
| Cache Miss (10 events) | < 500ms | ~15KB |
| Cache Miss (100 events) | < 1000ms | ~150KB |

### Optimization Techniques

#### 1. Async Operations
All I/O operations are async to prevent blocking:
```python
async def smart_sync(self, sync_request):
    # Non-blocking Odoo calls
    loop = asyncio.get_event_loop()
    sync_state = await loop.run_in_executor(None, odoo_call)
```

#### 2. Connection Pooling
Reuse database and Redis connections:
```python
# PostgreSQL pool
pool_size = 20
max_overflow = 10

# Redis connection reuse
redis_client = redis.from_url(REDIS_URL)
```

#### 3. Query Optimization
Indexed fields for fast queries:
```sql
-- Odoo indexes
CREATE INDEX idx_webhook_event_id ON update_webhook(id);
CREATE INDEX idx_webhook_model ON update_webhook(model);
CREATE INDEX idx_sync_state_user_device ON user_sync_state(user_id, device_id);
```

#### 4. Payload Minimization
Only return necessary fields:
```python
fields = ["id", "model", "record_id", "event", "timestamp"]
# Skip: payload, changed_fields (unless needed)
```

#### 5. Rate Limiting
Protect against abuse:
```python
@limiter.limit("200/minute")
async def sync_pull():
    pass
```

---

## Error Handling

### Retry Strategy

```python
# Exponential backoff
max_retries = 3
for attempt in range(max_retries):
    try:
        return await smart_sync()
    except OdooConnectionException:
        if attempt == max_retries - 1:
            raise
        await asyncio.sleep(2 ** attempt)  # 1s, 2s, 4s
```

### Exception Hierarchy

```python
BridgeCoreException
├── SyncException
│   ├── SyncStateNotFoundException
│   ├── SyncConflictException
│   └── InvalidSyncTokenException
├── OdooConnectionException
│   ├── OdooAuthenticationException
│   ├── OdooSessionExpiredException
│   └── OdooTimeoutException
└── WebhookException
    ├── WebhookEventNotFoundException
    └── WebhookRetryLimitException
```

### Error Responses

```json
{
  "error": "SyncStateNotFoundException",
  "message": "Sync state not found for user 1, device iphone-123",
  "code": "SYNC_STATE_NOT_FOUND",
  "details": {
    "user_id": 1,
    "device_id": "iphone-123"
  }
}
```

---

## Security

### Authentication

All sync endpoints require JWT authentication:
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### Authorization

Users can only sync their own data:
```python
# Validate user_id in request matches authenticated user
if sync_request.user_id != current_user.id:
    raise HTTPException(403, "Forbidden")
```

### Device Validation

Device IDs should be validated and registered:
```python
# Odoo validates device_id format
@api.constrains('device_id')
def _check_device_id(self):
    if len(self.device_id) < 3:
        raise ValidationError("Invalid device ID")
```

### Rate Limiting

```python
# Per-user limits
sync_pull: 200 requests/minute
get_state: 100 requests/minute
reset_state: 10 requests/hour
```

---

## Monitoring

### Metrics

#### Prometheus Metrics
```python
sync_requests_total
sync_events_returned_total
sync_cache_hits_total
sync_cache_misses_total
sync_errors_total
sync_duration_seconds
```

#### Grafana Dashboard

**Panels:**
1. Sync Requests per Minute
2. Cache Hit Rate
3. Average Sync Duration
4. Events Synced per User
5. Active Devices
6. Error Rate

### Logging

```python
# Success
logger.info(f"Smart sync complete: {len(events)} events for user {user_id}")

# Cache hit
logger.debug(f"Cache hit for sync query: {cache_key}")

# Error
logger.error(f"Odoo error during sync: {error}")
```

### Health Checks

```bash
# Smart sync health
GET /api/v2/sync/health

Response:
{
  "status": "healthy",
  "service": "smart-sync",
  "version": "2.0.0",
  "features": [
    "multi-user sync",
    "per-device tracking",
    "app-type filtering",
    "incremental sync"
  ]
}
```

---

## Troubleshooting

### Problem: No events returned but data changed in Odoo

**Solution:**
1. Check webhook module is installed in Odoo
2. Verify `update.webhook` model exists
3. Check webhook triggers are active
4. Verify sync state: `GET /api/v2/sync/state`

### Problem: Duplicate events

**Solution:**
- Events are ordered by ID (ascending)
- Each sync updates `last_event_id`
- Duplicates should not occur unless:
  - Sync state was manually modified
  - Database restore occurred

### Problem: Slow sync performance

**Solutions:**
1. Check cache is working (Redis available)
2. Verify Odoo query performance (indexes)
3. Reduce `limit` in sync request
4. Check network latency
5. Monitor Odoo server load

### Problem: Sync state not found

**Solutions:**
1. Check `user.sync.state` addon installed
2. Verify user ID and device ID are correct
3. Try reset sync state
4. Check database connectivity

---

## Best Practices

### For Mobile Developers

1. **Background Sync**
   ```dart
   Timer.periodic(Duration(seconds: 30), (_) {
     await syncService.backgroundSync();
   });
   ```

2. **Handle No Updates**
   ```dart
   if (response.has_updates) {
     await applyEvents(response.events);
   }
   ```

3. **Error Handling**
   ```dart
   try {
     await syncService.pull();
   } on SyncException catch (e) {
     if (e.code == "SYNC_STATE_NOT_FOUND") {
       await syncService.reset();
       await syncService.pull();
     }
   }
   ```

4. **WebSocket for Critical Events**
   ```dart
   websocket.onMessage((event) {
     if (event.type == "critical_event") {
       applyEventImmediately(event);
       scheduleSync();
     }
   });
   ```

### For Backend Developers

1. **Monitor Sync State Count**
   ```python
   stats = odoo_client.get_sync_statistics()
   if stats['active_states'] > 10000:
       logger.warning("High number of active sync states")
   ```

2. **Cleanup Old States**
   ```python
   # Cron job
   odoo_client.call_kw(
       "user.sync.state",
       "cleanup_old_states",
       [90]  # days
   )
   ```

3. **Cache Invalidation**
   ```python
   # After webhook event is created
   await cache.delete_pattern(f"sync:*")
   ```

---

## Conclusion

BridgeCore Smart Sync provides a robust, efficient, and scalable solution for synchronizing data between Flutter mobile apps and Odoo ERP. By tracking sync state per device, leveraging incremental sync, and optimizing with caching, it delivers fast, battery-efficient synchronization for modern mobile applications.

**Key Achievements:**
- ✅ < 200ms sync time (with cache)
- ✅ Multi-device support
- ✅ Real-time critical events
- ✅ Production-ready error handling
- ✅ Comprehensive monitoring

For questions or support:
- GitHub: https://github.com/geniustep/BridgeCore
- Issues: https://github.com/geniustep/BridgeCore/issues
