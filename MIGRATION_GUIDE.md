# Migration Guide: Legacy API to Tenant-Based API

## Overview

BridgeCore has been updated to use a tenant-based architecture. This guide helps you migrate from the legacy API to the new tenant-based API.

## Key Changes

### 1. Authentication

#### Old (Legacy - Deprecated)
```http
POST /api/v1/auth/login
{
  "username": "admin",
  "password": "admin123",
  "database": "testdb"
}
```

#### New (Tenant-Based)
```http
POST /api/v1/auth/tenant/login
{
  "email": "user@company.com",
  "password": "password123"
}
```

**Changes:**
- ✅ Endpoint changed: `/auth/login` → `/auth/tenant/login`
- ✅ Field changed: `username` → `email`
- ✅ Removed: `database` field (tenant determined from user)
- ✅ Response includes: `tenant` object with tenant information

### 2. Odoo Operations Endpoint

#### Old (Legacy - Deprecated)
```http
POST /api/v1/systems/{system_id}/odoo/{operation}
Authorization: Bearer {legacy_token}
{
  "model": "res.partner",
  "domain": [],
  "fields": ["name", "email"]
}
```

#### New (Tenant-Based)
```http
POST /api/v1/odoo/{operation}
Authorization: Bearer {tenant_token}
{
  "model": "res.partner",
  "domain": [],
  "fields": ["name", "email"]
}
```

**Changes:**
- ✅ **Removed `system_id`** from URL path
- ✅ **No Odoo credentials** needed in request
- ✅ **Tenant context** extracted automatically from JWT token
- ✅ **Odoo credentials** fetched from tenant database automatically

### 3. Token Structure

#### Old Token (Legacy)
```json
{
  "sub": "username",
  "user_id": 1,
  "type": "access"
}
```

#### New Token (Tenant)
```json
{
  "sub": "user_uuid",
  "tenant_id": "tenant_uuid",
  "email": "user@company.com",
  "role": "user",
  "user_type": "tenant",
  "type": "access"
}
```

## Step-by-Step Migration

### Step 1: Update Authentication

**Before:**
```javascript
// Old authentication
const response = await fetch('http://localhost:8001/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'admin',
    password: 'admin123',
    database: 'testdb'
  })
});

const { access_token, system_id } = await response.json();
```

**After:**
```javascript
// New tenant-based authentication
const response = await fetch('http://localhost:8001/api/v1/auth/tenant/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@company.com',
    password: 'password123'
  })
});

const { access_token, tenant } = await response.json();
// tenant.id, tenant.name, tenant.slug available
```

### Step 2: Update API Calls

**Before:**
```javascript
// Old endpoint with system_id
const response = await fetch(
  `http://localhost:8001/api/v1/systems/${system_id}/odoo/search_read`,
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${access_token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model: 'res.partner',
      domain: [],
      fields: ['name', 'email'],
      limit: 10
    })
  }
);
```

**After:**
```javascript
// New endpoint without system_id
const response = await fetch(
  'http://localhost:8001/api/v1/odoo/search_read',
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${access_token}`, // tenant token
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model: 'res.partner',
      domain: [],
      fields: ['name', 'email'],
      limit: 10
    })
  }
);
```

### Step 3: Remove Odoo Credentials

**Before:**
```javascript
// Old - might have sent Odoo credentials (if any)
const response = await fetch(
  `http://localhost:8001/api/v1/systems/${system_id}/odoo/search_read`,
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${access_token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      // Odoo credentials might have been here
      model: 'res.partner',
      // ...
    })
  }
);
```

**After:**
```javascript
// New - NO credentials needed!
const response = await fetch(
  'http://localhost:8001/api/v1/odoo/search_read',
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${access_token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      // NO Odoo credentials - fetched automatically!
      model: 'res.partner',
      // ...
    })
  }
);
```

## Code Examples

### Flutter/Dart

**Before:**
```dart
// Old authentication
final loginResponse = await http.post(
  Uri.parse('http://localhost:8001/api/v1/auth/login'),
  headers: {'Content-Type': 'application/json'},
  body: jsonEncode({
    'username': 'admin',
    'password': 'admin123',
    'database': 'testdb',
  }),
);

final data = jsonDecode(loginResponse.body);
final accessToken = data['access_token'];
final systemId = data['system_id'];

