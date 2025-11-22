# BridgeCore API Documentation

## Overview

BridgeCore provides two main API categories:
1. **Admin API** (`/admin/*`) - For platform administrators to manage tenants
2. **Tenant API** (`/api/v1/*`, `/api/v2/*`) - For tenant applications to interact with Odoo

### Interactive Documentation

BridgeCore automatically generates interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

---

## Authentication

### Admin Authentication

Admin users authenticate using email/password and receive a JWT token.

```bash
POST /admin/auth/login
Content-Type: application/json

{
    "email": "admin@bridgecore.local",
    "password": "your_password"
}
```

**Response:**
```json
{
    "admin": {
        "id": "uuid",
        "email": "admin@bridgecore.local",
        "full_name": "Admin User",
        "role": "super_admin",
        "is_active": true
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Using the Token:**
```bash
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Tenant Authentication

Tenant users authenticate against their Odoo instance.

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
    "username": "user@company.com",
    "password": "odoo_password",
    "database": "company_database"
}
```

**Response:**
```json
{
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
        "id": 1,
        "username": "user@company.com",
        "name": "User Name",
        "company_id": 1,
        "partner_id": 3
    }
}
```

---

## Admin API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/admin/auth/login` | Admin login |
| POST | `/admin/auth/logout` | Admin logout |
| GET | `/admin/auth/me` | Get current admin info |

### Tenant Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/tenants` | List all tenants |
| POST | `/admin/tenants` | Create new tenant |
| GET | `/admin/tenants/{id}` | Get tenant details |
| PUT | `/admin/tenants/{id}` | Update tenant |
| DELETE | `/admin/tenants/{id}` | Delete tenant (soft) |
| POST | `/admin/tenants/{id}/suspend` | Suspend tenant |
| POST | `/admin/tenants/{id}/activate` | Activate tenant |
| POST | `/admin/tenants/{id}/test-connection` | Test Odoo connection |
| GET | `/admin/tenants/statistics` | Get tenant statistics |

#### Create Tenant

```bash
POST /admin/tenants
Authorization: Bearer {admin_token}
Content-Type: application/json

{
    "name": "Acme Corporation",
    "slug": "acme-corp",
    "description": "Main corporate tenant",
    "contact_email": "contact@acme.com",
    "contact_phone": "+1234567890",
    "odoo_url": "https://acme.odoo.com",
    "odoo_database": "acme_prod",
    "odoo_version": "17.0",
    "odoo_username": "api_user",
    "odoo_password": "secure_password",
    "plan_id": "uuid-of-plan",
    "max_requests_per_day": 10000,
    "max_requests_per_hour": 1000,
    "allowed_models": ["res.partner", "sale.order", "product.product"],
    "allowed_features": ["sync", "webhooks", "analytics"]
}
```

**Response:**
```json
{
    "id": "uuid",
    "name": "Acme Corporation",
    "slug": "acme-corp",
    "status": "trial",
    "odoo_url": "https://acme.odoo.com",
    "odoo_database": "acme_prod",
    "created_at": "2025-11-21T10:00:00Z",
    ...
}
```

#### List Tenants with Filters

```bash
GET /admin/tenants?status=active&skip=0&limit=50
Authorization: Bearer {admin_token}
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| status | string | Filter by status (active, trial, suspended, deleted) |
| skip | integer | Pagination offset (default: 0) |
| limit | integer | Items per page (default: 100, max: 1000) |

### Plans Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/plans` | List all plans |
| GET | `/admin/plans/{id}` | Get plan details |

### Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/analytics/overview` | System-wide overview |
| GET | `/admin/analytics/top-tenants` | Top tenants by usage |
| GET | `/admin/analytics/tenants/{id}` | Tenant-specific analytics |
| GET | `/admin/analytics/tenants/{id}/daily` | Daily statistics |

#### System Overview

```bash
GET /admin/analytics/overview
Authorization: Bearer {admin_token}
```

**Response:**
```json
{
    "tenants": {
        "total": 50,
        "active": 42,
        "trial": 5,
        "suspended": 3
    },
    "usage_24h": {
        "total_requests": 125000,
        "successful_requests": 122500,
        "success_rate_percent": 98.0,
        "avg_response_time_ms": 245,
        "total_data_transferred_mb": 1250.5
    }
}
```

#### Top Tenants

