# BridgeCore Smart Sync Examples

This directory contains examples for integrating BridgeCore Smart Sync API with your applications.

## Contents

- [Flutter/Dart Example](#flutterdart-example)
- [cURL Examples](#curl-examples)
- [JavaScript/TypeScript Example](#javascripttypescript-example)
- [Python Example](#python-example)

---

## Flutter/Dart Example

See `flutter/smart_sync_service.dart` for a complete Flutter implementation.

### Quick Start

```dart
// 1. Add dependencies to pubspec.yaml
dependencies:
  dio: ^5.0.0
  shared_preferences: ^2.0.0
  web_socket_channel: ^2.0.0

// 2. Initialize service
final syncService = SmartSyncService(
  baseUrl: 'https://bridgecore.geniura.com',
  appType: 'sales_app',
  onEventsReceived: (events) async {
    // Apply events to local database
    for (final event in events) {
      await applyEvent(event);
    }
  },
);

await syncService.initialize();

// 3. Start background sync
syncService.startBackgroundSync();

// 4. Connect WebSocket for real-time events
syncService.connectWebSocket();
```

### Features

✅ Background sync every 30 seconds
✅ Manual sync (pull-to-refresh)
✅ Force full sync
✅ WebSocket for critical events
✅ Error handling & retry
✅ Offline support

---

## cURL Examples

### 1. Authentication

```bash
# Login to get access token
curl -X POST 'https://bridgecore.geniura.com/api/v1/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "your_username",
    "password": "your_password",
    "database": "your_database"
  }'

# Response:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIs...",
#   "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
#   "system_id": "odoo-your_username",
#   "user": { "id": 1, ... }
# }

# Save the access_token for subsequent requests
export TOKEN="eyJhbGciOiJIUzI1NiIs..."
```

### 2. Smart Sync Pull

```bash
# Pull new events since last sync
curl -X POST 'https://bridgecore.geniura.com/api/v2/sync/pull' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": 1,
    "device_id": "my-device-123",
    "app_type": "sales_app",
    "limit": 100
  }'

# Response:
# {
#   "status": "success",
#   "has_updates": true,
#   "new_events_count": 25,
#   "events": [
#     {
#       "id": 501,
#       "model": "sale.order",
#       "record_id": 456,
#       "event": "write",
#       "timestamp": "2025-11-16T10:30:00Z"
#     },
#     ...
#   ],
#   "next_sync_token": "525",
#   "last_sync_time": "2025-11-16T10:25:00Z"
# }
```

### 3. Get Sync State

```bash
# Get current sync state for user/device
curl -X GET 'https://bridgecore.geniura.com/api/v2/sync/state?user_id=1&device_id=my-device-123' \
  -H "Authorization: Bearer $TOKEN"

# Response:
# {
#   "user_id": 1,
#   "device_id": "my-device-123",
#   "last_event_id": 525,
#   "last_sync_time": "2025-11-16T10:30:00Z",
#   "sync_count": 15,
#   "is_active": true
# }
```

### 4. Reset Sync State (Force Full Sync)

```bash
# Reset sync state to force full sync
curl -X POST 'https://bridgecore.geniura.com/api/v2/sync/reset?user_id=1&device_id=my-device-123' \
  -H "Authorization: Bearer $TOKEN"

# Response:
# {
#   "status": "success",
#   "message": "Sync state reset successfully"
# }
```

### 5. Check for Updates (Quick)

```bash
# Quick check if updates are available
curl -X GET 'https://bridgecore.geniura.com/api/v1/webhooks/check-updates?limit=50' \
  -H "Authorization: Bearer $TOKEN"

# Response:
# {
#   "has_update": true,
#   "last_update_at": "2025-11-16 12:30:00",
#   "summary": [
#     {"model": "sale.order", "count": 15},
#     {"model": "res.partner", "count": 8}
#   ]
# }
```

### 6. Custom Model Filter

```bash
# Sync only specific models
curl -X POST 'https://bridgecore.geniura.com/api/v2/sync/pull' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": 1,
    "device_id": "my-device-123",
    "app_type": "sales_app",
    "limit": 100,
    "models_filter": ["sale.order", "res.partner"]
  }'
```

---

## JavaScript/TypeScript Example

```typescript
// SmartSyncClient.ts

interface SyncEvent {
  id: number;
  model: string;
  record_id: number;
  event: 'create' | 'write' | 'unlink';
  timestamp: string;
}

interface SyncResponse {
  status: string;
  has_updates: boolean;
  new_events_count: number;
  events: SyncEvent[];
  next_sync_token: string;
  last_sync_time?: string;
}

class SmartSyncClient {
  private baseUrl: string;
  private token: string;
  private userId: number;
  private deviceId: string;
  private appType: string;

  constructor(config: {
    baseUrl: string;
    token: string;
    userId: number;
    deviceId: string;
    appType: string;
  }) {
    this.baseUrl = config.baseUrl;
    this.token = config.token;
    this.userId = config.userId;
    this.deviceId = config.deviceId;
    this.appType = config.appType;
  }

  async pull(limit: number = 100): Promise<SyncResponse> {
    const response = await fetch(`${this.baseUrl}/api/v2/sync/pull`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: this.userId,
        device_id: this.deviceId,
        app_type: this.appType,
        limit: limit,
      }),
    });

    if (!response.ok) {
      throw new Error(`Sync failed: ${response.statusText}`);
    }

    return await response.json();
  }

  async getSyncState() {
    const params = new URLSearchParams({
      user_id: this.userId.toString(),
      device_id: this.deviceId,
    });

    const response = await fetch(
      `${this.baseUrl}/api/v2/sync/state?${params}`,
      {
        headers: {
          'Authorization': `Bearer ${this.token}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Get sync state failed: ${response.statusText}`);
    }

    return await response.json();
  }

  async reset() {
    const params = new URLSearchParams({
      user_id: this.userId.toString(),
      device_id: this.deviceId,
    });

    const response = await fetch(
      `${this.baseUrl}/api/v2/sync/reset?${params}`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.token}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Reset failed: ${response.statusText}`);
    }

    return await response.json();
  }

  async backgroundSync(
    onEventsReceived: (events: SyncEvent[]) => void,
    intervalMs: number = 30000
  ) {
    setInterval(async () => {
      try {
        const result = await this.pull();
        if (result.has_updates) {
          onEventsReceived(result.events);
        }
      } catch (error) {
        console.error('Background sync error:', error);
      }
    }, intervalMs);
  }
}