// Old API call
final response = await http.post(
  Uri.parse('http://localhost:8001/api/v1/systems/$systemId/odoo/search_read'),
  headers: {
    'Authorization': 'Bearer $accessToken',
    'Content-Type': 'application/json',
  },
  body: jsonEncode({
    'model': 'res.partner',
    'limit': 10,
  }),
);
```

**After:**
```dart
// New tenant-based authentication
final loginResponse = await http.post(
  Uri.parse('http://localhost:8001/api/v1/auth/tenant/login'),
  headers: {'Content-Type': 'application/json'},
  body: jsonEncode({
    'email': 'user@company.com',
    'password': 'password123',
  }),
);

final data = jsonDecode(loginResponse.body);
final accessToken = data['access_token'];
final tenant = data['tenant'];

// New API call - no system_id needed!
final response = await http.post(
  Uri.parse('http://localhost:8001/api/v1/odoo/search_read'),
  headers: {
    'Authorization': 'Bearer $accessToken',
    'Content-Type': 'application/json',
  },
  body: jsonEncode({
    'model': 'res.partner',
    'limit': 10,
  }),
);
```

### Python

**Before:**
```python
# Old authentication
import requests

login_response = requests.post(
    'http://localhost:8001/api/v1/auth/login',
    json={
        'username': 'admin',
        'password': 'admin123',
        'database': 'testdb'
    }
)
data = login_response.json()
access_token = data['access_token']
system_id = data['system_id']

# Old API call
response = requests.post(
    f'http://localhost:8001/api/v1/systems/{system_id}/odoo/search_read',
    headers={'Authorization': f'Bearer {access_token}'},
    json={'model': 'res.partner', 'limit': 10}
)
```

**After:**
```python
# New tenant-based authentication
import requests

login_response = requests.post(
    'http://localhost:8001/api/v1/auth/tenant/login',
    json={
        'email': 'user@company.com',
        'password': 'password123'
    }
)
data = login_response.json()
access_token = data['access_token']
tenant = data['tenant']

# New API call - no system_id needed!
response = requests.post(
    'http://localhost:8001/api/v1/odoo/search_read',
    headers={'Authorization': f'Bearer {access_token}'},
    json={'model': 'res.partner', 'limit': 10}
)
```

### JavaScript/TypeScript

**Before:**
```typescript
// Old authentication
const loginResponse = await fetch('http://localhost:8001/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'admin',
    password: 'admin123',
    database: 'testdb'
  })
});

const { access_token, system_id } = await loginResponse.json();

// Old API call
const response = await fetch(
  `http://localhost:8001/api/v1/systems/${system_id}/odoo/search_read`,
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${access_token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model: 'res.partner',
      limit: 10
    })
  }
);
```

**After:**
```typescript
// New tenant-based authentication
const loginResponse = await fetch('http://localhost:8001/api/v1/auth/tenant/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@company.com',
    password: 'password123'
  })
});

const { access_token, tenant } = await loginResponse.json();

// New API call - no system_id needed!
const response = await fetch(
  'http://localhost:8001/api/v1/odoo/search_read',
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${access_token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model: 'res.partner',
      limit: 10
    })
  }
);
```

## Breaking Changes Summary

| Aspect | Old (Legacy) | New (Tenant-Based) |
|--------|--------------|---------------------|
| **Login Endpoint** | `/api/v1/auth/login` | `/api/v1/auth/tenant/login` |
| **Login Fields** | `username`, `password`, `database` | `email`, `password` |
| **Odoo Endpoint** | `/api/v1/systems/{system_id}/odoo/{operation}` | `/api/v1/odoo/{operation}` |
| **System ID** | Required in URL | Not needed (from token) |
| **Odoo Credentials** | May have been in request | Never needed (from database) |
| **Token Type** | Legacy token | Tenant JWT token |
| **Response** | Includes `system_id` | Includes `tenant` object |

## Backward Compatibility

The legacy endpoint `/api/v1/auth/login` is still available but **deprecated**. It will be removed in a future version. Please migrate to the new tenant-based API as soon as possible.

## Testing Migration

1. **Test Authentication:**
   ```bash
   curl -X POST "http://localhost:8001/api/v1/auth/tenant/login" \
     -H "Content-Type: application/json" \
     -d '{"email":"user@company.com","password":"password123"}'
   ```

2. **Test Odoo Operation:**
   ```bash
   TOKEN="your_tenant_token"
   curl -X POST "http://localhost:8001/api/v1/odoo/search_read" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"model":"res.partner","limit":10}'
   ```

## Support

If you encounter issues during migration:
- Check [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for complete API reference
- Review error messages - they include helpful details
- Contact support: support@bridgecore.com

