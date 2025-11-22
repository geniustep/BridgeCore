# 🔧 تم تطبيق الإصلاح - Admin Dashboard API URL

## ✅ المشكلة التي تم حلها

كان Admin Dashboard يستخدم `http://localhost:8001` في طلبات API حتى عند الوصول من `https://bridgecore.geniura.com/admin/`.

## 🛠️ الحل المطبق

تم تعديل `/opt/BridgeCore/admin/src/config/api.ts` ليستخدم:
- **في Production** (bridgecore.geniura.com): مسار نسبي (`''`) - الطلبات تذهب لنفس الـ domain
- **في Local Dev** (localhost): `http://localhost:8001` - الطلبات تذهب للـ dev server

```typescript
const isProduction = window.location.hostname !== 'localhost';
export const API_BASE_URL = isProduction ? '' : (import.meta.env.VITE_API_URL || 'http://localhost:8001');
```

## 📋 ما تم عمله

1. ✅ تعديل `admin/src/config/api.ts` لاستخدام detection تلقائي
2. ✅ إعادة بناء Admin Dashboard container
3. ✅ إعادة تشغيل Admin service
4. ✅ التحقق من أن الملف الجديد موجود في الـ container

## 🔄 كيفية تطبيق الإصلاح في المتصفح

### الطريقة 1: Hard Refresh (الأسهل)
1. افتح `https://bridgecore.geniura.com/admin/` في المتصفح
2. اضغط على:
   - **Windows/Linux**: `Ctrl + Shift + R` أو `Ctrl + F5`
   - **Mac**: `Cmd + Shift + R`
3. سيتم تحميل الصفحة من جديد بدون cache

### الطريقة 2: Clear Cache
1. افتح Developer Tools (`F12`)
2. اذهب إلى **Application** tab (Chrome) أو **Storage** tab (Firefox)
3. اضغط على **Clear storage** أو **Clear site data**
4. أعد تحميل الصفحة (`F5`)

### الطريقة 3: Incognito/Private Window
1. افتح نافذة Incognito/Private
2. اذهب إلى `https://bridgecore.geniura.com/admin/`
3. سجل الدخول

## 🧪 التحقق من الإصلاح

بعد تطبيق Hard Refresh، افتح Developer Tools (`F12`) واذهب إلى **Console** tab.

يجب أن ترى:
```
[API CONFIG] {
  API_BASE_URL: "",
  isProduction: true,
  hostname: "bridgecore.geniura.com",
  ...
}
```

**ملاحظة:** `API_BASE_URL` يجب أن يكون **فارغ** (`""`) وليس `http://localhost:8001`

## 🎯 النتيجة المتوقعة

بعد الإصلاح:
- ✅ طلبات API ستذهب إلى `https://bridgecore.geniura.com/admin/auth/login`
- ✅ لن تظهر أخطاء CORS
- ✅ تسجيل الدخول سيعمل بشكل صحيح

## 📊 مثال على الطلبات

### قبل الإصلاح ❌
```
Request URL: http://localhost:8001/admin/auth/login
Status: Failed (CORS error)
```

### بعد الإصلاح ✅
```
Request URL: https://bridgecore.geniura.com/admin/auth/login
Status: 200 OK
```

## 🐛 إذا استمرت المشكلة

إذا استمرت المشكلة بعد Hard Refresh:

### 1. تحقق من Console
افتح Developer Tools → Console وابحث عن:
```
[API CONFIG]
```

إذا كان `API_BASE_URL` لا يزال `http://localhost:8001`، جرب:

### 2. Clear Browser Cache بالكامل
```
Chrome: Settings → Privacy and security → Clear browsing data
Firefox: Settings → Privacy & Security → Clear Data
```

### 3. تحقق من أن الملف الجديد يتم تحميله
في **Network** tab في Developer Tools:
- ابحث عن `index-C9Dzn9Ja.js` (الملف الجديد)
- **ليس** `index-CbtzuzYz.js` (الملف القديم)

### 4. أعد بناء الـ container يدوياً
```bash
cd /opt/BridgeCore/docker
docker-compose build --no-cache admin
docker-compose up -d admin
```

## ✅ تأكيد النجاح

للتأكد من أن كل شيء يعمل:

1. افتح `https://bridgecore.geniura.com/admin/`
2. افتح Developer Tools → Network tab
3. سجل الدخول بـ `admin@bridgecore.com` / `admin123`
4. يجب أن ترى طلب POST إلى:
   ```
   https://bridgecore.geniura.com/admin/auth/login
   ```
   وليس `http://localhost:8001/...`

## 📝 ملاحظات تقنية

### لماذا استخدمنا `window.location.hostname`؟
- هذا يتم تنفيذه في **runtime** (وقت التشغيل)
- Vite environment variables تُقرأ في **build time** (وقت البناء)
- نحتاج runtime detection لأن نفس الـ build يُستخدم في production و local dev

### لماذا `API_BASE_URL = ''` في production؟
- المسار النسبي (`''`) يعني "نفس الـ domain"
- عندما نكون على `https://bridgecore.geniura.com/admin/`
- الطلب إلى `/admin/auth/login` يذهب إلى `https://bridgecore.geniura.com/admin/auth/login`
- هذا يتجنب مشاكل CORS تماماً

## 🎉 الخلاصة

تم حل المشكلة! فقط قم بـ **Hard Refresh** (`Ctrl+Shift+R`) في المتصفح وكل شيء سيعمل.

---

**تاريخ الإصلاح:** November 22, 2025  
**الملفات المعدلة:** `/opt/BridgeCore/admin/src/config/api.ts`  
**الحالة:** ✅ تم التطبيق بنجاح