// Usage
const syncClient = new SmartSyncClient({
  baseUrl: 'https://bridgecore.geniura.com',
  token: 'your_access_token',
  userId: 1,
  deviceId: 'browser-abc123',
  appType: 'sales_app',
});

// Manual sync
const result = await syncClient.pull();
console.log(`Received ${result.new_events_count} events`);

// Background sync
syncClient.backgroundSync((events) => {
  console.log('New events:', events);
  // Apply to local state/database
});
```

---

## Python Example

```python
# smart_sync_client.py

import requests
import time
from typing import List, Dict, Optional, Callable
from threading import Thread

class SmartSyncClient:
    def __init__(
        self,
        base_url: str,
        token: str,
        user_id: int,
        device_id: str,
        app_type: str
    ):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.user_id = user_id
        self.device_id = device_id
        self.app_type = app_type
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        })

    def pull(self, limit: int = 100) -> Dict:
        """Pull new events since last sync"""
        response = self.session.post(
            f'{self.base_url}/api/v2/sync/pull',
            json={
                'user_id': self.user_id,
                'device_id': self.device_id,
                'app_type': self.app_type,
                'limit': limit
            }
        )
        response.raise_for_status()
        return response.json()

    def get_sync_state(self) -> Dict:
        """Get current sync state"""
        response = self.session.get(
            f'{self.base_url}/api/v2/sync/state',
            params={
                'user_id': self.user_id,
                'device_id': self.device_id
            }
        )
        response.raise_for_status()
        return response.json()

    def reset(self) -> Dict:
        """Reset sync state (force full sync)"""
        response = self.session.post(
            f'{self.base_url}/api/v2/sync/reset',
            params={
                'user_id': self.user_id,
                'device_id': self.device_id
            }
        )
        response.raise_for_status()
        return response.json()

    def background_sync(
        self,
        on_events_received: Callable[[List[Dict]], None],
        interval_seconds: int = 30
    ):
        """Start background sync in separate thread"""
        def sync_loop():
            while True:
                try:
                    result = self.pull()
                    if result['has_updates']:
                        on_events_received(result['events'])
                except Exception as e:
                    print(f"Background sync error: {e}")

                time.sleep(interval_seconds)

        thread = Thread(target=sync_loop, daemon=True)
        thread.start()

# Usage
if __name__ == '__main__':
    client = SmartSyncClient(
        base_url='https://bridgecore.geniura.com',
        token='your_access_token',
        user_id=1,
        device_id='python-client-123',
        app_type='sales_app'
    )

    # Manual sync
    result = client.pull()
    print(f"Has updates: {result['has_updates']}")
    print(f"Events count: {result['new_events_count']}")

    # Get sync state
    state = client.get_sync_state()
    print(f"Last event ID: {state['last_event_id']}")
    print(f"Sync count: {state['sync_count']}")

    # Background sync
    def handle_events(events):
        print(f"Received {len(events)} new events")
        for event in events:
            print(f"  - {event['event']} on {event['model']}:{event['record_id']}")

    client.background_sync(handle_events, interval_seconds=30)

    # Keep running
    input("Press Enter to stop...\n")
```

---

## Best Practices

### 1. Device ID Management

**Good:**
```dart
// Generate once, store permanently
String deviceId = await getDeviceUniqueId(); // Use device_info_plus
await prefs.setString('device_id', deviceId);
```

**Bad:**
```dart
// Don't generate new ID every time
String deviceId = DateTime.now().toString(); // ❌
```

### 2. Error Handling

**Good:**
```dart
try {
  await syncService.pull();
} on DioException catch (e) {
  if (e.response?.statusCode == 404) {
    // Sync state not found, reset
    await syncService.forceFullSync();
  } else {
    // Show error to user
  }
}
```

### 3. Background Sync Interval

**Recommendations:**
- **Active use**: 10-30 seconds
- **Background**: 1-5 minutes
- **Battery saver mode**: 10-15 minutes

### 4. Batch Processing

**Good:**
```dart
// Process events in batches
final batchSize = 20;
for (var i = 0; i < events.length; i += batchSize) {
  final batch = events.sublist(
    i,
    min(i + batchSize, events.length)
  );
  await database.transaction(() async {
    for (final event in batch) {
      await applyEvent(event);
    }
  });
}
```

---

## Troubleshooting

### Issue: Duplicate Events

**Solution:** Check that you're using the correct `device_id` and not regenerating it.

### Issue: Sync Too Slow

**Solutions:**
1. Reduce `limit` parameter
2. Filter by specific models
3. Check network connection
4. Verify cache is enabled

### Issue: Missing Events

**Solutions:**
1. Check sync state: `GET /api/v2/sync/state`
2. Verify app_type matches expected models
3. Check Odoo webhook module is active

---

## Support

- **Documentation**: See `docs/SYNC_ARCHITECTURE.md`
- **GitHub**: https://github.com/geniustep/BridgeCore
- **Issues**: https://github.com/geniustep/BridgeCore/issues
