# 📖 BridgeCore Usage Guide

Complete guide for using BridgeCore in your applications.

## Table of Contents

- [Getting Started](#getting-started)
- [Authentication](#authentication)
- [Tenant Operations](#tenant-operations)
- [Odoo Operations](#odoo-operations)
- [Webhook System](#webhook-system)
- [Smart Sync](#smart-sync)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)

---

## Getting Started

### Prerequisites

Before using BridgeCore, ensure you have:
- BridgeCore instance running (see [QUICK_START.md](./QUICK_START.md))
- Tenant account created by admin
- User credentials (email and password)

### Base URL

```
Production: https://api.bridgecore.com
Development: http://localhost:8000
```

---

## Authentication

### Login

```bash
curl -X POST https://api.bridgecore.com/api/v1/auth/tenant/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@company.com",
    "password": "your_password"
  }'
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "uuid",
    "email": "user@company.com",
    "full_name": "John Doe",
    "role": "user",
    "odoo_user_id": 6
  },
  "tenant": {
    "id": "uuid",
    "name": "Company Name",
    "slug": "company-slug",
    "status": "active",
    "odoo_url": "https://company.odoo.com",
    "odoo_database": "company_db",
    "odoo_version": "18.0"
  }
}
```

### Get Current User Info

```bash
curl -X POST https://api.bridgecore.com/api/v1/auth/tenant/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

**Response:**
```json
{
  "user": {...},
  "tenant": {...},
  "partner_id": 7,
  "employee_id": null,
  "groups": ["base.group_user", "sales.group_sale_user"],
  "is_admin": false,
  "is_internal_user": true,
  "company_ids": [1],
  "current_company_id": 1,
  "odoo_fields_data": null
}
```

### Refresh Token

```bash
curl -X POST https://api.bridgecore.com/api/v1/auth/tenant/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

---

## Tenant Operations

### List Tenants (Admin Only)

```bash
curl -X GET "https://api.bridgecore.com/admin/tenants?status=active&limit=100" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### Create Tenant (Admin Only)

```bash
curl -X POST https://api.bridgecore.com/admin/tenants \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Company",
    "slug": "new-company",
    "contact_email": "admin@newcompany.com",
    "odoo_url": "https://newcompany.odoo.com",
    "odoo_database": "newcompany_db",
    "odoo_username": "api_user",
    "odoo_password": "secure_password",
    "plan_id": "uuid",
    "max_users": 50
  }'
```

### Test Connection (Admin Only)

```bash
curl -X POST https://api.bridgecore.com/admin/tenants/TENANT_ID/test-connection \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

---

## Odoo Operations

### Search & Read

```bash
curl -X POST https://api.bridgecore.com/api/v1/odoo/search_read \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "res.partner",
    "domain": [["customer_rank", ">", 0]],
    "fields": ["id", "name", "email", "phone"],
    "limit": 100,
    "offset": 0,
    "order": "name ASC"
  }'
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Customer A",
    "email": "customer.a@example.com",
    "phone": "+1234567890"
  },
  {
    "id": 2,
    "name": "Customer B",
    "email": "customer.b@example.com",
    "phone": "+0987654321"
  }
]
```

### Create Record

```bash
curl -X POST https://api.bridgecore.com/api/v1/odoo/create \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "res.partner",
    "values": {
      "name": "New Customer",
      "email": "new@example.com",
      "phone": "+1111111111",
      "is_company": false
    }
  }'
```

**Response:**
```json
{
  "id": 123,
  "success": true
}
```

### Update Record

```bash
curl -X POST https://api.bridgecore.com/api/v1/odoo/write \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "res.partner",
    "ids": [123],
    "values": {
      "phone": "+2222222222",
      "mobile": "+3333333333"
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "updated_count": 1
}
```

### Delete Record

```bash
curl -X POST https://api.bridgecore.com/api/v1/odoo/unlink \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "res.partner",
    "ids": [123]
  }'
```

**Response:**
```json
{
  "success": true,
  "deleted_count": 1
}
```

### Call Odoo Method

```bash
curl -X POST https://api.bridgecore.com/api/v1/odoo/call \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "sale.order",
    "method": "action_confirm",
    "args": [[1, 2, 3]],
    "kwargs": {}
  }'
```

---

## Webhook System

### Check for Updates

```bash
curl -X GET "https://api.bridgecore.com/api/v1/webhooks/check-updates?limit=50" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
{
  "has_updates": true,
  "events_count": 25,
  "events": [
    {
      "id": "uuid",
      "model": "sale.order",
      "event": "write",
      "record_id": 123,
      "timestamp": "2025-11-22T10:30:00Z",
      "data": {
        "id": 123,
        "name": "SO001",
        "state": "sale"
      }
    }
  ]
}
```

### List Events

```bash
curl -X GET "https://api.bridgecore.com/api/v1/webhooks/events?model=sale.order&limit=100" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Mark Events as Processed

```bash
curl -X POST https://api.bridgecore.com/api/v1/webhooks/events/mark-processed \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_ids": ["uuid1", "uuid2", "uuid3"]
  }'
```

---

## Smart Sync

### Pull Updates

```bash
curl -X POST https://api.bridgecore.com/api/v2/sync/pull \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "device_id": "device_123",
    "app_type": "sales_app",
    "limit": 100,
    "models": ["sale.order", "res.partner"]
  }'
```

**Response:**
```json
{
  "has_updates": true,
  "new_events_count": 25,
  "events": [...],
  "next_sync_token": "1234",
  "last_sync_time": "2025-11-22T10:30:00Z",
  "sync_state": {
    "user_id": 1,
    "device_id": "device_123",
    "last_event_id": "uuid",
    "last_sync_time": "2025-11-22T10:30:00Z"
  }
}
```

### Get Sync State

```bash
curl -X GET "https://api.bridgecore.com/api/v2/sync/state?user_id=1&device_id=device_123" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Reset Sync State

```bash
curl -X POST "https://api.bridgecore.com/api/v2/sync/reset?user_id=1&device_id=device_123" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Error Handling

### Common Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| 400 | Bad Request | Check request format |
| 401 | Unauthorized | Check access token |
| 403 | Forbidden | Check permissions |
| 404 | Not Found | Check resource ID |
| 429 | Too Many Requests | Rate limit exceeded, wait and retry |
| 500 | Internal Server Error | Contact support |

### Error Response Format

```json
{
  "detail": "Error message",
  "error_code": "ERROR_CODE",
  "timestamp": "2025-11-22T10:30:00Z",
  "request_id": "uuid"
}
```

### Handling 401 Errors

```python
import requests

def make_request_with_retry(url, headers, data):
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 401:
        # Token expired, refresh it
        refresh_response = requests.post(
            "https://api.bridgecore.com/api/v1/auth/tenant/refresh",
            json={"refresh_token": refresh_token}
        )
        
        new_tokens = refresh_response.json()
        headers["Authorization"] = f"Bearer {new_tokens['access_token']}"
        
        # Retry request
        response = requests.post(url, headers=headers, json=data)
    
    return response
```

### Handling 429 Errors

```python
import time
import requests

def make_request_with_backoff(url, headers, data, max_retries=3):
    for attempt in range(max_retries):
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 429:
            # Rate limit exceeded, wait and retry
            wait_time = 2 ** attempt  # Exponential backoff
            time.sleep(wait_time)
            continue
        
        return response
    
    raise Exception("Max retries exceeded")
```

---

## Best Practices

### 1. Token Management

```python
class TokenManager:
    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
    
    def is_token_expired(self):
        return time.time() >= self.token_expiry
    
    def refresh_if_needed(self):
        if self.is_token_expired():
            self.refresh_access_token()
    
    def refresh_access_token(self):
        response = requests.post(
            "https://api.bridgecore.com/api/v1/auth/tenant/refresh",
            json={"refresh_token": self.refresh_token}
        )
        
        tokens = response.json()
        self.access_token = tokens["access_token"]
        self.token_expiry = time.time() + tokens["expires_in"]
```

### 2. Batch Operations

```python
# Instead of multiple single requests
for partner_id in partner_ids:
    response = requests.post(
        "https://api.bridgecore.com/api/v1/odoo/write",
        headers=headers,
        json={
            "model": "res.partner",
            "ids": [partner_id],
            "values": {"phone": "+1234567890"}
        }
    )

# Use batch update
response = requests.post(
    "https://api.bridgecore.com/api/v1/odoo/write",
    headers=headers,
    json={
        "model": "res.partner",
        "ids": partner_ids,  # All IDs at once
        "values": {"phone": "+1234567890"}
    }
)
```

### 3. Pagination

```python
def fetch_all_partners(headers):
    all_partners = []
    offset = 0
    limit = 100
    
    while True:
        response = requests.post(
            "https://api.bridgecore.com/api/v1/odoo/search_read",
            headers=headers,
            json={
                "model": "res.partner",
                "domain": [["customer_rank", ">", 0]],
                "fields": ["id", "name", "email"],
                "limit": limit,
                "offset": offset
            }
        )
        
        partners = response.json()
        if not partners:
            break
        
        all_partners.extend(partners)
        offset += limit
    
    return all_partners
```

### 4. Error Logging

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def make_api_request(url, headers, data):
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        raise
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection Error: {e}")
        raise
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout Error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        raise
```

### 5. Caching

```python
from functools import lru_cache
import time

class CachedAPI:
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    def get_partners(self, headers):
        cache_key = "partners"
        
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_data
        
        # Fetch from API
        response = requests.post(
            "https://api.bridgecore.com/api/v1/odoo/search_read",
            headers=headers,
            json={
                "model": "res.partner",
                "domain": [["customer_rank", ">", 0]],
                "fields": ["id", "name", "email"]
            }
        )
        
        data = response.json()
        self.cache[cache_key] = (data, time.time())
        return data
```

---

## Flutter Integration

### Setup

```dart
import 'package:bridgecore_flutter/bridgecore_flutter.dart';

void main() {
  BridgeCore.initialize(
    baseUrl: 'https://api.bridgecore.com',
    debugMode: true,
  );
  
  runApp(MyApp());
}
```

### Login

```dart
final loginResponse = await BridgeCore.instance.auth.login(
  email: 'user@company.com',
  password: 'password123',
);

print('Logged in as: ${loginResponse.user.fullName}');
```

### Fetch Data

```dart
final partners = await BridgeCore.instance.odoo.searchRead(
  model: 'res.partner',
  domain: [['customer_rank', '>', 0]],
  fields: ['id', 'name', 'email'],
  limit: 50,
);

print('Found ${partners.length} customers');
```

---

## React Integration

### Setup

```typescript
import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'https://api.bridgecore.com',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 errors
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Refresh token logic
      const refreshToken = localStorage.getItem('refresh_token');
      const response = await axios.post(
        'https://api.bridgecore.com/api/v1/auth/tenant/refresh',
        { refresh_token: refreshToken }
      );
      
      const { access_token } = response.data;
      localStorage.setItem('access_token', access_token);
      
      // Retry original request
      error.config.headers.Authorization = `Bearer ${access_token}`;
      return axios(error.config);
    }
    
    return Promise.reject(error);
  }
);
```

### Usage

```typescript
// Login
const login = async (email: string, password: string) => {
  const response = await apiClient.post('/api/v1/auth/tenant/login', {
    email,
    password,
  });
  
  localStorage.setItem('access_token', response.data.access_token);
  localStorage.setItem('refresh_token', response.data.refresh_token);
  
  return response.data;
};

// Fetch partners
const getPartners = async () => {
  const response = await apiClient.post('/api/v1/odoo/search_read', {
    model: 'res.partner',
    domain: [['customer_rank', '>', 0]],
    fields: ['id', 'name', 'email'],
    limit: 100,
  });
  
  return response.data;
};

// Create partner
const createPartner = async (data: PartnerData) => {
  const response = await apiClient.post('/api/v1/odoo/create', {
    model: 'res.partner',
    values: data,
  });
  
  return response.data;
};
```

---

## Support

For more information:
- **Documentation**: [docs/](../../)
- **API Reference**: [API_DOCUMENTATION.md](../api/API_DOCUMENTATION.md)
- **GitHub Issues**: https://github.com/geniustep/BridgeCore/issues
- **Email**: support@bridgecore.com

---

**Last Updated**: 2025-11-22
