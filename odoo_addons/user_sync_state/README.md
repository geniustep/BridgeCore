# User Sync State Module for Odoo

## Overview

This module provides synchronization state tracking for BridgeCore Smart Sync API. It enables multi-user, multi-device synchronization by tracking the last synced event ID for each user/device combination.

## Features

- **Multi-User Support**: Track sync state per user
- **Multi-Device Support**: Each device has its own sync state
- **App Type Filtering**: Different sync states for different app types
- **Sync Statistics**: Track sync count, total events, and performance
- **Automatic State Management**: Auto-create states via API
- **Cleanup Tools**: Remove old inactive states

## Installation

1. Copy the `user_sync_state` folder to your Odoo addons directory:
   ```bash
   cp -r user_sync_state /path/to/odoo/addons/
   ```

2. Update the addons list in Odoo:
   - Go to Apps
   - Click "Update Apps List"

3. Install the module:
   - Search for "User Sync State"
   - Click "Install"

## Configuration

No configuration required. The module works out of the box with BridgeCore.

## Usage

### From BridgeCore API

The module is designed to work seamlessly with BridgeCore v2 Smart Sync API:

```python
# BridgeCore automatically calls these methods:
sync_state = odoo_client.call_kw(
    'user.sync.state',
    'get_or_create_state',
    [user_id, device_id, app_type]
)
```

### From Odoo UI

Access sync states via:
- **Menu**: Sync States > User Sync States
- **View**: See all active sync states
- **Actions**: Reset, Activate, Deactivate states

### API Methods

#### `get_or_create_state(user_id, device_id, app_type)`
Get existing sync state or create new one.

**Parameters:**
- `user_id` (int): Odoo user ID
- `device_id` (str): Unique device identifier
- `app_type` (str): App type (sales_app, delivery_app, etc.)

**Returns:**
```python
{
    'id': 123,
    'user_id': 1,
    'device_id': 'iphone-abc123',
    'app_type': 'sales_app',
    'last_event_id': 550,
    'last_sync_time': '2025-11-16T10:30:00',
    'sync_count': 25,
    'is_active': True
}
```

#### `update_sync_state(last_event_id, event_count)`
Update state after successful sync.

#### `reset_sync_state()`
Reset state to force full sync.

#### `cleanup_old_states(days=90)`
Remove inactive states older than specified days.

#### `get_sync_statistics(user_id=None)`
Get sync statistics for monitoring.

## App Types

Supported app types:
- `sales_app`: Sales application
- `delivery_app`: Delivery application
- `warehouse_app`: Warehouse application
- `manager_app`: Manager application
- `mobile_app`: Generic mobile application

## Database Schema

### Table: `user_sync_state`

| Field | Type | Description |
|-------|------|-------------|
| `user_id` | Many2one(res.users) | User who owns this state |
| `device_id` | Char(255) | Unique device identifier |
| `app_type` | Selection | Type of application |
| `last_event_id` | Integer | Last synced event ID |
| `last_sync_time` | Datetime | Last sync timestamp |
| `sync_count` | Integer | Total sync operations |
| `is_active` | Boolean | Active status |
| `total_events_synced` | Integer | Lifetime event count |

### Constraints

- **Unique**: `(user_id, device_id)` must be unique

## Integration with BridgeCore

### Smart Sync Flow

1. **Mobile App** → POST `/api/v2/sync/pull`
2. **BridgeCore** → Call `get_or_create_state()`
3. **Odoo** → Return sync state
4. **BridgeCore** → Fetch events where `id > last_event_id`
5. **BridgeCore** → Call `update_sync_state()`
6. **Mobile App** ← Receive new events

### Example BridgeCore Integration

```python
# In BridgeCore WebhookService
async def smart_sync(self, sync_request: SyncRequest):
    # Get sync state
    sync_state = await self.odoo.call_kw(
        "user.sync.state",
        "get_or_create_state",
        [
            sync_request.user_id,
            sync_request.device_id,
            sync_request.app_type
        ]
    )

    last_event_id = sync_state.get("last_event_id", 0)

    # Fetch new events
    events = await self.odoo.search_read(
        "update.webhook",
        domain=[("id", ">", last_event_id)],
        limit=100
    )

    # Update sync state
    if events:
        new_last_event_id = events[-1]["id"]
        await self.odoo.call_kw(
            "user.sync.state",
            "write",
            [[sync_state["id"]], {
                "last_event_id": new_last_event_id,
                "last_sync_time": datetime.now().isoformat(),
                "sync_count": sync_state.get("sync_count", 0) + 1
            }]
        )

    return events
```

## Monitoring & Maintenance

### View Sync Statistics

```python
# From Odoo Python console
env['user.sync.state'].get_sync_statistics()
```

### Cleanup Old States

```python
# Remove states inactive for 90+ days
env['user.sync.state'].cleanup_old_states(days=90)
```

### Monitor Active Devices

```xml
<!-- In Odoo UI -->
Sync States → User Sync States → Group By: User
```

## Troubleshooting

### Device Not Syncing

1. Check if sync state exists:
   ```python
   env['user.sync.state'].search([
       ('user_id', '=', user_id),
       ('device_id', '=', device_id)
   ])
   ```

2. Reset sync state:
   ```python
   state.reset_sync_state()
   ```

### Multiple Devices Per User

Each device has its own sync state. This is normal and expected for multi-device support.

### Sync Count Not Increasing

Check:
- Is the sync state active? (`is_active = True`)
- Is BridgeCore calling `update_sync_state()`?
- Check BridgeCore logs for errors

## Security

Access levels:
- **Users** (`base.group_user`): Read, Write, Create
- **System Administrators** (`base.group_system`): Full access including Delete

## Performance

- Indexed fields: `user_id`, `device_id`, `last_event_id`, `is_active`
- Optimized queries for large datasets
- Efficient cleanup with batch operations

## License

LGPL-3

## Author

BridgeCore Team

## Support

- GitHub: https://github.com/geniustep/BridgeCore
- Issues: https://github.com/geniustep/BridgeCore/issues

## Changelog

### Version 1.0.0
- Initial release
- Basic sync state tracking
- Multi-user/multi-device support
- Statistics and monitoring
- Cleanup tools
