# دليل الخطوات التالية بعد إنشاء Tenant

## ✅ الخطوة 1: اختبار الاتصال بـ Odoo

بعد إنشاء Tenant، يجب اختبار الاتصال بـ Odoo للتأكد من أن الإعدادات صحيحة.

### من Admin Dashboard:
1. اذهب إلى صفحة **Tenants**
2. اضغط على Tenant الذي أنشأته
3. اضغط على زر **"Test Connection"**
4. تحقق من النتيجة:
   - ✅ **Success**: الاتصال يعمل
   - ❌ **Failed**: تحقق من:
     - Odoo URL صحيح
     - Database name صحيح
     - Username و Password صحيحين
     - Odoo instance متاح من الشبكة

### من API مباشرة:
```bash
# احصل على Admin Token أولاً
ADMIN_TOKEN=$(curl -s -X POST http://localhost:8001/admin/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@bridgecore.com","password":"admin123"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])")

# احصل على Tenant ID
TENANT_ID=$(curl -s -X GET http://localhost:8001/admin/tenants \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[0]['id'] if data else '')")

# اختبر الاتصال
curl -X POST http://localhost:8001/admin/tenants/$TENANT_ID/test-connection \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json"
```

---

## ✅ الخطوة 2: تفعيل Tenant

إذا كان Tenant في حالة `trial`، يجب تفعيله:

### من Admin Dashboard:
1. اذهب إلى صفحة **Tenants**
2. اضغط على Tenant
3. اضغط على زر **"Activate"**

### من API:
```bash
curl -X POST http://localhost:8001/admin/tenants/$TENANT_ID/activate \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json"
```

---

## ✅ الخطوة 3: إنشاء مستخدمين للـ Tenant

بعد تفعيل Tenant، يمكنك إنشاء مستخدمين للوصول إلى البيانات.

### من Admin Dashboard:
1. اذهب إلى صفحة **Tenants**
2. اضغط على Tenant
3. ابحث عن قسم **Users** أو **Tenant Users**
4. اضغط على **"Add User"**
5. املأ البيانات:
   - Email
   - Password
   - Full Name
   - Role (Admin أو User)

### ملاحظة:
إذا لم تكن هناك واجهة لإنشاء مستخدمين، يمكنك استخدام API مباشرة (انظر أدناه).

---

## ✅ الخطوة 4: استخدام API للوصول إلى البيانات

بعد إنشاء Tenant وتفعيله، يمكن للمستخدمين استخدام API للوصول إلى بيانات Odoo.

### 4.1 تسجيل الدخول كمستخدم Tenant

```bash
# تسجيل الدخول
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@company.com",
    "password": "password",
    "database": "company_db"
  }'

# Response:
# {
#   "access_token": "eyJ...",
#   "refresh_token": "eyJ...",
#   "system_id": "odoo-company_db",
#   "user": {
#     "id": 1,
#     "username": "user@company.com",
#     "name": "User Name"
#   }
# }
```

### 4.2 استخدام Token للوصول إلى البيانات

```bash
# احفظ Token
TOKEN="your_access_token_here"

# البحث وقراءة البيانات
curl -X POST http://localhost:8001/api/v1/odoo/search_read \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "res.partner",
    "domain": [["customer_rank", ">", 0]],
    "fields": ["id", "name", "email", "phone"],
    "limit": 100
  }'

# إنشاء سجل جديد
curl -X POST http://localhost:8001/api/v1/odoo/create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "res.partner",
    "values": {
      "name": "New Customer",
      "email": "customer@example.com",
      "phone": "+1234567890"
    }
  }'

# تحديث سجل
curl -X POST http://localhost:8001/api/v1/odoo/write \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "res.partner",
    "ids": [1],
    "values": {
      "phone": "+9876543210"
    }
  }'

# حذف سجل
curl -X POST http://localhost:8001/api/v1/odoo/unlink \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "res.partner",
    "ids": [1, 2, 3]
  }'
```

---

## ✅ الخطوة 5: مراقبة الاستخدام والتحليلات

### من Admin Dashboard:
1. اذهب إلى صفحة **Analytics** لرؤية:
   - إحصائيات عامة
   - أكثر المستأجرين استخداماً
   - إحصائيات لكل tenant

2. اذهب إلى صفحة **Logs** لرؤية:
   - Usage Logs - جميع الطلبات
   - Error Logs - الأخطاء والمشاكل

### من API:
```bash
# إحصائيات عامة
curl -X GET http://localhost:8001/admin/analytics/overview \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# إحصائيات Tenant محدد
curl -X GET "http://localhost:8001/admin/analytics/tenants/$TENANT_ID?days=30" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Usage Logs
curl -X GET "http://localhost:8001/admin/logs/usage?tenant_id=$TENANT_ID&limit=100" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## ✅ الخطوة 6: إعداد Webhooks (اختياري)

إذا كنت تريد تتبع التغييرات في الوقت الفعلي من Odoo:

### 6.1 تفعيل Webhooks في Odoo:
1. اذهب إلى Odoo Settings
2. ابحث عن Webhooks أو API Settings
3. أضف Webhook URL: `http://your-bridgecore-url/api/v1/webhooks/push`

### 6.2 استخدام Smart Sync:
```bash
# Pull التحديثات
curl -X POST http://localhost:8001/api/v2/sync/pull \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "device_id": "device_123",
    "app_type": "sales_app",
    "limit": 100
  }'
```

---

## 📋 Checklist سريع:

- [ ] ✅ تم إنشاء Tenant
- [ ] ✅ تم اختبار الاتصال بـ Odoo
- [ ] ✅ تم تفعيل Tenant
- [ ] ✅ تم إنشاء مستخدمين للـ Tenant
- [ ] ✅ تم اختبار تسجيل الدخول
- [ ] ✅ تم اختبار API (search_read, create, update)
- [ ] ✅ تم مراجعة Analytics
- [ ] ✅ تم مراجعة Logs

---

## 🔗 روابط مفيدة:

- **API Documentation**: http://localhost:8001/docs
- **Admin Dashboard**: http://localhost:3001
- **Flower (Celery)**: http://localhost:5555

---

## 💡 نصائح:

1. **أمان**: غيّر كلمات المرور الافتراضية في الإنتاج
2. **Rate Limiting**: راقب حدود الاستخدام لكل tenant
3. **Logs**: راجع Logs بانتظام للكشف عن المشاكل
4. **Backup**: احتفظ بنسخ احتياطية من قاعدة البيانات

---

## 🆘 في حالة وجود مشاكل:

1. تحقق من السجلات:
   ```bash
   docker-compose logs -f fastapi
   ```

2. تحقق من حالة الخدمات:
   ```bash
   docker-compose ps
   ```

3. تحقق من الاتصال بـ Odoo:
   ```bash
   curl -X POST http://localhost:8001/admin/tenants/{tenant_id}/test-connection
   ```

