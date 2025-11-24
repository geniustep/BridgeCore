# BridgeCore Offline Sync - Complete Guide

## 📚 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Core Concepts](#core-concepts)
- [API Reference](#api-reference)
- [Implementation Guide](#implementation-guide)
- [Conflict Resolution](#conflict-resolution)
- [Best Practices](#best-practices)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

---

## 🌟 Overview

BridgeCore Offline Sync is a comprehensive offline-first synchronization system designed for mobile and web applications that need to work seamlessly with or without internet connectivity.

### Key Features

✅ **Push/Pull Architecture**: Upload local changes and download server updates
✅ **Conflict Detection**: Automatic conflict detection with multiple resolution strategies
✅ **Dependency Resolution**: Handles complex relationships between records
✅ **Batch Processing**: Efficient processing of multiple changes
✅ **Incremental Sync**: Only sync what changed since last time
✅ **Multi-Device Support**: Each device maintains independent sync state
✅ **Model Filtering**: Sync only relevant data for each app type
✅ **Tenant Isolation**: Complete data isolation per tenant

### Use Cases

1. **Mobile Sales App**: Sales reps work offline and sync when back online
2. **Delivery App**: Drivers update deliveries offline, sync at end of day
3. **Warehouse App**: Inventory updates in areas with poor connectivity
4. **Field Service**: Technicians work at remote locations
5. **CRM App**: Sales team updates leads and opportunities offline

---

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Mobile/Web Application                       │
│                    (Offline-First)                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Local SQLite │  │ Sync Manager │  │  UI Layer    │         │
│  │   Database   │◄─┤    Service   ├─►│              │         │
│  └──────────────┘  └───────┬──────┘  └──────────────┘         │
│                            │                                    │
└────────────────────────────┼────────────────────────────────────┘
                             │ HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BridgeCore API                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Offline Sync Endpoints                           │  │
│  │  /api/v1/offline-sync/push                               │  │
│  │  /api/v1/offline-sync/pull                               │  │
│  │  /api/v1/offline-sync/resolve-conflicts                  │  │
│  │  /api/v1/offline-sync/state                              │  │
│  │  /api/v1/offline-sync/reset                              │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                         │
│  ┌────────────────────▼─────────────────────────────────────┐  │
│  │         OfflineSyncService                               │  │
│  │  - push_changes()                                        │  │
│  │  - pull_changes()                                        │  │
│  │  - resolve_conflicts()                                   │  │
│  │  - get_sync_state()                                      │  │
│  └───────┬──────────────────────┬───────────────────────────┘  │
│          │                      │                               │
│  ┌───────▼──────────┐  ┌────────▼─────────┐                   │
│  │  OdooClient      │  │  CacheService    │                   │
│  │  (XML-RPC)       │  │  (Redis)         │                   │
│  └───────┬──────────┘  └──────────────────┘                   │
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
│  └──────────────────┘  └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

#### Push (Upload Local Changes)

```
1. User makes changes offline
   ↓
2. Changes saved to local SQLite with status="pending_sync"
   ↓
3. When online, app calls /push with all pending changes
   ↓
4. BridgeCore processes changes in batches:
   - Sorts by dependencies
   - Replaces local IDs with server IDs
   - Detects conflicts
   - Executes create/update/delete on Odoo
   ↓
5. Returns results with ID mapping
   ↓
6. App updates local database:
   - Maps local IDs to server IDs
   - Marks changes as "synced"
   - Handles conflicts if any
```

#### Pull (Download Server Changes)

```
1. App calls /pull with last_event_id
   ↓
2. BridgeCore queries Odoo for new events:
   - WHERE id > last_event_id
   - Filters by app_type models
   - Orders by id ASC
   ↓
3. Returns new events with server data
   ↓
4. App applies changes to local database:
   - Create new records
   - Update existing records
   - Delete removed records
   ↓
5. Updates last_event_id for next sync
```

---

## 💡 Core Concepts

### 1. Sync State

Each device maintains its own sync state:

```json
{
  "device_id": "iphone-abc123",
  "user_id": 1,
  "last_event_id": 1250,
  "last_sync_time": "2025-11-24T10:30:00Z",
  "total_syncs": 150,
  "app_type": "sales_app"
}
```

**Purpose**: Track what has been synced to avoid duplicates

### 2. Local Changes

Changes made offline are tracked locally:

```json
{
  "local_id": "local_uuid_1",
  "action": "create",
  "model": "sale.order",
  "record_id": null,
  "data": {
    "partner_id": 42,
    "date_order": "2025-11-24"
  },
  "local_timestamp": "2025-11-24T10:30:00Z",
  "version": 1
}
```

**Purpose**: Queue changes for upload when online

### 3. Conflict Detection

Conflicts occur when:
- Local change was made BEFORE server change
- Server record was modified by another user
- Timestamps don't match

**Example**:
```
User A (offline): Changes customer phone at 10:30
User B (online):  Changes customer phone at 10:35
User A (online):  Tries to sync at 10:40 → CONFLICT!
```

### 4. Conflict Resolution Strategies

```python
SERVER_WINS    # Server data takes precedence (default)
CLIENT_WINS    # Client data overwrites server
MANUAL         # Return conflict for user to resolve
MERGE          # Merge both versions
NEWEST_WINS    # Most recent change wins
```

### 5. App Type Filtering

Each app type syncs only relevant models:

```python
APP_TYPE_MODELS = {
    "sales_app": [
        "sale.order",
        "sale.order.line",
        "res.partner",
        "product.product"
    ],
    "delivery_app": [
        "stock.picking",
        "stock.move",
        "res.partner"
    ],
    # ... more app types
}
```

**Purpose**: Reduce data transfer and sync time

---

## 📡 API Reference

### Base URL

```
https://api.bridgecore.com/api/v1/offline-sync
```

### Authentication

All endpoints require JWT authentication:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### Endpoints

#### 1. Push Local Changes

**POST** `/push`

Upload local changes to server.

**Request Body**:
```json
{
  "device_id": "iphone-abc123",
  "changes": [
    {
      "local_id": "local_uuid_1",
      "action": "create",
      "model": "sale.order",
      "record_id": null,
      "data": {
        "partner_id": 42,
        "order_line": []
      },
      "local_timestamp": "2025-11-24T10:30:00Z",
      "version": 1,
      "priority": 5
    }
  ],
  "conflict_strategy": "server_wins",
  "stop_on_error": false,
  "batch_size": 50
}
```

**Response**:
```json
{
  "success": true,
  "total": 10,
  "succeeded": 9,
  "failed": 0,
  "conflicts": 1,
  "results": [
    {
      "local_id": "local_uuid_1",
      "status": "success",
      "action": "create",
      "model": "sale.order",
      "server_id": 789,
      "server_timestamp": "2025-11-24T10:31:00Z",
      "processing_time_ms": 45.2
    }
  ],
  "id_mapping": {
    "local_uuid_1": 789,
    "local_uuid_2": 790
  },
  "next_sync_token": "1_iphone-abc123_1732451400",
  "server_timestamp": "2025-11-24T10:31:00Z",
  "total_processing_time_ms": 523.5,
  "average_processing_time_ms": 52.3
}
```

**Rate Limit**: 100 requests/minute

---

#### 2. Pull Server Changes

**POST** `/pull`

Download new changes from server.

**Request Body**:
```json
{
  "device_id": "iphone-abc123",
  "app_type": "sales_app",
  "last_event_id": 1250,
  "models_filter": ["sale.order", "res.partner"],
  "priority_filter": ["high", "medium"],
  "limit": 100,
  "offset": 0,
  "include_payload": true,
  "include_metadata": false
}
```

**Response**:
```json
{
  "success": true,
  "has_updates": true,
  "new_events_count": 25,
  "events": [
    {
      "event_id": 1251,
      "model": "sale.order",
      "record_id": 456,
      "action": "write",
      "timestamp": "2025-11-24T10:30:00Z",
      "data": {
        "id": 456,
        "state": "sale",
        "amount_total": 1500.00
      },
      "changed_fields": ["state", "amount_total"],
      "priority": "high",
      "category": "business"
    }
  ],
  "next_sync_token": "1_iphone-abc123_1732451400",
  "last_event_id": 1275,
  "last_sync_time": "2025-11-24T10:31:00Z",
  "has_more": false,
  "total_available": 25,
  "server_timestamp": "2025-11-24T10:31:00Z"
}
```

**Rate Limit**: 200 requests/minute

---

#### 3. Resolve Conflicts

**POST** `/resolve-conflicts`

Resolve conflicts manually or automatically.

**Request Body**:
```json
{
  "device_id": "iphone-abc123",
  "conflicts": [
    {
      "local_id": "local_uuid_5",
      "server_id": 123,
      "model": "res.partner",
      "local_data": {"phone": "+1234567890"},
      "server_data": {"phone": "+0987654321"}
    }
  ],
  "resolutions": [
    {
      "local_id": "local_uuid_5",
      "strategy": "client_wins"
    }
  ]
}
```

**Response**:
```json
{
  "success": true,
  "resolved": 1,
  "failed": 0,
  "results": [
    {
      "local_id": "local_uuid_5",
      "status": "success",
      "action": "update",
      "model": "res.partner",
      "server_id": 123
    }
  ]
}
```

**Rate Limit**: 50 requests/minute

---

#### 4. Get Sync State

**GET** `/state?device_id=iphone-abc123`

Get current sync state for device.

**Response**:
```json
{
  "device_id": "iphone-abc123",
  "user_id": 1,
  "last_event_id": 1275,
  "last_sync_time": "2025-11-24T10:31:00Z",
  "next_sync_token": "1_iphone-abc123_1732451400",
  "total_syncs": 150,
  "total_events_synced": 3500,
  "sync_status": "idle",
  "pending_changes": 0,
  "app_type": "sales_app"
}
```

**Rate Limit**: 100 requests/minute

---

#### 5. Reset Sync State

**POST** `/reset?device_id=iphone-abc123`

Reset sync state to force full sync.

**Response**:
```json
{
  "success": true,
  "message": "Sync state reset successfully",
  "device_id": "iphone-abc123"
}
```

**Rate Limit**: 10 requests/hour

---

## 🚀 Implementation Guide

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

// 3. Start background sync (every 30 seconds)
syncService.startBackgroundSync();

// 4. Manual sync on user action
async function manualSync() {
  try {
    // Step 1: Push local changes
    const pushResult = await syncService.push();
    console.log(`Pushed ${pushResult.succeeded} changes`);

    // Step 2: Handle conflicts if any
    if (pushResult.conflicts > 0) {
      await handleConflicts(pushResult);
    }

    // Step 3: Pull server changes
    const pullResult = await syncService.pull();
    console.log(`Pulled ${pullResult.new_events_count} events`);

    // Step 4: Apply to local database
    await applyEventsToDatabase(pullResult.events);

    // Step 5: Update UI
    notifyUser('Sync completed successfully');

  } catch (error) {
    console.error('Sync failed:', error);
    notifyUser('Sync failed. Will retry automatically.');
  }
}
```

### Handling Offline Changes

```typescript
// When user creates/updates/deletes offline
async function saveOfflineChange(action, model, data) {
  const change = {
    local_id: generateUUID(),
    action: action,
    model: model,
    data: data,
    local_timestamp: new Date().toISOString(),
    sync_status: 'pending',
    version: 1,
  };

  // Save to local database
  await localDB.insert('pending_changes', change);

  // Try to sync immediately if online
  if (navigator.onLine) {
    await syncService.push();
  }
}
```

### Handling Conflicts

```typescript
async function handleConflicts(pushResult) {
  const conflicts = pushResult.results.filter(
    r => r.status === 'conflict'
  );

  for (const conflict of conflicts) {
    // Show conflict resolution UI to user
    const resolution = await showConflictDialog({
      localData: conflict.conflict_info.local_data,
      serverData: conflict.conflict_info.server_data,
    });

    // Submit resolution
    await syncService.resolveConflict({
      local_id: conflict.local_id,
      strategy: resolution.strategy,
      merged_data: resolution.merged_data,
    });
  }
}
```

---

## ⚔️ Conflict Resolution

### Conflict Detection

Conflicts are detected when:

1. **Version Mismatch**: Local version < Server version
2. **Timestamp Mismatch**: Server write_date > Local timestamp
3. **Concurrent Modification**: Two users modify same record

### Resolution Strategies

#### 1. Server Wins (Default)

```json
{
  "conflict_strategy": "server_wins"
}
```

- **Use when**: Server data is always correct
- **Result**: Local change discarded, server data kept
- **Safe for**: Settings, configurations

#### 2. Client Wins

```json
{
  "conflict_strategy": "client_wins"
}
```

- **Use when**: Client data is always correct
- **Result**: Server data overwritten with local
- **Safe for**: User preferences, drafts

#### 3. Manual Resolution

```json
{
  "conflict_strategy": "manual"
}
```

- **Use when**: User should decide
- **Result**: Conflict returned to client
- **Safe for**: Critical business data

#### 4. Merge

```json
{
  "conflict_strategy": "merge",
  "merged_data": {
    "name": "Merged Name",
    "email": "local_email@example.com",
    "phone": "+server_phone"
  }
}
```

- **Use when**: Both changes are valid
- **Result**: Custom merged data applied
- **Safe for**: Non-overlapping field changes

#### 5. Newest Wins

```json
{
  "conflict_strategy": "newest_wins"
}
```

- **Use when**: Most recent change should win
- **Result**: Compares timestamps, keeps newest
- **Safe for**: Time-sensitive data

---

## ✅ Best Practices

### 1. Sync Frequency

```typescript
// Background sync every 30 seconds
setInterval(async () => {
  if (navigator.onLine && !isSyncing) {
    await syncService.syncOnce();
  }
}, 30000);

// Aggressive sync for critical changes
async function saveCriticalChange(data) {
  await saveOfflineChange('create', 'sale.order', data);
  await syncService.push(); // Immediate sync
}
```

### 2. Error Handling

```typescript
try {
  await syncService.push();
} catch (error) {
  if (error.code === 'NETWORK_ERROR') {
    // Retry later
    scheduleRetry();
  } else if (error.code === 'CONFLICT') {
    // Handle conflicts
    await handleConflicts(error.conflicts);
  } else {
    // Log error
    logger.error('Sync failed', error);
  }
}
```

### 3. Optimistic Updates

```typescript
// Update UI immediately
updateUI(newData);

// Save locally
await saveOfflineChange('update', 'res.partner', newData);

// Sync in background
syncService.push().catch(error => {
  // Revert UI if sync fails
  revertUI();
  showError('Update failed. Try again.');
});
```

### 4. Batch Operations

```typescript
// Batch multiple changes together
const changes = [];

for (const item of items) {
  changes.push({
    local_id: generateUUID(),
    action: 'create',
    model: 'sale.order.line',
    data: item,
  });
}

// Push all at once
await syncService.push({ changes });
```

### 5. Progress Tracking

```typescript
syncService.on('progress', (event) => {
  const progress = (event.current / event.total) * 100;
  updateProgressBar(progress);
});

syncService.on('complete', () => {
  hideProgressBar();
  notifyUser('Sync completed');
});
```

---

## 📱 Examples

### Flutter Example

```dart
class OfflineSyncService {
  final String baseUrl;
  final String deviceId;
  final String appType;

  OfflineSyncService({
    required this.baseUrl,
    required this.deviceId,
    required this.appType,
  });

  // Push local changes
  Future<PushResponse> push() async {
    // Get pending changes from local DB
    final changes = await db.getPendingChanges();

    if (changes.isEmpty) {
      return PushResponse(success: true, total: 0);
    }

    // Call API
    final response = await dio.post(
      '$baseUrl/api/v1/offline-sync/push',
      data: {
        'device_id': deviceId,
        'changes': changes.map((c) => c.toJson()).toList(),
        'conflict_strategy': 'server_wins',
      },
    );

    final result = PushResponse.fromJson(response.data);

    // Update local database with server IDs
    await updateLocalIds(result.id_mapping);

    // Mark as synced
    await markAsSynced(changes);

    return result;
  }

  // Pull server changes
  Future<PullResponse> pull() async {
    // Get last event ID
    final lastEventId = await db.getLastEventId(deviceId);

    // Call API
    final response = await dio.post(
      '$baseUrl/api/v1/offline-sync/pull',
      data: {
        'device_id': deviceId,
        'app_type': appType,
        'last_event_id': lastEventId,
        'limit': 100,
      },
    );

    final result = PullResponse.fromJson(response.data);

    // Apply events to local database
    await applyEvents(result.events);

    // Update last event ID
    await db.setLastEventId(deviceId, result.last_event_id);

    return result;
  }

  // Complete sync
  Future<void> syncOnce() async {
    try {
      // Push first
      final pushResult = await push();

      // Handle conflicts
      if (pushResult.conflicts > 0) {
        await handleConflicts(pushResult);
      }

      // Then pull
      await pull();

    } catch (e) {
      print('Sync error: $e');
      rethrow;
    }
  }

  // Background sync
  void startBackgroundSync() {
    Timer.periodic(Duration(seconds: 30), (timer) async {
      if (await checkConnectivity()) {
        await syncOnce();
      }
    });
  }
}
```

### React/TypeScript Example

```typescript
class OfflineSyncService {
  private baseUrl: string;
  private deviceId: string;
  private appType: string;
  private token: string;

  constructor(config: SyncConfig) {
    this.baseUrl = config.baseUrl;
    this.deviceId = config.deviceId;
    this.appType = config.appType;
    this.token = config.token;
  }

  async push(): Promise<PushResponse> {
    // Get pending changes
    const changes = await this.getPendingChanges();

    if (changes.length === 0) {
      return { success: true, total: 0 };
    }

    // Call API
    const response = await fetch(
      `${this.baseUrl}/api/v1/offline-sync/push`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          device_id: this.deviceId,
          changes: changes,
          conflict_strategy: 'server_wins',
        }),
      }
    );

    const result = await response.json();

    // Update local database
    await this.updateLocalIds(result.id_mapping);
    await this.markAsSynced(changes);

    return result;
  }

  async pull(): Promise<PullResponse> {
    const lastEventId = await this.getLastEventId();

    const response = await fetch(
      `${this.baseUrl}/api/v1/offline-sync/pull`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          device_id: this.deviceId,
          app_type: this.appType,
          last_event_id: lastEventId,
          limit: 100,
        }),
      }
    );

    const result = await response.json();

    // Apply events
    await this.applyEvents(result.events);
    await this.setLastEventId(result.last_event_id);

    return result;
  }

  async syncOnce(): Promise<void> {
    await this.push();
    await this.pull();
  }

  startBackgroundSync(): void {
    setInterval(async () => {
      if (navigator.onLine) {
        try {
          await this.syncOnce();
        } catch (error) {
          console.error('Background sync failed:', error);
        }
      }
    }, 30000);
  }
}
```

---

## 🔧 Troubleshooting

### Problem: Changes not syncing

**Solutions**:
1. Check internet connectivity
2. Verify JWT token is valid
3. Check sync state: `GET /api/v1/offline-sync/state`
4. Review pending changes in local database
5. Check API logs for errors

### Problem: Frequent conflicts

**Solutions**:
1. Sync more frequently (reduce interval)
2. Use optimistic locking (version field)
3. Change conflict strategy to `newest_wins`
4. Implement field-level conflict resolution
5. Educate users about offline editing

### Problem: Slow sync performance

**Solutions**:
1. Reduce batch size
2. Filter by specific models only
3. Sync during off-peak hours
4. Use pagination for large datasets
5. Check network speed

### Problem: Duplicate records

**Solutions**:
1. Ensure local_id is truly unique (use UUID)
2. Check ID mapping is applied correctly
3. Verify sync state is updated after push
4. Don't retry push without clearing synced changes
5. Reset sync state if database corrupted

### Problem: Missing changes

**Solutions**:
1. Check if changes were marked as synced prematurely
2. Verify last_event_id is correct
3. Check Odoo webhooks are enabled
4. Review model filtering (app_type)
5. Use full sync reset: `POST /reset`

---

## 📊 Performance Tips

### 1. Optimize Database Queries

```sql
-- Create indexes for fast lookups
CREATE INDEX idx_pending_changes_status
ON pending_changes(sync_status);