```bash
GET /admin/analytics/top-tenants?limit=10&days=7
Authorization: Bearer {admin_token}
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| limit | integer | Number of tenants (default: 10) |
| days | integer | Time period in days (default: 7) |

### Logs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/logs/usage` | Get usage logs |
| GET | `/admin/logs/usage/summary` | Usage summary |
| GET | `/admin/logs/errors` | Get error logs |
| GET | `/admin/logs/errors/summary` | Error summary |
| POST | `/admin/logs/errors/{id}/resolve` | Resolve an error |

#### Get Usage Logs

```bash
GET /admin/logs/usage?tenant_id={id}&method=POST&status_code=200&limit=100
Authorization: Bearer {admin_token}
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| tenant_id | uuid | Filter by tenant |
| method | string | HTTP method (GET, POST, PUT, DELETE) |
| status_code | integer | HTTP status code |
| start_date | datetime | Start of date range (ISO 8601) |
| end_date | datetime | End of date range (ISO 8601) |
| skip | integer | Pagination offset |
| limit | integer | Items per page |

#### Resolve Error

```bash
POST /admin/logs/errors/{error_id}/resolve
Authorization: Bearer {admin_token}
Content-Type: application/json

{
    "resolution_notes": "Fixed by updating the configuration in Odoo"
}
```

---

## Tenant API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/tenant/login` | Tenant user login (NEW) |
| POST | `/api/v1/auth/login` | Legacy login (deprecated) |
| POST | `/api/v1/auth/logout` | User logout |
| POST | `/api/v1/auth/refresh` | Refresh token |
| GET | `/api/v1/auth/me` | Get current user |

**Note:** The new tenant-based authentication endpoint `/api/v1/auth/tenant/login` is recommended. The legacy `/api/v1/auth/login` endpoint is deprecated and will be removed in a future version.

#### Tenant User Login (NEW)

```bash
POST /api/v1/auth/tenant/login
Content-Type: application/json

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

### Odoo Operations

**Important:** All Odoo operations use tenant JWT tokens. Odoo credentials are automatically fetched from tenant database - **NO credentials needed in requests!**

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/odoo/search_read` | Search and read records |
| POST | `/api/v1/odoo/read` | Read specific records by IDs |
| POST | `/api/v1/odoo/create` | Create record |
| POST | `/api/v1/odoo/write` | Update records |
| POST | `/api/v1/odoo/unlink` | Delete records |
| POST | `/api/v1/odoo/search_count` | Count matching records |
| POST | `/api/v1/odoo/search` | Search for record IDs only |
| POST | `/api/v1/odoo/fields_get` | Get model field definitions |
| POST | `/api/v1/odoo/call_kw` | Call any Odoo method |
| GET | `/api/v1/odoo/models` | List available models |
| GET | `/api/v1/odoo/cache/stats` | Get cache statistics |
| DELETE | `/api/v1/odoo/cache/clear` | Clear cache |

#### Search and Read

```bash
POST /api/v1/odoo/search_read
Authorization: Bearer {tenant_token}
Content-Type: application/json

{
    "model": "res.partner",
    "domain": [
        ["customer_rank", ">", 0],
        ["active", "=", true]
    ],
    "fields": ["id", "name", "email", "phone", "city"],
    "limit": 100,
    "offset": 0,
    "order": "name ASC"
}
```

**Response:**
```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "name": "Customer A",
            "email": "a@example.com",
            "phone": "+1234567890",
            "city": "New York"
        },
        ...
    ],
    "count": 100,
    "total": 1250
}
```

#### Create Record

```bash
POST /api/v1/odoo/create
Authorization: Bearer {tenant_token}
Content-Type: application/json

{
    "model": "res.partner",
    "values": {
        "name": "New Customer",
        "email": "new@example.com",
        "phone": "+1234567890",
        "customer_rank": 1
    }
}
```

**Response:**
```json
{
    "success": true,
    "id": 123
}
```

#### Update Records

```bash
POST /api/v1/odoo/write
Authorization: Bearer {tenant_token}
Content-Type: application/json

{
    "model": "res.partner",
    "ids": [123, 124, 125],
    "values": {
        "phone": "+0987654321",
        "city": "Los Angeles"
    }
}
```

#### Delete Records

```bash
POST /api/v1/odoo/unlink
Authorization: Bearer {tenant_token}
Content-Type: application/json

{
    "model": "res.partner",
    "ids": [123, 124]
}
```

### Webhook System (v1)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/webhooks/check-updates` | Check for new updates |
| GET | `/api/v1/webhooks/events` | List webhook events |
| POST | `/api/v1/webhooks/push` | Receive push from Odoo |

#### Check for Updates

```bash
GET /api/v1/webhooks/check-updates?limit=50
Authorization: Bearer {tenant_token}
```

