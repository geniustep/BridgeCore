# 🌐 BridgeCore API Endpoints - Complete Reference

**النسخة:** 2.0  
**Base URL:** `/api/v1/odoo`  
**المصادقة:** Bearer Token (JWT)

---

## 📋 جدول جميع الـ Endpoints (26)

| # | Category | Operation | Endpoint | Priority |
|---|----------|-----------|----------|----------|
| **CRUD** | | | | |
| 1 | CRUD | create | `POST /api/v1/odoo/create` | 🔴 |
| 2 | CRUD | read | `POST /api/v1/odoo/read` | 🔴 |
| 3 | CRUD | write | `POST /api/v1/odoo/write` | 🔴 |
| 4 | CRUD | unlink | `POST /api/v1/odoo/unlink` | 🔴 |
| 5 | CRUD | copy | `POST /api/v1/odoo/copy` | 🟡 |
| **Search** | | | | |
| 6 | Search | search | `POST /api/v1/odoo/search` | 🔴 |
| 7 | Search | search_read | `POST /api/v1/odoo/search_read` | 🔴 |
| 8 | Search | search_count | `POST /api/v1/odoo/search_count` | 🔴 |
| **Names** | | | | |
| 9 | Names | name_search | `POST /api/v1/odoo/name_search` | 🟡 |
| 10 | Names | name_get | `POST /api/v1/odoo/name_get` | 🟡 |
| 11 | Names | name_create | `POST /api/v1/odoo/name_create` | 🟢 |
| **Advanced** | | | | |
| 12 | Advanced | onchange | `POST /api/v1/odoo/onchange` | 🔴 |
| 13 | Advanced | read_group | `POST /api/v1/odoo/read_group` | 🟡 |
| 14 | Advanced | default_get | `POST /api/v1/odoo/default_get` | 🟡 |
| **Views** | | | | |
| 15 | Views | fields_get | `POST /api/v1/odoo/fields_get` | 🟡 |
| 16 | Views | fields_view_get | `POST /api/v1/odoo/fields_view_get` | 🟢 |
| 17 | Views | load_views | `POST /api/v1/odoo/load_views` | 🟢 |
| 18 | Views | get_views | `POST /api/v1/odoo/get_views` | 🟢 |
| **Web** | | | | |
| 19 | Web | web_save | `POST /api/v1/odoo/web_save` | 🟡 |
| 20 | Web | web_read | `POST /api/v1/odoo/web_read` | 🟡 |
| 21 | Web | web_search_read | `POST /api/v1/odoo/web_search_read` | 🟡 |
| **Permissions** | | | | |
| 22 | Permissions | check_access_rights | `POST /api/v1/odoo/check_access_rights` | 🟡 |
| **Utility** | | | | |
| 23 | Utility | exists | `POST /api/v1/odoo/exists` | 🟢 |
| **Custom** | | | | |
| 24 | Custom | call_method | `POST /api/v1/odoo/call_method` | 🟡 |
| 25 | Custom | action_confirm | `POST /api/v1/odoo/action_confirm` | 🟡 |
| 26 | Custom | button_cancel | `POST /api/v1/odoo/button_cancel` | 🟡 |

---

## 📝 تفاصيل الـ Endpoints

### 1. CRUD Operations

#### 1.1 Create
```http
POST /api/v1/odoo/create
Authorization: Bearer {token}
Content-Type: application/json

{
  "model": "res.partner",
  "values": {
    "name": "أحمد محمد",
    "email": "ahmed@example.com",
    "phone": "+966501234567",
    "is_company": false
  },
  "context": {
    "lang": "ar_001"
  }
}
```

**Response:**
```json
{
  "success": true,
  "id": 12345,
  "model": "res.partner"
}
```

---

#### 1.2 Read
```http
POST /api/v1/odoo/read
Authorization: Bearer {token}
Content-Type: application/json

{
  "model": "res.partner",
  "ids": [12345, 12346],
  "fields": ["name", "email", "phone", "country_id"],
  "context": {}
}
```

**Response:**
```json
{
  "success": true,
  "records": [
    {
      "id": 12345,
      "name": "أحمد محمد",
      "email": "ahmed@example.com",
      "phone": "+966501234567",
      "country_id": [1, "Saudi Arabia"]
    }
  ],
  "count": 1
}
```

---

#### 1.3 Write (Update)
```http
POST /api/v1/odoo/write
Authorization: Bearer {token}
Content-Type: application/json

{
  "model": "res.partner",
  "ids": [12345],
  "values": {
    "phone": "+966509876543",
    "mobile": "+966551234567"
  },
  "context": {}
}
```

