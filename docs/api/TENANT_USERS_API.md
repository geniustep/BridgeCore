# 🔐 Tenant Users Management API

## ✅ Overview

تم إضافة API كامل لإدارة مستخدمي الـ Tenant من Admin Dashboard.

## 🎯 Features

- ✅ عرض جميع مستخدمي tenant معين
- ✅ عرض تفاصيل مستخدم محدد
- ✅ إضافة مستخدم جديد
- ✅ تعديل بيانات المستخدم (بما في ذلك كلمة السر)
- ✅ حذف مستخدم

## 📋 API Endpoints

### Base URL
```
https://bridgecore.geniura.com/admin/tenant-users
```

### Authentication
جميع الـ endpoints تتطلب Admin JWT token:
```
Authorization: Bearer {admin_token}
```

---

## 1️⃣ List Tenant Users

**Endpoint:** `GET /admin/tenant-users`

**Query Parameters:**
- `tenant_id` (required): UUID of the tenant
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Max records to return (default: 100, max: 500)

**Example:**
```bash
curl -X GET "https://bridgecore.geniura.com/admin/tenant-users?tenant_id=23c1a19e-410a-4a57-a1b4-98580921d27e" \
  -H "Authorization: Bearer {admin_token}"
```

**Response:**
```json
[
  {
    "id": "2f4ebb4b-a6e3-4ec5-ab7d-b2389bb104ce",
    "tenant_id": "23c1a19e-410a-4a57-a1b4-98580921d27e",
    "email": "user@done.com",
    "full_name": "Test User",
    "role": "admin",
    "is_active": true,
    "odoo_user_id": 2,
    "last_login": "2025-11-22T01:45:11.873956",
    "created_at": "2025-11-22T01:04:19.728935",
    "updated_at": "2025-11-22T01:45:11.874600"
  }
]
```

---

## 2️⃣ Get Tenant User

**Endpoint:** `GET /admin/tenant-users/{user_id}`

**Path Parameters:**
- `user_id`: UUID of the user

**Example:**
```bash
curl -X GET "https://bridgecore.geniura.com/admin/tenant-users/2f4ebb4b-a6e3-4ec5-ab7d-b2389bb104ce" \
  -H "Authorization: Bearer {admin_token}"
```

**Response:**
```json
{
  "id": "2f4ebb4b-a6e3-4ec5-ab7d-b2389bb104ce",
  "tenant_id": "23c1a19e-410a-4a57-a1b4-98580921d27e",
  "email": "user@done.com",
  "full_name": "Test User",
  "role": "admin",
  "is_active": true,
  "odoo_user_id": 2,
  "last_login": "2025-11-22T01:45:11.873956",
  "created_at": "2025-11-22T01:04:19.728935",
  "updated_at": "2025-11-22T01:45:11.874600"
}
```

---

## 3️⃣ Create Tenant User

**Endpoint:** `POST /admin/tenant-users`

**Request Body:**
```json
{
  "tenant_id": "23c1a19e-410a-4a57-a1b4-98580921d27e",
  "email": "newuser@done.com",
  "password": "password123",
  "full_name": "New Test User",
  "role": "user",
  "is_active": true,
  "odoo_user_id": null
}
```

**Field Descriptions:**
- `tenant_id` (required): UUID of the tenant
- `email` (required): User email
- `password` (required): User password (min 8 characters)
- `full_name` (required): User full name
- `role` (optional): User role - "admin" or "user" (default: "user")
- `is_active` (optional): Whether user is active (default: true)
- `odoo_user_id` (optional): Odoo user ID for integration

**Example:**
```bash
curl -X POST "https://bridgecore.geniura.com/admin/tenant-users" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "23c1a19e-410a-4a57-a1b4-98580921d27e",
    "email": "newuser@done.com",
    "password": "password123",
    "full_name": "New Test User",
    "role": "user",
    "is_active": true
  }'
```

**Response:**
```json
{
  "id": "7644a138-e0cb-45eb-8eca-ca484914c2d1",
  "tenant_id": "23c1a19e-410a-4a57-a1b4-98580921d27e",
  "email": "newuser@done.com",
  "full_name": "New Test User",
  "role": "user",
  "is_active": true,
  "odoo_user_id": null,
  "last_login": null,
  "created_at": "2025-11-22T02:51:05.061212",
  "updated_at": "2025-11-22T02:51:05.061220"
}
```

---

## 4️⃣ Update Tenant User

**Endpoint:** `PUT /admin/tenant-users/{user_id}`

**Path Parameters:**
- `user_id`: UUID of the user

**Request Body:** (جميع الحقول اختيارية)
```json
{
  "email": "updated@done.com",
  "password": "newpassword123",
  "full_name": "Updated Name",
  "role": "admin",
  "is_active": false,
  "odoo_user_id": 5
}
```

**Example - Update Password:**
```bash
curl -X PUT "https://bridgecore.geniura.com/admin/tenant-users/7644a138-e0cb-45eb-8eca-ca484914c2d1" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "password": "newpassword123"
  }'
```

