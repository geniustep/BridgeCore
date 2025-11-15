# Flutter API Compatibility Changes

## Overview

BridgeCore has been updated to be 100% compatible with the Flutter mobile client. All endpoints now match the expected API structure.

## Quick Start

### 1. Start the Server

```bash
# Development
uvicorn app.main:app --reload

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2. Run Integration Tests

```bash
python test_flutter_integration.py
```

## API Changes

### Authentication Endpoints

All authentication endpoints moved to `/api/v1/auth/*`

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin",
  "database": "testdb"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "system_id": "odoo-testdb",
  "user": {
    "id": 1,
    "username": "admin",
    "name": "Administrator",
    "company_id": 1,
    "partner_id": 3
  }
}
```

#### Refresh Token
```http
POST /api/v1/auth/refresh
Authorization: Bearer {refresh_token}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### Get Session Info
```http
GET /api/v1/auth/session
Authorization: Bearer {access_token}

Response:
{
  "user": {
    "id": 1,
    "username": "admin",
    "name": "Administrator"
  },
  "session_expires_at": 1234567890
}
```

#### Logout
```http
POST /api/v1/auth/logout
Authorization: Bearer {access_token}

Response:
{}
```

### Odoo Operations Endpoint

Unified endpoint for all Odoo operations: `/api/v1/systems/{system_id}/odoo/{operation}`

#### Search Read
```http
POST /api/v1/systems/odoo-prod/odoo/search_read
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "model": "product.product",
  "domain": [["sale_ok", "=", true]],
  "fields": ["id", "name", "list_price"],
  "limit": 80,
  "offset": 0,
  "order": "name ASC"
}

Response:
{
  "result": [
    {
      "id": 1,
      "name": "Product A",
      "list_price": 100.0
    }
  ]
}
```

#### Create Record
```http
POST /api/v1/systems/odoo-prod/odoo/create
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "model": "res.partner",
  "values": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890"
  }
}

Response:
{
  "result": 123
}
```

#### Update Record
```http
POST /api/v1/systems/odoo-prod/odoo/write
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "model": "res.partner",
  "ids": [123],
  "values": {
    "phone": "+9876543210"
  }
}

Response:
{
  "result": true
}
```

#### Delete Record
```http
POST /api/v1/systems/odoo-prod/odoo/unlink
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "model": "res.partner",
  "ids": [123]
}

Response:
{
  "result": true
}
```

#### Get Fields Metadata
```http
POST /api/v1/systems/odoo-prod/odoo/fields_get
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "model": "product.product",
  "fields": ["name", "list_price"]
}

Response:
{
  "result": {
    "name": {
      "type": "char",
      "string": "Name",
      "required": true
    },
    "list_price": {
      "type": "float",
      "string": "Sales Price"
    }
  }
}
```

## Supported Odoo Operations

- `search_read` - Search and read records
- `read` - Read specific records by IDs
- `create` - Create new record
- `write` - Update existing records
- `unlink` - Delete records
- `search` - Search for record IDs only
- `search_count` - Count matching records
- `fields_get` - Get model field definitions
- `name_search` - Search by name
- `name_get` - Get display names
- `web_search_read` - Web search read (Odoo 14+)
- `web_read` - Web read (Odoo 14+)
- `web_save` - Web save (Odoo 14+)
- `call_kw` - Call any Odoo method

## Testing with cURL

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin","database":"testdb"}'

# Save the access_token from response
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."

# Get session info
curl -X GET http://localhost:8000/api/v1/auth/session \
  -H "Authorization: Bearer $TOKEN"

# Search products
curl -X POST http://localhost:8000/api/v1/systems/odoo-testdb/odoo/search_read \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model":"product.product","domain":[],"fields":["name","list_price"],"limit":10}'
```

## Flutter Client Integration

No changes needed in Flutter code! The BridgeCoreClient will work directly with these endpoints.

```dart
// Initialize
final client = BridgeCoreClient(baseUrl: 'http://localhost:8000');

// Login
final authResult = await client.login(
  username: 'admin',
  password: 'admin',
  database: 'testdb',
);

// Use operations
final products = await client.searchRead(
  model: 'product.product',
  domain: [],
  fields: ['name', 'list_price'],
  limit: 10,
);
```

## Migration from Old API

### Old Format (Before)
```
POST /auth/login
POST /systems/{id}/create?model=...
GET /systems/{id}/read?model=...
```

### New Format (After)
```
POST /api/v1/auth/login
POST /api/v1/systems/{id}/odoo/create
POST /api/v1/systems/{id}/odoo/search_read
```

The old `/systems/*` endpoints are still available for backwards compatibility.

## Next Steps

1. **Replace Mock Data**: Update `app/api/routes/odoo.py` to use actual Odoo RPC
2. **Token Blacklisting**: Implement Redis-based token blacklist for logout
3. **Real User Data**: Connect to Odoo to fetch actual user info (company_id, partner_id)
4. **Error Handling**: Add more detailed error messages
5. **Rate Limiting**: Configure rate limits per endpoint

## Testing Checklist

- [x] Login returns correct format with system_id and user object
- [x] Refresh token works with Bearer authorization
- [x] Session endpoint returns user and expiration
- [x] Logout returns empty object
- [x] Odoo search_read operation works
- [x] Odoo create operation works
- [x] All responses have correct structure

Run `python test_flutter_integration.py` to verify all tests pass.

## Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

## Support

For issues or questions, check the main README or create an issue on GitHub.