**Response:**
```json
{
  "success": true,
  "updated": true,
  "affected_records": 1
}
```

---

#### 1.4 Unlink (Delete)
```http
POST /api/v1/odoo/unlink
Authorization: Bearer {token}
Content-Type: application/json

{
  "model": "res.partner",
  "ids": [12345],
  "context": {}
}
```

**Response:**
```json
{
  "success": true,
  "deleted": true,
  "affected_records": 1
}
```

---

#### 1.5 Copy
```http
POST /api/v1/odoo/copy
Authorization: Bearer {token}
Content-Type: application/json

{
  "model": "sale.order",
  "id": 100,
  "default": {
    "date_order": "2024-12-01",
    "name": "نسخة من الطلب"
  },
  "context": {}
}
```

**Response:**
```json
{
  "success": true,
  "new_id": 101,
  "original_id": 100
}
```

---

### 2. Search Operations

#### 2.1 Search
```http
POST /api/v1/odoo/search
Authorization: Bearer {token}
Content-Type: application/json

{
  "model": "res.partner",
  "domain": [
    ["is_company", "=", true],
    ["country_id", "=", 1]
  ],
  "limit": 100,
  "offset": 0,
  "order": "name ASC",
  "context": {}
}
```

**Response:**
```json
{
  "success": true,
  "ids": [1, 5, 10, 15, 20],
  "count": 5
}
```

---

#### 2.2 Search Read
```http
POST /api/v1/odoo/search_read
Authorization: Bearer {token}
Content-Type: application/json

{
  "model": "product.product",
  "domain": [
    ["sale_ok", "=", true],
    ["type", "=", "product"]
  ],
  "fields": ["name", "list_price", "qty_available"],
  "limit": 50,
  "offset": 0,
  "order": "name ASC",
  "context": {}
}
```

**Response:**
```json
{
  "success": true,
  "records": [
    {
      "id": 1,
      "name": "لابتوب Dell",
      "list_price": 3500.00,
      "qty_available": 10.0
    },
    {
      "id": 2,
      "name": "ماوس Logitech",
      "list_price": 150.00,
      "qty_available": 50.0
    }
  ],
  "count": 2
}
```

---

#### 2.3 Search Count
```http
POST /api/v1/odoo/search_count
Authorization: Bearer {token}
Content-Type: application/json

{
  "model": "sale.order",
  "domain": [
    ["state", "in", ["sale", "done"]],
    ["date_order", ">=", "2024-01-01"]
  ],
  "context": {}
}
```

**Response:**
```json
{
  "success": true,
  "count": 1250
}
```

---

### 3. Name Operations

#### 3.1 Name Search (للـ Autocomplete)
```http
POST /api/v1/odoo/name_search
Authorization: Bearer {token}
Content-Type: application/json

{
  "model": "res.partner",
  "name": "ahmed",
  "domain": [["is_company", "=", true]],
  "operator": "ilike",
  "limit": 10,
  "context": {}
}
```

**Response:**
```json
{
  "success": true,
  "results": [
    [100, "Ahmed Ali Company"],
    [105, "Ahmed Trading Est."],
    [110, "Al-Ahmed Group"]
  ],
  "count": 3
}
```

---

#### 3.2 Name Get
```http
POST /api/v1/odoo/name_get
Authorization: Bearer {token}
Content-Type: application/json

{
  "model": "res.partner",
  "ids": [100, 105, 110],
  "context": {}
}
```

**Response:**
```json
{
  "success": true,
  "names": [
    [100, "Ahmed Ali Company"],
    [105, "Ahmed Trading Est."],
    [110, "Al-Ahmed Group"]
  ]
}
```

---

#### 3.3 Name Create
```http
POST /api/v1/odoo/name_create
Authorization: Bearer {token}
Content-Type: application/json

{
  "model": "res.partner",
  "name": "شركة جديدة",
  "context": {}
}
```

**Response:**
```json
{
  "success": true,
  "result": [200, "شركة جديدة"]
}
```

---

### 4. Advanced Operations

#### 4.1 Onchange (الأهم!)
```http
POST /api/v1/odoo/onchange
Authorization: Bearer {token}
Content-Type: application/json

{
  "model": "sale.order.line",
  "ids": [],
  "values": {
    "order_id": 100,
    "product_id": 50,
    "product_uom_qty": 5.0
  },
  "field": "product_id",
  "spec": {
    "product_id": "1",
    "product_uom_qty": "1",
    "price_unit": "1",
    "discount": "1",
    "tax_id": "1"
  },
  "context": {
    "lang": "ar_001",
    "pricelist": 1
  }
}
```

