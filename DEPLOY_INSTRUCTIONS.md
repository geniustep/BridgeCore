# تعليمات تحديث الخادم البعيد (Production Server)

## الخطوات السريعة

### 1. الاتصال بالخادم البعيد

```bash
ssh user@bridgecore.geniura.com
# أو
ssh root@bridgecore.geniura.com
```

### 2. تنفيذ سكريبت التحديث التلقائي

```bash
cd /opt/BridgeCore
git pull origin main
./scripts/deploy_to_production.sh
```

### 3. أو تنفيذ الخطوات يدوياً

```bash
# الانتقال إلى مجلد المشروع
cd /opt/BridgeCore  # أو المسار الصحيح

# جلب التحديثات
git fetch origin
git pull origin main

# إعادة تشغيل الخادم (اختر الطريقة المناسبة)

# إذا كنت تستخدم Docker Compose:
docker-compose restart fastapi
# أو
docker-compose up -d --build fastapi

# إذا كنت تستخدم systemd:
sudo systemctl restart bridgecore
# أو
sudo systemctl restart bridgecore-api

# إذا كنت تستخدم PM2:
pm2 restart bridgecore
```

### 4. التحقق من التحديث

```bash
# اختبار الـ endpoint الجديد
curl -X POST "https://bridgecore.geniura.com/api/v1/auth/tenant/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@done.com", "password": "done123"}'
```

## التحديثات المطلوبة

- ✅ إضافة `/api/v1/auth` إلى middleware skip paths
- ✅ إضافة endpoint `/api/v1/auth/tenant/login`
- ✅ تحديث tenant context middleware

## Commit Hash

Latest commit: `e417cb4` (fix: Add /api/v1/auth to middleware skip paths)