CREATE INDEX idx_pending_changes_timestamp
ON pending_changes(local_timestamp);
```

### 2. Compress Payloads

```typescript
// Use gzip compression for large payloads
const compressed = await gzip(JSON.stringify(changes));
```

### 3. Parallel Processing

```typescript
// Push and pull in parallel (if no conflicts)
const [pushResult, pullResult] = await Promise.all([
  syncService.push(),
  syncService.pull(),
]);
```

### 4. Smart Retry

```typescript
// Exponential backoff for retries
async function retrySync(attempt = 0) {
  try {
    await syncService.syncOnce();
  } catch (error) {
    const delay = Math.pow(2, attempt) * 1000; // 1s, 2s, 4s, 8s
    setTimeout(() => retrySync(attempt + 1), delay);
  }
}
```

---

## 🎯 Summary

BridgeCore Offline Sync provides a complete solution for building offline-first applications:

✅ **Push/Pull** architecture for bidirectional sync
✅ **Conflict resolution** with multiple strategies
✅ **Incremental sync** for efficiency
✅ **Multi-device support** with independent states
✅ **Batch processing** for performance
✅ **Model filtering** for reduced data transfer
✅ **Tenant isolation** for security

### Next Steps

1. 📖 Read the [API Reference](#api-reference)
2. 💻 Check [Examples](#examples)
3. 🚀 Start implementing in your app
4. 📞 Contact support for help

---

**Made with ❤️ by BridgeCore Team**

For support: support@bridgecore.com
Documentation: https://docs.bridgecore.com
GitHub: https://github.com/geniustep/BridgeCore