**Response:**
```json
{
  "success": true,
  "value": {
    "name": "لابتوب Dell Inspiron",
    "price_unit": 3500.00,
    "discount": 0.0,
    "tax_id": [[6, false, [1, 2]]],
    "product_uom": 1
  },
  "warning": null,
  "domain": {}
}
```

**Use Cases:**
- عند تغيير المنتج → حساب السعر
- عند تغيير الكمية → حساب المجموع
- عند تغيير العميل → تحديث شروط الدفع

---

#### 4.2 Read Group (للتقارير)
```http
POST /api/v1/odoo/read_group
Authorization: Bearer {token}
Content-Type: application/json

{
  "model": "sale.order",
  "domain": [
    ["state", "in", ["sale", "done"]],
    ["date_order", ">=", "2024-01-01"]
  ],
  "fields": ["amount_total"],
  "groupby": ["partner_id"],
  "orderby": "amount_total desc",
  "limit": 10,
  "context": {}
}
```

**Response:**
```json
{
  "success": true,
  "groups": [
    {
      "partner_id": [100, "أحمد للتجارة"],
      "partner_id_count": 15,
      "amount_total": 250000.00,
      "__domain": [["partner_id", "=", 100]]
    },
    {
      "partner_id": [105, "شركة النور"],
      "partner_id_count": 10,
      "amount_total": 180000.00,
      "__domain": [["partner_id", "=", 105]]
    }
  ],
  "count": 2
}
```

---

#### 4.3 Default Get
```http
POST /api/v1/odoo/default_get
Authorization: Bearer {token}
Content-Type: application/json

{
  "model": "sale.order",
  "fields": ["partner_id", "date_order", "pricelist_id", "warehouse_id"],
  "context": {
    "lang": "ar_001",
    "uid": 1
  }
}
```

**Response:**
```json
{
  "success": true,
  "defaults": {
    "date_order": "2024-11-23",
    "pricelist_id": 1,
    "warehouse_id": 1
  }
}
```

---

### 5. Views Operations

#### 5.1 Fields Get
```http
POST /api/v1/odoo/fields_get
Authorization: Bearer {token}
Content-Type: application/json

{
  "model": "res.partner",
  "fields": ["name", "email", "x_custom_field"],
  "attributes": ["string", "type", "required", "readonly"],
  "context": {}
}
```

**Response:**
```json
{
  "success": true,
  "fields": {
    "name": {
      "string": "Name",
      "type": "char",
      "required": true,
      "readonly": false,
      "size": 128
    },
    "email": {
      "string": "Email",
      "type": "char",
      "required": false,
      "readonly": false
    },
    "x_custom_field": {
      "string": "Custom Field",
      "type": "selection",
      "selection": [["option1", "Option 1"], ["option2", "Option 2"]]
    }
  }
}
```

---

#### 5.2 Fields View Get
```http
POST /api/v1/odoo/fields_view_get
Authorization: Bearer {token}
Content-Type: application/json

{
  "model": "res.partner",
  "view_id": null,
  "view_type": "form",
  "context": {}
}
```

**Response:**
```json
{
  "success": true,
  "view": {
    "arch": "<form>...</form>",
    "fields": {...},
    "model": "res.partner",
    "type": "form"
  }
}
```

---

#### 5.3 Load Views
```http
POST /api/v1/odoo/load_views
Authorization: Bearer {token}
Content-Type: application/json

{
  "model": "res.partner",
  "views": [
    [false, "form"],
    [false, "tree"],
    [false, "search"]
  ],
  "options": {
    "toolbar": true
  },
  "context": {}
}
```

**Response:**
```json
{
  "success": true,
  "views": {
    "form": {...},
    "tree": {...},
    "search": {...}
  }
}
```

---

### 6. Web Operations

#### 6.1 Web Search Read
```http
POST /api/v1/odoo/web_search_read
Authorization: Bearer {token}
Content-Type: application/json

{
  "model": "res.partner",
  "domain": [["is_company", "=", true]],
  "specification": {
    "name": {},
    "email": {},
    "country_id": {
      "fields": {
        "name": {},
        "code": {}
      }
    }
  },
  "limit": 50,
  "order": "name ASC",
  "context": {}
}
```

