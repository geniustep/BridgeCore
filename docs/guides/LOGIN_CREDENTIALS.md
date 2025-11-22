# BridgeCore - بيانات الدخول للاختبار

## 🔐 Tenant User Login (للتطبيقات - Flutter)

**API Endpoint:**
```bash
POST https://bridgecore.geniura.com/api/v1/auth/tenant/login
```

**بيانات الدخول:**
- **Email:** `user@done.com`
- **Password:** `done123`

**مثال على الطلب:**
```bash
curl -X POST "https://bridgecore.geniura.com/api/v1/auth/tenant/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@done.com", "password": "done123"}'
```

**الاستجابة:**
```json
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "uuid",
    "email": "user@done.com",
    "full_name": "Test User",
    "role": "admin",
    "odoo_user_id": 2
  },
  "tenant": {
    "id": "uuid",
    "name": "Done Company",
    "slug": "done-company",
    "status": "active"
  }
}
```

---

## 👨‍💼 Admin Login (للوحة الإدارة)

**API Endpoint:**
```bash
POST https://bridgecore.geniura.com/admin/auth/login
```

**بيانات الدخول:**
- **Email:** `admin@bridgecore.com`
- **Password:** `admin123`

**مثال على الطلب:**
```bash
curl -X POST "https://bridgecore.geniura.com/admin/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@bridgecore.com", "password": "admin123"}'
```

**الاستجابة:**
```json
{
  "admin": {
    "id": "uuid",
    "email": "admin@bridgecore.com",
    "full_name": "Super Admin",
    "role": "super_admin",
    "is_active": true,
    "last_login": "2025-11-22T01:04:32.964624"
  },
  "token": "eyJhbGci...",
  "token_type": "bearer"
}
```

---

## 🌐 Admin Dashboard

**URL:** https://bridgadmin.geniura.com/

استخدم بيانات Admin للدخول إلى لوحة الإدارة.

---

## 📝 معلومات إضافية

### Tenant Information
- **Name:** Done Company
- **Slug:** done-company
- **Status:** Active
- **Odoo URL:** https://odoo.geniura.com
- **Odoo Database:** done

### Plan Information
- **Plan:** Free Plan
- **Max Requests/Day:** 1000
- **Max Requests/Hour:** 100
- **Max Users:** 5

---

## 🔄 Endpoints الأخرى

### Get Current Tenant User
```bash
GET https://bridgecore.geniura.com/api/v1/auth/tenant/me
Authorization: Bearer {access_token}
```

### Get Current Admin
```bash
GET https://bridgecore.geniura.com/admin/auth/me
Authorization: Bearer {admin_token}
```

### Refresh Token (Tenant)
```bash
POST https://bridgecore.geniura.com/api/v1/auth/tenant/refresh
Authorization: Bearer {refresh_token}
```

### Logout (Tenant)
```bash
POST https://bridgecore.geniura.com/api/v1/auth/tenant/logout
Authorization: Bearer {access_token}
```

---

## 📚 التوثيق الكامل

- **Swagger UI:** https://bridgecore.geniura.com/docs
- **ReDoc:** https://bridgecore.geniura.com/redoc

---

## ✅ الحالة

- ✅ API يعمل بشكل صحيح
- ✅ Tenant Login يعمل
- ✅ Admin Login يعمل
- ✅ قاعدة البيانات محدثة
- ✅ بيانات الاختبار جاهزة

تم التحديث: 22 نوفمبر 2025

