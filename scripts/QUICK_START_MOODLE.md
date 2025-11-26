# Quick Start: اختبار Moodle API

## خطوات سريعة

### 1. الحصول على Moodle Token

```bash
# في Moodle Admin Panel:
Site Administration → Plugins → Web Services → Manage Tokens
→ Add Token → Copy token
```

### 2. إعداد اتصال Moodle (Admin API)

```bash
# الحصول على Admin Token
curl -X POST http://localhost:8001/admin/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "password"}'

# إضافة Moodle System (إذا لم يكن موجوداً)
curl -X POST http://localhost:8001/admin/systems \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "system_type": "moodle",
    "name": "Moodle LMS",
    "status": "active",
    "is_enabled": true
  }'

# إضافة اتصال للـ Tenant
curl -X POST http://localhost:8001/admin/systems/tenant-connections \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "TENANT_UUID",
    "system_id": "MOODLE_SYSTEM_UUID",
    "connection_config": {
      "url": "https://lms.example.com",
      "token": "MOODLE_TOKEN",
      "service": "moodle_mobile_app"
    },
    "is_active": true
  }'
```

### 3. اختبار API

```bash
# الحصول على Tenant Token
TOKEN=$(curl -s -X POST http://localhost:8001/api/v1/auth/tenant/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}' \
  | jq -r '.access_token')

# اختبار Site Info
curl -X GET http://localhost:8001/api/v1/moodle/site-info \
  -H "Authorization: Bearer $TOKEN"

# اختبار Health
curl -X GET http://localhost:8001/api/v1/moodle/health \
  -H "Authorization: Bearer $TOKEN"

# الحصول على الكورسات
curl -X GET http://localhost:8001/api/v1/moodle/courses \
  -H "Authorization: Bearer $TOKEN"
```

### 4. استخدام سكريبت الاختبار

```bash
python3 scripts/test_moodle_api.py \
  --base-url http://localhost:8001 \
  --moodle-url https://lms.example.com \
  --token MOODLE_TOKEN \
  --tenant-email user@example.com \
  --tenant-password password
```

---

## Endpoints الرئيسية

| Endpoint | Method | الوصف |
|----------|--------|-------|
| `/api/v1/moodle/site-info` | GET | معلومات الموقع |
| `/api/v1/moodle/health` | GET | فحص الاتصال |
| `/api/v1/moodle/courses` | GET | جميع الكورسات |
| `/api/v1/moodle/courses/{id}` | GET | كورس محدد |
| `/api/v1/moodle/users` | GET | جميع المستخدمين |
| `/api/v1/moodle/call` | POST | استدعاء دالة Moodle |

---

## استكشاف الأخطاء

| المشكلة | الحل |
|---------|------|
| "Moodle is not configured" | أضف اتصال Moodle للـ tenant |
| "Connection timeout" | تحقق من URL وإعدادات Firewall |
| "Invalid token" | أنشئ token جديد من Moodle |
| "Web services not enabled" | فعل Web Services في Moodle |

---

## المزيد من المعلومات

راجع `scripts/README_MOODLE_TESTING.md` للدليل الكامل.