**Response:**
```json
{
  "success": true,
  "records": [
    {
      "id": 100,
      "name": "شركة ABC",
      "email": "info@abc.com",
      "country_id": {
        "id": 1,
        "name": "Saudi Arabia",
        "code": "SA"
      }
    }
  ],
  "length": 1
}
```

---

### 7. Permissions

#### 7.1 Check Access Rights
```http
POST /api/v1/odoo/check_access_rights
Authorization: Bearer {token}
Content-Type: application/json

{
  "model": "sale.order",
  "operation": "unlink",
  "raise_exception": false,
  "context": {}
}
```

**Response:**
```json
{
  "success": true,
  "has_access": true,
  "operation": "unlink",
  "model": "sale.order"
}
```

---

### 8. Utility

#### 8.1 Exists
```http
POST /api/v1/odoo/exists
Authorization: Bearer {token}
Content-Type: application/json

{
  "model": "res.partner",
  "ids": [1, 2, 999, 1000],
  "context": {}
}
```

**Response:**
```json
{
  "success": true,
  "existing_ids": [1, 2],
  "missing_ids": [999, 1000]
}
```

---

### 9. Custom Methods

#### 9.1 Call Method (عام)
```http
POST /api/v1/odoo/call_method
Authorization: Bearer {token}
Content-Type: application/json

{
  "model": "sale.order",
  "method": "action_confirm",
  "ids": [100],
  "args": [],
  "kwargs": {},
  "context": {}
}
```

**Response:**
```json
{
  "success": true,
  "result": true
}
```

---

#### 9.2 Action Confirm (مختصر)
```http
POST /api/v1/odoo/action_confirm
Authorization: Bearer {token}
Content-Type: application/json

{
  "model": "sale.order",
  "ids": [100, 101],
  "context": {}
}
```

---

## 🔐 المصادقة والـ Headers

### Required Headers
```http
Authorization: Bearer {jwt_token}
Content-Type: application/json
X-Tenant-ID: {tenant_id}  # اختياري إذا كان في الـ token
```

### Authentication Flow
```http
# 1. Login
POST /api/v1/auth/login
{
  "email": "user@company.com",
  "password": "password123",
  "system_credentials": {
    "system_type": "odoo",
    "url": "https://demo.odoo.com",
    "database": "demo",
    "username": "admin",
    "password": "admin"
  }
}

# Response
{
  "access_token": "eyJhbG...",
  "refresh_token": "eyJhbG...",
  "token_type": "bearer",
  "expires_in": 1800
}

# 2. استخدام الـ Token
POST /api/v1/odoo/search_read
Authorization: Bearer eyJhbG...
```

---

## 📊 Error Responses

### Standard Error Format
```json
{
  "success": false,
  "error": {
    "code": "ODOO_ERROR",
    "message": "Invalid field 'x_custom_field' on model 'res.partner'",
    "details": {
      "model": "res.partner",
      "method": "search_read",
      "odoo_error": "..."
    }
  }
}
```

### Common Error Codes
- `AUTH_ERROR` - مشكلة في المصادقة
- `ODOO_ERROR` - خطأ من Odoo
- `VALIDATION_ERROR` - بيانات غير صحيحة
- `NOT_FOUND` - مورد غير موجود
- `PERMISSION_DENIED` - لا توجد صلاحية

---

## 🎯 Best Practices

### 1. استخدام Context
```json
{
  "context": {
    "lang": "ar_001",           // اللغة
    "tz": "Asia/Riyadh",        // المنطقة الزمنية
    "active_test": false,       // تضمين السجلات غير النشطة
    "tracking_disable": true     // تعطيل التتبع (للأداء)
  }
}
```

### 2. Pagination
```json
{
  "limit": 50,
  "offset": 0,
  "order": "id DESC"
}
```

### 3. Field Selection
```json
{
  "fields": ["id", "name", "email"]  // فقط الحقول المطلوبة
}
```

---

## 📈 Rate Limiting

```
- 1000 requests/hour per user
- 100 requests/minute per user
- Burst: 20 requests/second
```

---

## 🔗 Related Documentation

- [دليل Odoo API](./odoo_jsonrpc_guide_fixed.md)
- [خطة التطوير](./BRIDGECORE_PHASE1_PLAN.md)
- [التنفيذ الكامل](./BRIDGECORE_OPERATIONS_COMPLETE.md)

---

**Last Updated:** نوفمبر 2024  
**API Version:** 2.0  
**Status:** 🟢 Complete Specification
