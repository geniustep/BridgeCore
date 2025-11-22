# 🔐 BridgeCore Authentication Guide

## نظرة عامة

BridgeCore يدعم نوعين من المصادقة:
1. **Tenant User Authentication** - للمستخدمين النهائيين (Flutter Apps)
2. **Admin Authentication** - للوحة الإدارة

---

## 1️⃣ Tenant User Login (للمستخدمين النهائيين)

### Endpoint
```
POST /api/v1/auth/tenant/login
```

### Request Body (أساسي)
```json
{
  "email": "user@company.com",
  "password": "password123"
}
```

### Request Body (مع فحص حقول Odoo - اختياري)
```json
{
  "email": "user@company.com",
  "password": "password123",
  "odoo_fields_check": {
    "model": "res.users",
    "list_fields": ["name", "login", "email", "lang", "tz"]
  }
}
```

### Response (نجاح)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "6d8d496b-9314-4744-98cd-518c98dfc94a",
    "email": "admin@done.done",
    "full_name": "zakaria hamid",
    "role": "admin",
    "odoo_user_id": null
  },
  "tenant": {
    "id": "60624b22-867b-4d41-9152-b0369d66262a",
    "name": "Done Distribution",
    "slug": "done-distribution",
    "status": "trial",
    "odoo_database": "shuttlebee",
    "odoo_version": "18.0"
  },
  "odoo_fields_data": null
}
```

### Response (مع فحص حقول Odoo)
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": { ... },
  "tenant": { ... },
  "odoo_fields_data": {
    "success": true,
    "model_exists": true,
    "model_name": "User",
    "fields_exist": true,
    "fields_info": {
      "name": {
        "id": 1145,
        "name": "name",
        "field_description": "Name",
        "ttype": "char"
      },
      "email": {
        "id": 1146,
        "name": "email",
        "field_description": "Email",
        "ttype": "char"
      }
    },
    "data": {
      "id": 2,
      "name": "Administrator",
      "login": "done",
      "email": "admin@example.com",
      "lang": "fr_FR",
      "tz": "Africa/Casablanca"
    }
  }
}
```

### Error Responses

#### 401 Unauthorized - بيانات خاطئة
```json
{
  "detail": "Invalid email or password"
}
```

#### 403 Forbidden - حساب معطل
```json
{
  "detail": "User account is inactive. Please contact administrator."
}
```

#### 403 Forbidden - Tenant معلق
```json
{
  "detail": "Tenant account is suspended. Please contact support."
}
```

#### 402 Payment Required - Trial منتهي
```json
{
  "detail": "Trial period has expired. Please upgrade your account."
}
```

---

## 2️⃣ Admin Login (للوحة الإدارة)

### Endpoint
```
POST /admin/auth/login
```

### Request Body
```json
{
  "email": "admin@bridgecore.com",
  "password": "admin123"
}
```

### Response (نجاح)
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "admin": {
    "id": 1,
    "email": "admin@bridgecore.com",
    "full_name": "BridgeCore Admin",
    "is_active": true,
    "is_superuser": true
  }
}
```

### Error Response
```json
{
  "detail": "Invalid credentials"
}
```

---

## 3️⃣ استخدام Access Token

### في Headers
```bash
Authorization: Bearer {access_token}
```

### مثال - جلب بيانات المستخدم
```bash
curl -X GET "https://bridgecore.geniura.com/api/v1/auth/tenant/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Response
```json
{
  "id": "6d8d496b-9314-4744-98cd-518c98dfc94a",
  "email": "admin@done.done",
  "full_name": "zakaria hamid",
  "role": "admin",
  "odoo_user_id": null,
  "is_active": true,
  "last_login": "2025-11-22T13:47:33.123456",
  "tenant": {
    "id": "60624b22-867b-4d41-9152-b0369d66262a",
    "name": "Done Distribution",
    "slug": "done-distribution",
    "status": "trial",
    "odoo_url": "https://app.propanel.ma",
    "odoo_database": "shuttlebee",
    "odoo_version": "18.0"
  }
}
```

---

## 4️⃣ Refresh Token

### Endpoint
```
POST /api/v1/auth/tenant/refresh
```

### Request Body
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Response
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

## 5️⃣ Token Expiration

| Token Type | مدة الصلاحية | الاستخدام |
|-----------|-------------|-----------|
| Access Token | 30 دقيقة | للوصول إلى الـ APIs |
| Refresh Token | 7 أيام | لتجديد Access Token |
| Admin Token | 24 ساعة | للوحة الإدارة |

---

## 6️⃣ أمثلة عملية

### مثال 1: Flutter - تسجيل دخول بسيط
```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

Future<Map<String, dynamic>> login(String email, String password) async {
  final response = await http.post(
    Uri.parse('https://bridgecore.geniura.com/api/v1/auth/tenant/login'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'email': email,
      'password': password,
    }),
  );

  if (response.statusCode == 200) {
    final data = jsonDecode(response.body);
    
    // حفظ الـ tokens
    await saveToken('access_token', data['access_token']);
    await saveToken('refresh_token', data['refresh_token']);
    
    // حفظ معلومات المستخدم
    await saveUserData(data['user']);
    await saveTenantData(data['tenant']);
    
    return data;
  } else {
    throw Exception('Login failed: ${response.body}');
  }
}
```

