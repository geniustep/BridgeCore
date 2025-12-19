# دليل تتبع Logs لـ Odoo

## مواقع ملفات الـ Logs

الـ logs يتم حفظها في مجلد `logs/`:

- **`logs/app.log`** - جميع الـ logs (DEBUG, INFO, WARNING, ERROR)
- **`logs/errors.log`** - الأخطاء فقط (ERROR level)
- **`logs/app.json`** - في production (JSON format)

## أوامر تتبع الـ Logs

### 1. تتبع جميع الـ Logs (Real-time)

```bash
# تتبع جميع الـ logs
tail -f /opt/BridgeCore/logs/app.log

# أو مع ألوان (إذا كان terminal يدعم)
tail -f /opt/BridgeCore/logs/app.log | grep --color=always -E "ODOO|ERROR|WARNING|INFO"
```

### 2. تتبع أخطاء Odoo فقط

```bash
# تتبع ملف الأخطاء فقط
tail -f /opt/BridgeCore/logs/errors.log

# أو تصفية logs Odoo من ملف الـ logs الرئيسي
tail -f /opt/BridgeCore/logs/app.log | grep -i "odoo"
```

### 3. تتبع عمليات Search Read تحديداً

```bash
# تتبع عمليات search_read فقط
tail -f /opt/BridgeCore/logs/app.log | grep -i "search_read\|SEARCHREAD"

# تتبع الأخطاء في search_read
tail -f /opt/BridgeCore/logs/app.log | grep -i "search_read.*error\|SEARCHREAD.*Error"
```

### 4. تتبع عمليات Odoo مع تفاصيل

```bash
# تتبع جميع عمليات Odoo مع تفاصيل
tail -f /opt/BridgeCore/logs/app.log | grep -E "ODOO|odoo|Odoo" --color=always

# تتبع عمليات Odoo مع context
tail -f /opt/BridgeCore/logs/app.log | grep -A 5 -B 5 -i "odoo"
```

### 5. البحث في الـ Logs (غير Real-time)

```bash
# البحث عن خطأ معين
grep -i "shuttle.trip" /opt/BridgeCore/logs/app.log

# البحث عن أخطاء Odoo في آخر 100 سطر
tail -n 100 /opt/BridgeCore/logs/app.log | grep -i "odoo.*error"

# البحث عن جميع عمليات search_read
grep -i "search_read" /opt/BridgeCore/logs/app.log | tail -20
```

### 6. عرض آخر N سطر من الـ Logs

```bash
# آخر 50 سطر
tail -n 50 /opt/BridgeCore/logs/app.log

# آخر 100 سطر مع ألوان
tail -n 100 /opt/BridgeCore/logs/app.log | grep --color=always -E "ERROR|WARNING|ODOO"

# آخر 20 خطأ
tail -n 200 /opt/BridgeCore/logs/app.log | grep -i "error" | tail -20
```

### 7. تتبع Logs مع Timestamp

```bash
# تتبع مع عرض الوقت
tail -f /opt/BridgeCore/logs/app.log | while read line; do echo "[$(date '+%Y-%m-%d %H:%M:%S')] $line"; done

# أو استخدام ts (إذا كان مثبت)
tail -f /opt/BridgeCore/logs/app.log | ts '[%Y-%m-%d %H:%M:%S]'
```

### 8. تتبع Logs من Console (إذا كان الخادم يعمل)

إذا كان الخادم يعمل في terminal، ستظهر الـ logs مباشرة في الـ console:

```bash
# تشغيل الخادم مع logs
cd /opt/BridgeCore
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# الـ logs ستظهر مباشرة في الـ terminal
```

## أمثلة على Logs المتوقعة لـ Odoo

### Logs ناجحة:
```
2025-01-11 10:30:15 | INFO     | app.services.odoo.search_ops:search_read:211 - 🔍 [SEARCHREAD] Starting search_read operation
2025-01-11 10:30:15 | INFO     | app.services.odoo.search_ops:search_read:239 - ✅ [SEARCHREAD] Completed successfully
```

### Logs أخطاء:
```
2025-01-11 10:30:20 | ERROR    | app.services.odoo.search_ops:search_read:254 - ❌ [SEARCHREAD] Error: Connection timeout
2025-01-11 10:30:20 | ERROR    | app.api.routes.odoo.search:195 - ❌ [ENDPOINT] /search_read error
```

## أوامر مفيدة إضافية

### عرض حجم ملفات الـ Logs

```bash
# حجم جميع ملفات الـ logs
du -h /opt/BridgeCore/logs/*

# أكبر ملفات الـ logs
ls -lhS /opt/BridgeCore/logs/
```

### تنظيف الـ Logs القديمة

```bash
# حذف logs أقدم من 7 أيام (بحذر!)
find /opt/BridgeCore/logs/ -name "*.log" -mtime +7 -delete

# أو أرشفة logs قديمة
find /opt/BridgeCore/logs/ -name "*.log" -mtime +7 -exec gzip {} \;
```

### مراقبة Logs في الوقت الفعلي مع تصفية

```bash
# تتبع مع تصفية متعددة
tail -f /opt/BridgeCore/logs/app.log | grep --line-buffered -E "ERROR|WARNING|ODOO" | while read line; do echo "[$(date '+%H:%M:%S')] $line"; done
```

## استخدام journalctl (إذا كان يعمل كـ service)

إذا كان التطبيق يعمل كـ systemd service:

```bash
# تتبع logs الـ service
journalctl -u bridgecore -f

# تتبع مع تصفية Odoo
journalctl -u bridgecore -f | grep -i odoo
```

## نصائح

1. **استخدم `tail -f`** لتتبع logs في الوقت الفعلي
2. **استخدم `grep`** للبحث عن كلمات محددة
3. **راجع `errors.log`** للأخطاء فقط (أسرع)
4. **استخدم `--color=always`** مع grep لعرض ملون
5. **احفظ logs مهمة** قبل حذفها

## مثال عملي: تتبع خطأ search_read

```bash
# Terminal 1: تتبع logs
tail -f /opt/BridgeCore/logs/app.log | grep -i "search_read"

# Terminal 2: إرسال طلب (من Insomnia أو curl)
# سترى الـ logs تظهر مباشرة في Terminal 1
```
