# BridgeCore API Documentation

## Overview

BridgeCore provides a tenant-based API for interacting with Odoo ERP systems. All endpoints use JWT authentication with tenant context automatically extracted from the token.

## Base URL

```
http://localhost:8001  # Development
https://api.bridgecore.com  # Production
```

## Authentication

### Tenant User Login

**Endpoint:** `POST /api/v1/auth/tenant/login`

**Request:**
```json
{
  "email": "user@company.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "uuid",
    "email": "user@company.com",
    "full_name": "User Name",
    "role": "user"
  },
  "tenant": {
    "id": "uuid",
    "name": "Company Name",
    "slug": "company-slug",
    "status": "active"
  }
}
```

### Refresh Token

**Endpoint:** `POST /api/v1/auth/tenant/refresh`

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Logout

**Endpoint:** `POST /api/v1/auth/tenant/logout`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "message": "Logged out successfully"
}
```

---

## Odoo Operations

All Odoo operations use the unified endpoint: `/api/v1/odoo/{operation}`

**Important:** 
- ✅ **NO `system_id` needed** - Tenant is extracted from JWT token
- ✅ **NO Odoo credentials needed** - Automatically fetched from tenant database
- ✅ **Secure** - Tenant credentials are encrypted and never exposed

### Common Headers

All Odoo operation requests require:
```
Authorization: Bearer {tenant_access_token}
Content-Type: application/json
```

### Search Read

**Endpoint:** `POST /api/v1/odoo/search_read`

**Request:**
```json
{
  "model": "res.partner",
  "domain": [["is_company", "=", true]],
  "fields": ["name", "email", "phone"],
  "limit": 10,
  "offset": 0,
  "order": "name ASC"
}
```

**Response:**
```json
{
  "result": [
    {
      "id": 1,
      "name": "Company A",
      "email": "info@company-a.com",
      "phone": "+1234567890"
    },
    {
      "id": 2,
      "name": "Company B",
      "email": "info@company-b.com",
      "phone": "+0987654321"
    }
  ],
  "cached": false,
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Read

**Endpoint:** `POST /api/v1/odoo/read`

**Request:**
```json
{
  "model": "res.partner",
  "ids": [1, 2, 3],
  "fields": ["name", "email", "phone"]
}
```

**Response:**
```json
{
  "result": [
    {
      "id": 1,
      "name": "Company A",
      "email": "info@company-a.com",
      "phone": "+1234567890"
    }
  ],
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Create

**Endpoint:** `POST /api/v1/odoo/create`

**Request:**
```json
{
  "model": "res.partner",
  "values": {
    "name": "New Company",
    "email": "new@company.com",
    "phone": "+1234567890",
    "is_company": true
  }
}
```

**Response:**
```json
{
  "result": 123,
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Write (Update)

**Endpoint:** `POST /api/v1/odoo/write`

**Request:**
```json
{
  "model": "res.partner",
  "ids": [123],
  "values": {
    "email": "updated@company.com",
    "phone": "+9876543210"
  }
}
```

**Response:**
```json
{
  "result": true,
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Unlink (Delete)

**Endpoint:** `POST /api/v1/odoo/unlink`

**Request:**
```json
{
  "model": "res.partner",
  "ids": [123, 124]
}
```

**Response:**
```json
{
  "result": true,
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Search Count

**Endpoint:** `POST /api/v1/odoo/search_count`

**Request:**
```json
{
  "model": "res.partner",
  "domain": [["is_company", "=", true]]
}
```

**Response:**
```json
{
  "result": 42,
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Fields Get

**Endpoint:** `POST /api/v1/odoo/fields_get`

**Request:**
```json
{
  "model": "res.partner",
  "fields": ["name", "email", "phone"]
}
```

**Response:**
```json
{
  "result": {
    "name": {
      "type": "char",
      "string": "Name",
      "required": true
    },
    "email": {
      "type": "char",
      "string": "Email"
    },
    "phone": {
      "type": "char",
      "string": "Phone"
    }
  },
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Search

**Endpoint:** `POST /api/v1/odoo/search`

**Request:**
```json
{
  "model": "res.partner",
  "domain": [["is_company", "=", true]],
  "limit": 10,
  "offset": 0
}
```

**Response:**
```json
{
  "result": [1, 2, 3, 4, 5],
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Call KW (Custom Method)

**Endpoint:** `POST /api/v1/odoo/call_kw`

**Request:**
```json
{
  "model": "sale.order",
  "method": "action_confirm",
  "args": [[123]],
  "kwargs": {}
}
```

**Response:**
```json
{
  "result": true,
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## Helper Endpoints

### Get Available Models

**Endpoint:** `GET /api/v1/odoo/models`

**Headers:**
```
Authorization: Bearer {tenant_access_token}
```

**Response:**
```json
{
  "result": [
    {"model": "res.partner", "name": "Contact"},
    {"model": "product.product", "name": "Product"},
    {"model": "sale.order", "name": "Sales Order"},
    {"model": "account.move", "name": "Invoice"},
    {"model": "stock.picking", "name": "Transfer"}
  ],
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
  "tenant_name": "Company Name"
}
```

### Get Cache Statistics

**Endpoint:** `GET /api/v1/odoo/cache/stats`

**Headers:**
```
Authorization: Bearer {tenant_access_token}
```

**Response:**
```json
{
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
  "tenant_name": "Company Name",
  "cache_stats": {
    "total_keys": 150,
    "hit_rate_percent": 85.5,
    "total_hits": 1200,
    "total_misses": 200
  }
}
```

### Clear Cache

**Endpoint:** `DELETE /api/v1/odoo/cache/clear`

**Query Parameters:**
- `model` (optional): Clear cache for specific model only

**Headers:**
```
Authorization: Bearer {tenant_access_token}
```

**Response:**
```json
{
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
  "tenant_name": "Company Name",
  "model": "res.partner",
  "deleted_keys": 25,
  "message": "Cleared 25 cache entries"
}
```

---

## Supported Operations

| Operation | Description | Method |
|-----------|-------------|--------|
| `search_read` | Search and read records | POST |
| `read` | Read specific records by IDs | POST |
| `create` | Create new record | POST |
| `write` | Update existing records | POST |
| `unlink` | Delete records | POST |
| `search` | Search for record IDs only | POST |
| `search_count` | Count matching records | POST |
| `fields_get` | Get model field definitions | POST |
| `name_search` | Search by name | POST |
| `name_get` | Get display names | POST |
| `web_search_read` | Web search read (Odoo 14+) | POST |
| `web_read` | Web read (Odoo 14+) | POST |
| `web_save` | Web save (Odoo 14+) | POST |
| `call_kw` | Call any Odoo method | POST |

---

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Tenant information not found. Are you using a valid tenant token?"
}
```

### 403 Forbidden
```json
{
  "detail": "Tenant account is suspended. Please contact support."
}
```

### 404 Not Found
```json
{
  "detail": "Tenant not found"
}
```

### 400 Bad Request
```json
{
  "detail": "Invalid operation: invalid_op. Must be one of [search_read, read, create, ...]"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Operation failed: Connection timeout"
}
```

---

## Example cURL Requests

### 1. Login
```bash
curl -X POST "http://localhost:8001/api/v1/auth/tenant/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@company.com",
    "password": "password123"
  }'
```

### 2. Search Read
```bash
TOKEN="your_access_token_here"

curl -X POST "http://localhost:8001/api/v1/odoo/search_read" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "res.partner",
    "domain": [["is_company", "=", true]],
    "fields": ["name", "email"],
    "limit": 10
  }'
```

### 3. Create Record
```bash
curl -X POST "http://localhost:8001/api/v1/odoo/create" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "res.partner",
    "values": {
      "name": "New Company",
      "email": "new@company.com"
    }
  }'
```

---

## Migration from Legacy API

### Old Endpoint (Deprecated)
```
POST /api/v1/systems/{system_id}/odoo/{operation}
```

### New Endpoint
```
POST /api/v1/odoo/{operation}
```

### Changes
1. ✅ **Removed `system_id`** from URL path
2. ✅ **Removed Odoo credentials** from request body
3. ✅ **Use Tenant JWT token** instead of legacy token
4. ✅ **Tenant context** extracted automatically from token

### Migration Steps

1. **Update Authentication:**
   ```javascript
   // Old
   POST /api/v1/auth/login
   { "username": "...", "password": "...", "database": "..." }
   
   // New
   POST /api/v1/auth/tenant/login
   { "email": "...", "password": "..." }
   ```

2. **Update API Calls:**
   ```javascript
   // Old
   POST /api/v1/systems/odoo-prod/odoo/search_read
   
   // New
   POST /api/v1/odoo/search_read
   ```

3. **Remove Credentials:**
   ```javascript
   // Old - Don't send Odoo credentials
   // New - Credentials fetched automatically from tenant database
   ```

---

## Rate Limiting

Each tenant has configurable rate limits:
- **Per Hour**: Default 1000 requests/hour
- **Per Day**: Default 10000 requests/day

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1234567890
```

When limit is exceeded:
```json
{
  "detail": "Rate limit exceeded. Please try again later."
}
```

---

## Caching

Read operations are automatically cached:
- **Cache TTL**: 5 minutes (default)
- **Cache Key**: Based on tenant, operation, model, domain, fields
- **Cache Invalidation**: Automatic on write operations

Response includes cache status:
```json
{
  "result": [...],
  "cached": true,
  "tenant_id": "..."
}
```

---

## WebSocket Updates

Real-time updates are broadcast via WebSocket when records are created/updated/deleted:
- **Channel**: `tenant:{tenant_id}:{model}:{record_id}`
- **Events**: `create`, `write`, `unlink`

---

## Best Practices

1. **Always use Tenant JWT tokens** - Never use legacy tokens
2. **Handle token expiration** - Implement refresh token logic
3. **Use appropriate limits** - Don't request more than needed
4. **Cache responses** - Check `cached` flag in responses
5. **Handle errors gracefully** - Check status codes and error messages
6. **Monitor rate limits** - Check rate limit headers

---

## Support

For issues or questions:
- **Email**: support@bridgecore.com
- **Documentation**: https://docs.bridgecore.com
- **API Docs**: http://localhost:8001/docs (Swagger UI)

