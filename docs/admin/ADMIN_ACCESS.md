# كيفية الوصول إلى Admin Dashboard

## ✅ تم الإعداد بنجاح!

Admin Dashboard الآن يعمل ومتصل بالـ API الصحيح.

## 🌐 الروابط

### Admin Dashboard
- **المنفذ المحلي:** http://localhost:3002
- **الدومين (إذا كان متاحاً):** https://bridgadmin.geniura.com

### API
- **الدومين:** https://bridgecore.geniura.com
- **API Docs:** https://bridgecore.geniura.com/docs

## 🔐 بيانات الدخول

### Admin Login
```
Email: admin@bridgecore.com
Password: admin123
```

## 📋 البيانات المتاحة

### Tenant الحالي
```
ID: 23c1a19e-410a-4a57-a1b4-98580921d27e
Name: Done Company
Slug: done-company
Status: ACTIVE
```

### Tenant User
```
Email: user@done.com
Password: done123
```

## 🔗 الروابط المباشرة

### تعديل Tenant
```
http://localhost:3002/tenants/23c1a19e-410a-4a57-a1b4-98580921d27e/edit
```

### قائمة Tenants
```
http://localhost:3002/tenants
```

### Dashboard
```
http://localhost:3002/
```

## 📝 ملاحظات مهمة

1. **Admin Dashboard يعمل على المنفذ 3002** (وليس 3001)
2. **Admin Dashboard متصل بـ** `https://bridgecore.geniura.com`
3. **يجب تسجيل الدخول أولاً** باستخدام بيانات Admin
4. **جميع البيانات موجودة في قاعدة بيانات** `middleware_db`

## 🔄 إعادة التشغيل

إذا احتجت لإعادة تشغيل Admin Dashboard:

```bash
cd /opt/BridgeCore
docker-compose restart admin-dashboard
```

## 🛠️ التحقق من الحالة

```bash
# التحقق من أن الحاويات تعمل
docker ps | grep bridgecore

# التحقق من logs
docker-compose logs admin-dashboard

# اختبار الاتصال
curl http://localhost:3002
```

## ✨ الخطوات التالية

1. افتح المتصفح على: http://localhost:3002
2. سجل الدخول بحساب Admin
3. اذهب إلى Tenants
4. ستجد "Done Company" في القائمة
5. اضغط على Edit لتعديل البيانات

---

تم التحديث: 22 نوفمبر 2025