### مثال 2: Flutter - تسجيل دخول مع فحص حقول مخصصة
```dart
Future<Map<String, dynamic>> loginWithCustomFields(
  String email, 
  String password
) async {
  final response = await http.post(
    Uri.parse('https://bridgecore.geniura.com/api/v1/auth/tenant/login'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'email': email,
      'password': password,
      'odoo_fields_check': {
        'model': 'res.users',
        'list_fields': ['x_employee_code', 'x_department', 'x_branch_id']
      }
    }),
  );

  if (response.statusCode == 200) {
    final data = jsonDecode(response.body);
    
    // التحقق من نتيجة فحص الحقول
    if (data['odoo_fields_data']?['success'] == true) {
      final customFields = data['odoo_fields_data']['data'];
      print('Employee Code: ${customFields['x_employee_code']}');
      print('Department: ${customFields['x_department']}');
    } else {
      print('Custom fields not found: ${data['odoo_fields_data']['error']}');
    }
    
    return data;
  } else {
    throw Exception('Login failed');
  }
}
```

### مثال 3: JavaScript - تسجيل دخول
```javascript
async function login(email, password) {
  try {
    const response = await fetch('https://bridgecore.geniura.com/api/v1/auth/tenant/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: email,
        password: password,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const data = await response.json();
    
    // حفظ الـ tokens في localStorage
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    localStorage.setItem('user', JSON.stringify(data.user));
    localStorage.setItem('tenant', JSON.stringify(data.tenant));
    
    return data;
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
}
```

### مثال 4: استخدام Access Token
```javascript
async function fetchUserData() {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('https://bridgecore.geniura.com/api/v1/auth/tenant/me', {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (response.status === 401) {
    // Token منتهي - نحتاج refresh
    await refreshToken();
    return fetchUserData(); // إعادة المحاولة
  }

  return await response.json();
}
```

### مثال 5: تجديد Token
```javascript
async function refreshToken() {
  const refreshToken = localStorage.getItem('refresh_token');
  
  const response = await fetch('https://bridgecore.geniura.com/api/v1/auth/tenant/refresh', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      refresh_token: refreshToken,
    }),
  });

  if (!response.ok) {
    // Refresh token منتهي - نحتاج login جديد
    throw new Error('Session expired. Please login again.');
  }

  const data = await response.json();
  localStorage.setItem('access_token', data.access_token);
  
  return data.access_token;
}
```

---

## 7️⃣ معالجة الأخطاء

### Status Codes

| Code | المعنى | الإجراء المطلوب |
|------|--------|-----------------|
| 200 | نجاح | متابعة العمل |
| 401 | Unauthorized | بيانات خاطئة أو token منتهي |
| 402 | Payment Required | Trial منتهي - ترقية الحساب |
| 403 | Forbidden | حساب معطل أو معلق |
| 410 | Gone | حساب محذوف |
| 422 | Validation Error | بيانات غير صحيحة |
| 500 | Server Error | خطأ في السيرفر |

### مثال - معالجة شاملة للأخطاء
```dart
Future<void> handleLogin(String email, String password) async {
  try {
    final data = await login(email, password);
    // نجح تسجيل الدخول
    navigateToHome();
  } catch (e) {
    if (e.toString().contains('401')) {
      showError('البريد الإلكتروني أو كلمة السر غير صحيحة');
    } else if (e.toString().contains('403')) {
      showError('حسابك معطل. يرجى التواصل مع الدعم الفني');
    } else if (e.toString().contains('402')) {
      showError('انتهت فترة التجربة. يرجى ترقية حسابك');
    } else if (e.toString().contains('410')) {
      showError('هذا الحساب محذوف');
    } else {
      showError('حدث خطأ. يرجى المحاولة لاحقاً');
    }
  }
}
```

---

## 8️⃣ Best Practices

### ✅ الأمان
1. **لا تحفظ كلمات السر** في local storage أو shared preferences
2. **استخدم HTTPS دائماً** - لا تستخدم HTTP
3. **احذف الـ tokens** عند تسجيل الخروج
4. **تحقق من انتهاء Token** قبل كل request

### ✅ إدارة الـ Session
1. **حفظ refresh_token** بشكل آمن (Secure Storage في Flutter)
2. **تجديد access_token** تلقائياً عند انتهائه
3. **تسجيل خروج تلقائي** عند انتهاء refresh_token

### ✅ تجربة المستخدم
1. **عرض رسائل خطأ واضحة** بالعربية
2. **Loading indicator** أثناء تسجيل الدخول
3. **Remember me** باستخدام refresh_token
4. **Auto-login** إذا كان الـ token صالحاً

---

## 9️⃣ الملفات المرجعية

| الملف | الوصف |
|------|--------|
| `AUTHENTICATION_GUIDE.md` | هذا الملف - دليل شامل للمصادقة |
| `TENANT_USERS_API.md` | توثيق API إدارة المستخدمين |
| `ODOO_FIELDS_CHECK.md` | توثيق ميزة فحص حقول Odoo |
| `INTEGRATION_GUIDE.md` | دليل التكامل مع Flutter |
| `QUICK_START.md` | دليل البدء السريع |

---

## 🔟 أمثلة cURL كاملة

### تسجيل دخول عادي
```bash
curl -X POST https://bridgecore.geniura.com/api/v1/auth/tenant/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@done.done",
    "password": ",,07Genius"
  }'
```

### تسجيل دخول مع فحص حقول
```bash
curl -X POST https://bridgecore.geniura.com/api/v1/auth/tenant/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@done.done",
    "password": ",,07Genius",
    "odoo_fields_check": {
      "model": "res.users",
      "list_fields": ["name", "email", "lang"]
    }
  }'
```

### جلب معلومات المستخدم
```bash
curl -X GET https://bridgecore.geniura.com/api/v1/auth/tenant/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### تجديد Token
```bash
curl -X POST https://bridgecore.geniura.com/api/v1/auth/tenant/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

---

**آخر تحديث:** 22 نوفمبر 2025

