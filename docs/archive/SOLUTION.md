# حل مشكلة عدم تطابق بيانات Tenant

## المشكلة

عند استخدام `/api/v1/auth/tenant/me` يتم إرجاع tenant بـ ID: `23c1a19e-410a-4a57-a1b4-98580921d27e` (Done Company)

لكن عند محاولة الوصول إلى `http://localhost:3001/tenants/f9347437-67fe-4c93-9031-472afb5f1fc6/edit` في Admin Dashboard، لا يتم العثور على البيانات.

## السبب

يوجد **قاعدتي بيانات مختلفتين**:

1. **قاعدة بيانات `middleware_db`** (المستخدمة حالياً بواسطة API الرئيسي):
   - تحتوي على tenant واحد: `Done Company` (ID: `23c1a19e-410a-4a57-a1b4-98580921d27e`)
   - هذه هي القاعدة المتصلة بـ `https://bridgecore.geniura.com`

2. **قاعدة بيانات `bridgecore`** (قاعدة بيانات قديمة):
   - تحتوي على tenants قديمة: `done` (ID: `f9347437-67fe-4c93-9031-472afb5f1fc6`) و `alwah`
   - هذه القاعدة غير مستخدمة حالياً

## الحل

### الخيار 1: استخدام البيانات الجديدة (Done Company)

استخدم الـ ID الصحيح في Admin Dashboard:

```
http://localhost:3001/tenants/23c1a19e-410a-4a57-a1b4-98580921d27e/edit
```

### الخيار 2: إنشاء tenant جديد من Admin Dashboard

1. افتح Admin Dashboard: `http://localhost:3001` أو `https://bridgadmin.geniura.com`
2. سجل الدخول بحساب Admin:
   - Email: `admin@bridgecore.com`
   - Password: `admin123`
3. اذهب إلى Tenants → Create New Tenant
4. أنشئ tenant جديد بالبيانات التي تريدها

### الخيار 3: نقل البيانات القديمة إلى قاعدة البيانات الجديدة

إذا كنت تريد الاحتفاظ بالبيانات القديمة، يمكنك نقلها يدوياً:

```bash
# 1. تصدير البيانات من القاعدة القديمة
docker run -d --name temp_pg -v bridgecore_postgres_data:/var/lib/postgresql/data postgres:15-alpine
docker exec temp_pg pg_dump -U postgres bridgecore > /tmp/old_data.sql

# 2. استيراد البيانات إلى القاعدة الجديدة
docker exec -i bridgecore_db psql -U postgres middleware_db < /tmp/old_data.sql
```

## التحقق من البيانات

```bash
# التحقق من tenants في قاعدة البيانات الحالية
cd /opt/BridgeCore/docker
docker-compose exec -T db psql -U postgres -d middleware_db -c "SELECT id, name, slug, status FROM tenants;"

# التحقق من tenant users
docker-compose exec -T db psql -U postgres -d middleware_db -c "SELECT id, email, full_name, tenant_id FROM tenant_users;"
```

## بيانات الدخول الحالية

### Tenant User (للتطبيقات)
- Email: `user@done.com`
- Password: `done123`
- Tenant: Done Company (ID: `23c1a19e-410a-4a57-a1b4-98580921d27e`)

### Admin (للوحة الإدارة)
- Email: `admin@bridgecore.com`
- Password: `admin123`

## الروابط

- **API:** https://bridgecore.geniura.com
- **Admin Dashboard:** https://bridgadmin.geniura.com (أو http://localhost:3001)
- **API Docs:** https://bridgecore.geniura.com/docs

## ملاحظة مهمة

**Admin Dashboard يجب أن يكون متصلاً بنفس قاعدة البيانات التي يستخدمها الـ API الرئيسي.**

إذا كان Admin Dashboard يعمل على `localhost:3001`، تأكد من أن متغير البيئة `VITE_API_URL` يشير إلى `https://bridgecore.geniura.com` وليس `localhost:8000`.

