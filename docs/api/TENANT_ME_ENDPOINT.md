# Tenant /me Endpoint Documentation

## Overview

The `/api/v1/auth/tenant/me` endpoint provides comprehensive information about the currently authenticated tenant user, including:

- **User Profile**: BridgeCore user information
- **Tenant Information**: Associated tenant details
- **Odoo Integration Data**: Partner, Employee, Groups, Companies
- **Custom Fields**: Optional Odoo model fields (on-demand)

---

## Endpoint Details

**URL**: `POST /api/v1/auth/tenant/me`

**Method**: `POST` (supports optional request body)

**Authentication**: Required - Bearer Token (JWT)

**Content-Type**: `application/json`

---

## Request

### Headers

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

### Body (Optional)

```json
{
  "odoo_fields_check": {
    "model": "res.users",
    "list_fields": ["shuttle_role", "custom_field1", "custom_field2"]
  }
}
```

**Parameters**:
- `odoo_fields_check` (optional): Object to request custom Odoo fields
  - `model` (string): Odoo model name (e.g., `"res.users"`, `"hr.employee"`)
  - `list_fields` (array): List of field names to retrieve

---

## Response

### Success Response (200 OK)

```json
{
  "user": {
    "id": "1f396a5a-a924-4e72-bf68-2710ae88decc",
    "email": "youssef@done.bridgecore.internal",
    "full_name": "chauffeur youssef",
    "role": "user",
    "odoo_user_id": 6,
    "created_at": "2025-11-22T20:08:29.905871",
    "last_login": "2025-11-22T21:07:10.433485"
  },
  "tenant": {
    "id": "9b230aba-8477-4979-a345-04c9b255cf45",
    "name": "done",
    "slug": "done",
    "status": "active",
    "odoo_url": "https://app.propanel.ma",
    "odoo_database": "shuttlebee",
    "odoo_version": "18.0"
  },
  "partner_id": 7,
  "employee_id": null,
  "groups": [
    "base.group_user",
    "base.group_partner_manager",
    "shuttlebee.group_shuttle_driver",
    "fleet.fleet_group_manager",
    "hr.group_hr_manager"
  ],
  "is_admin": false,
  "is_internal_user": true,
  "company_ids": [1],
  "current_company_id": 1,
  "odoo_fields_data": {
    "shuttle_role": "driver"
  }
}
```

### Response Fields

#### User Object
| Field | Type | Description |
|-------|------|-------------|
| `id` | string (UUID) | BridgeCore user ID |
| `email` | string | User email address |
| `full_name` | string | User's full name |
| `role` | string | User role in BridgeCore (`admin`, `user`) |
| `odoo_user_id` | integer | Linked Odoo user ID |
| `created_at` | string (ISO 8601) | User creation timestamp |
| `last_login` | string (ISO 8601) | Last login timestamp |

#### Tenant Object
| Field | Type | Description |
|-------|------|-------------|
| `id` | string (UUID) | Tenant ID |
| `name` | string | Tenant name |
| `slug` | string | Tenant slug |
| `status` | string | Tenant status (`active`, `inactive`, `suspended`) |
| `odoo_url` | string | Odoo instance URL |
| `odoo_database` | string | Odoo database name |
| `odoo_version` | string | Odoo version (e.g., `"18.0"`) |

#### Odoo Integration Fields
| Field | Type | Description |
|-------|------|-------------|
| `partner_id` | integer \| null | Odoo partner ID (from `res.partner`) |
| `employee_id` | integer \| null | Odoo employee ID (from `hr.employee`) - `null` if not an employee |
| `groups` | array[string] | List of Odoo group XML IDs (e.g., `"base.group_user"`) |
| `is_admin` | boolean | `true` if user has admin groups (`base.group_system` or `base.group_erp_manager`) |
| `is_internal_user` | boolean | `true` if user has `base.group_user` |
| `company_ids` | array[integer] | List of company IDs the user has access to |
| `current_company_id` | integer \| null | Current active company ID |
| `odoo_fields_data` | object \| null | Custom Odoo fields (only if requested and have values) |

---

## Usage Examples

### Example 1: Basic User Info (No Custom Fields)

**Request**:
```bash
curl -X POST https://bridgecore.geniura.com/api/v1/auth/tenant/me \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"
```

**Response**:
```json
{
  "user": {...},
  "tenant": {...},
  "partner_id": 7,
  "employee_id": null,
  "groups": ["base.group_user", ...],
  "is_admin": false,
  "is_internal_user": true,
  "company_ids": [1],
  "current_company_id": 1,
  "odoo_fields_data": null
}
```

---

### Example 2: With Custom Odoo Fields

**Request**:
```bash
curl -X POST https://bridgecore.geniura.com/api/v1/auth/tenant/me \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "odoo_fields_check": {
      "model": "res.users",
      "list_fields": ["shuttle_role", "phone", "mobile"]
    }
  }'
```

**Response**:
```json
{
  "user": {...},
  "tenant": {...},
  "partner_id": 7,
  "employee_id": null,
  "groups": [...],
  "is_admin": false,
  "is_internal_user": true,
  "company_ids": [1],
  "current_company_id": 1,
  "odoo_fields_data": {
    "shuttle_role": "driver",
    "phone": "+212600000000",
    "mobile": "+212700000000"
  }
}
```

**Note**: Only fields with non-empty values are included in `odoo_fields_data`.

---

### Example 3: JavaScript/TypeScript