**Response:**
```json
{
    "has_update": true,
    "last_update_at": "2025-11-21T10:30:00Z",
    "summary": [
        {"model": "sale.order", "count": 15},
        {"model": "res.partner", "count": 8}
    ]
}
```

### Smart Sync (v2)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v2/sync/pull` | Pull new changes |
| GET | `/api/v2/sync/state` | Get sync state |
| POST | `/api/v2/sync/reset` | Reset sync state |

#### Smart Sync Pull

```bash
POST /api/v2/sync/pull
Authorization: Bearer {tenant_token}
Content-Type: application/json

{
    "user_id": 1,
    "device_id": "device_abc123",
    "app_type": "sales_app",
    "limit": 100
}
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
            "timestamp": "2025-11-21T10:30:00Z",
            "changed_fields": ["state", "amount_total"]
        }
    ],
    "next_sync_token": "1234",
    "last_sync_time": "2025-11-21T10:30:00Z"
}
```

---

## Error Handling

### Error Response Format

All API errors follow this format:

```json
{
    "detail": "Error message describing what went wrong",
    "error_code": "ERROR_CODE",
    "timestamp": "2025-11-21T10:30:00Z"
}
```

### Common HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid or missing token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

### Rate Limiting

When rate limit is exceeded:

```json
{
    "detail": "Rate limit exceeded. Try again in 3600 seconds.",
    "error_code": "RATE_LIMIT_EXCEEDED",
    "retry_after": 3600
}
```

**Rate Limit Headers:**
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1700564400
```

---

## Pagination

List endpoints support pagination:

```bash
GET /admin/tenants?skip=0&limit=50
```

**Response includes pagination info:**
```json
{
    "items": [...],
    "total": 150,
    "skip": 0,
    "limit": 50,
    "has_more": true
}
```

---

## Filtering

### Domain Syntax (Odoo-style)

For Odoo operations, use domain syntax:

```json
{
    "domain": [
        ["field", "operator", "value"],
        ["field2", "operator", "value2"]
    ]
}
```

**Operators:**
| Operator | Description |
|----------|-------------|
| `=` | Equals |
| `!=` | Not equals |
| `>` | Greater than |
| `>=` | Greater than or equal |
| `<` | Less than |
| `<=` | Less than or equal |
| `like` | Pattern match (% wildcards) |
| `ilike` | Case-insensitive pattern match |
| `in` | In list |
| `not in` | Not in list |
| `child_of` | Child of (hierarchy) |

**Example:**
```json
{
    "domain": [
        ["state", "=", "sale"],
        ["amount_total", ">", 1000],
        ["partner_id.country_id.code", "=", "US"]
    ]
}
```

---

## Webhooks Configuration

### Odoo Module Setup

Install `auto-webhook-odoo` module in your Odoo instance:

```bash
git clone https://github.com/geniustep/auto-webhook-odoo.git
cp -r auto-webhook-odoo /path/to/odoo/addons/auto_webhook
```

### Configure Webhook Endpoint

In Odoo, configure the webhook to push to:
```
POST https://your-bridgecore.com/api/v1/webhooks/push
```

---

## SDK Examples

### Python

```python
import requests

# Admin Login
response = requests.post(
    "http://localhost:8000/admin/auth/login",
    json={"email": "admin@bridgecore.local", "password": "admin123"}
)
token = response.json()["token"]

# List Tenants
headers = {"Authorization": f"Bearer {token}"}
tenants = requests.get(
    "http://localhost:8000/admin/tenants",
    headers=headers
).json()
```

### JavaScript/TypeScript

```typescript
// Admin Login
const loginResponse = await fetch('http://localhost:8000/admin/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        email: 'admin@bridgecore.local',
        password: 'admin123'
    })
});
const { token } = await loginResponse.json();

// List Tenants
const tenantsResponse = await fetch('http://localhost:8000/admin/tenants', {
    headers: { 'Authorization': `Bearer ${token}` }
});
const tenants = await tenantsResponse.json();
```

### cURL

```bash
# Admin Login
TOKEN=$(curl -s -X POST http://localhost:8000/admin/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@bridgecore.local","password":"admin123"}' \
    | jq -r '.token')

# List Tenants
curl -X GET http://localhost:8000/admin/tenants \
    -H "Authorization: Bearer $TOKEN"
```

---

## Versioning

The API uses URL versioning:
- `/api/v1/*` - Version 1 (current stable)
- `/api/v2/*` - Version 2 (Smart Sync features)
- `/admin/*` - Admin API (no version prefix)

Deprecated endpoints will include a `Deprecation` header with the sunset date.