**Example - Update Multiple Fields:**
```bash
curl -X PUT "https://bridgecore.geniura.com/admin/tenant-users/7644a138-e0cb-45eb-8eca-ca484914c2d1" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Updated User",
    "password": "newpassword123",
    "role": "admin",
    "is_active": true
  }'
```

**Response:**
```json
{
  "id": "7644a138-e0cb-45eb-8eca-ca484914c2d1",
  "tenant_id": "23c1a19e-410a-4a57-a1b4-98580921d27e",
  "email": "newuser@done.com",
  "full_name": "Updated User",
  "role": "admin",
  "is_active": true,
  "odoo_user_id": null,
  "last_login": null,
  "created_at": "2025-11-22T02:51:05.061212",
  "updated_at": "2025-11-22T02:51:13.484436"
}
```

---

## 5️⃣ Delete Tenant User

**Endpoint:** `DELETE /admin/tenant-users/{user_id}`

**Path Parameters:**
- `user_id`: UUID of the user

**Example:**
```bash
curl -X DELETE "https://bridgecore.geniura.com/admin/tenant-users/7644a138-e0cb-45eb-8eca-ca484914c2d1" \
  -H "Authorization: Bearer {admin_token}"
```

**Response:**
```json
{
  "message": "User deleted successfully"
}
```

---

## 🔐 Password Management

### تشفير كلمة السر
- كلمات السر يتم تشفيرها تلقائياً باستخدام bcrypt
- لا يتم إرجاع كلمة السر في أي response
- عند التحديث، يتم تشفير كلمة السر الجديدة تلقائياً

### متطلبات كلمة السر
- الحد الأدنى: 8 أحرف
- يمكن أن تحتوي على: أحرف، أرقام، رموز خاصة

### تحديث كلمة السر
```bash
# تحديث كلمة السر فقط
curl -X PUT "https://bridgecore.geniura.com/admin/tenant-users/{user_id}" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{"password": "newpassword123"}'
```

---

## 🧪 Testing

### Test 1: Create User
```bash
TOKEN=$(curl -s -X POST "https://bridgecore.geniura.com/admin/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@bridgecore.com","password":"admin123"}' | jq -r '.token')

curl -X POST "https://bridgecore.geniura.com/admin/tenant-users" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "23c1a19e-410a-4a57-a1b4-98580921d27e",
    "email": "testuser@done.com",
    "password": "password123",
    "full_name": "Test User",
    "role": "user"
  }'
```

### Test 2: Update Password
```bash
curl -X PUT "https://bridgecore.geniura.com/admin/tenant-users/{user_id}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"password": "newpassword123"}'
```

### Test 3: Verify New Password
```bash
curl -X POST "https://bridgecore.geniura.com/api/v1/auth/tenant/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"testuser@done.com","password":"newpassword123"}'
```

---

## 📊 Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created successfully |
| 400 | Bad request (email already exists, invalid data) |
| 401 | Unauthorized (invalid/missing admin token) |
| 404 | Not found (user or tenant not found) |
| 500 | Internal server error |

---

## 📝 Files Created/Modified

### New Files:
1. `/opt/BridgeCore/app/schemas/admin/tenant_user_schemas.py`
   - Schemas for tenant user CRUD operations

2. `/opt/BridgeCore/app/api/routes/admin/tenant_users.py`
   - API endpoints for tenant user management

### Modified Files:
1. `/opt/BridgeCore/app/schemas/admin/__init__.py`
   - Added tenant user schemas export

2. `/opt/BridgeCore/app/main.py`
   - Added tenant users router

3. `/opt/BridgeCore/admin/nginx.conf`
   - Added `tenant-users` to API proxy regex

---

## 🎯 Use Cases

### 1. إضافة مستخدم جديد لـ tenant
```bash
POST /admin/tenant-users
{
  "tenant_id": "...",
  "email": "user@example.com",
  "password": "password123",
  "full_name": "John Doe",
  "role": "user"
}
```

### 2. إعادة تعيين كلمة سر مستخدم
```bash
PUT /admin/tenant-users/{user_id}
{
  "password": "newpassword123"
}
```

### 3. تعطيل مستخدم
```bash
PUT /admin/tenant-users/{user_id}
{
  "is_active": false
}
```

### 4. ترقية مستخدم إلى admin
```bash
PUT /admin/tenant-users/{user_id}
{
  "role": "admin"
}
```

### 5. حذف مستخدم
```bash
DELETE /admin/tenant-users/{user_id}
```

---

## ✅ Summary

تم إضافة API كامل لإدارة مستخدمي الـ Tenant:

- ✅ عرض المستخدمين
- ✅ إضافة مستخدم جديد
- ✅ تعديل بيانات المستخدم
- ✅ **تعديل كلمة السر** ← هذا ما طلبته!
- ✅ حذف مستخدم
- ✅ تشفير كلمات السر تلقائياً
- ✅ التحقق من صحة البيانات

**الآن يمكن للـ Admin إدارة مستخدمي أي tenant بما في ذلك تغيير كلمات السر!** 🎉

---

**Date:** November 22, 2025  
**Status:** ✅ Implemented and Tested  
**API Version:** 1.0