```typescript
interface TenantMeRequest {
  odoo_fields_check?: {
    model: string;
    list_fields: string[];
  };
}

interface TenantMeResponse {
  user: {
    id: string;
    email: string;
    full_name: string;
    role: string;
    odoo_user_id: number;
    created_at: string;
    last_login: string | null;
  };
  tenant: {
    id: string;
    name: string;
    slug: string;
    status: string;
    odoo_url: string;
    odoo_database: string;
    odoo_version: string;
  };
  partner_id: number | null;
  employee_id: number | null;
  groups: string[];
  is_admin: boolean;
  is_internal_user: boolean;
  company_ids: number[];
  current_company_id: number | null;
  odoo_fields_data: Record<string, any> | null;
}

async function getTenantUserInfo(
  accessToken: string,
  customFields?: TenantMeRequest
): Promise<TenantMeResponse> {
  const response = await fetch('https://bridgecore.geniura.com/api/v1/auth/tenant/me', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: customFields ? JSON.stringify(customFields) : undefined
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
}

// Usage
const userInfo = await getTenantUserInfo(token);
console.log('Partner ID:', userInfo.partner_id);
console.log('Is Admin:', userInfo.is_admin);
console.log('Groups:', userInfo.groups);

// With custom fields
const userInfoWithFields = await getTenantUserInfo(token, {
  odoo_fields_check: {
    model: 'res.users',
    list_fields: ['shuttle_role', 'department_id']
  }
});
console.log('Custom Fields:', userInfoWithFields.odoo_fields_data);
```

---

## Error Responses

### 401 Unauthorized - Invalid Token
```json
{
  "detail": "Invalid token"
}
```

### 401 Unauthorized - User Not Found
```json
{
  "detail": "User not found or inactive"
}
```

### 404 Not Found - Tenant Not Found
```json
{
  "detail": "Tenant not found"
}
```

---

## Important Notes

### 1. **Odoo Data Availability**
- If Odoo connection fails, the endpoint will still return basic user/tenant info
- Odoo-specific fields will be `null` or empty arrays
- Check logs for Odoo connection errors

### 2. **Custom Fields Behavior**
- `odoo_fields_data` is only populated if:
  - `odoo_fields_check` is provided in the request
  - The Odoo connection is successful
  - The specified model and fields exist
  - The fields have non-empty values (`null`, `False`, `""` are excluded)

### 3. **Groups Format**
- Groups are returned as XML IDs (e.g., `"base.group_user"`)
- Format: `module.group_name`
- If XML ID is not found, fallback format: `"group_{id}"`

### 4. **Employee ID**
- Will be `null` if the user is not an employee in Odoo
- Requires `hr.employee` record with `user_id` matching the Odoo user

### 5. **Performance Considerations**
- Without custom fields: ~500-1000ms (depends on Odoo connection)
- With custom fields: ~1000-1500ms (additional Odoo query)
- Consider caching for frequently accessed data

---

## Comparison with Login Endpoint

| Feature | `/tenant/login` | `/tenant/me` |
|---------|----------------|--------------|
| **Purpose** | Authenticate user | Get current user info |
| **Authentication** | Email + Password | Bearer Token |
| **Returns Token** | ✅ Yes | ❌ No |
| **Odoo Fields** | ✅ Stored in token | ✅ Fetched on-demand |
| **Partner ID** | ❌ No | ✅ Yes |
| **Employee ID** | ❌ No | ✅ Yes |
| **Groups** | ❌ No | ✅ Yes (full list) |
| **Companies** | ❌ No | ✅ Yes (all + current) |
| **Use Case** | Initial login | Profile page, settings |

---

## Best Practices

### 1. **Cache User Info**
```typescript
// Cache user info in localStorage or state management
const userInfo = await getTenantUserInfo(token);
localStorage.setItem('userInfo', JSON.stringify(userInfo));

// Refresh periodically or on specific actions
```

### 2. **Conditional Custom Fields**
```typescript
// Only request custom fields when needed
const basicInfo = await getTenantUserInfo(token);

// Later, if you need custom fields
const detailedInfo = await getTenantUserInfo(token, {
  odoo_fields_check: {
    model: 'res.users',
    list_fields: ['shuttle_role']
  }
});
```

### 3. **Permission Checks**
```typescript
if (userInfo.is_admin) {
  // Show admin features
}

if (userInfo.groups.includes('shuttlebee.group_shuttle_driver')) {
  // Show driver-specific features
}
```

### 4. **Multi-Company Support**
```typescript
if (userInfo.company_ids.length > 1) {
  // Show company switcher
  console.log('Available companies:', userInfo.company_ids);
  console.log('Current company:', userInfo.current_company_id);
}
```

---

## Related Documentation

- [AUTHENTICATION_GUIDE.md](./AUTHENTICATION_GUIDE.md) - Login and token management
- [ODOO_FIELDS_CHECK.md](./ODOO_FIELDS_CHECK.md) - Custom fields during login
- [TENANT_USER_MANAGEMENT_FIX.md](./TENANT_USER_MANAGEMENT_FIX.md) - User creation and linking

---

## Changelog

### 2025-11-22
- ✅ Enhanced `/me` endpoint with comprehensive Odoo data
- ✅ Added `partner_id`, `employee_id`
- ✅ Added `groups`, `is_admin`, `is_internal_user`
- ✅ Added `company_ids`, `current_company_id`
- ✅ Added optional `odoo_fields_check` for custom fields
- ✅ Changed from `GET` to `POST` to support request body

---

## Support

For issues or questions:
1. Check the logs: `docker logs bridgecore-api`
2. Verify token validity
3. Ensure Odoo connection is active
4. Refer to related documentation

---

**Last Updated**: 2025-11-22

