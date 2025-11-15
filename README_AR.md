# BridgeCore - دليل المشروع الشامل (عربي)

<div dir="rtl">

## 📋 نظرة عامة

**BridgeCore** هو middleware شامل مبني على FastAPI يربط بين تطبيقات Flutter وأنظمة ERP/CRM (Odoo، SAP، Salesforce).

### ✨ المميزات الرئيسية

- 🔄 **ترقية إصدارات Odoo التلقائية**: من النسخة 13.0 إلى 19.0 بدعم الترقية متعددة الخطوات
- 🔐 **أمان متقدم**: JWT، تشفير Fernet، حد معدل الطلبات
- ⚡ **أداء عالي**: Redis caching، Circuit Breaker، Connection pooling
- 📊 **مراقبة شاملة**: Sentry، Prometheus، WebSocket للتحديثات الفورية
- 🔧 **قابل للتوسع**: Celery task queue، عمليات دفعية، تقارير

---

## 📚 الملفات المتوفرة

### 1. التوثيق الشامل

#### `DOCUMENTATION.md` (الإنجليزية)
التوثيق الكامل للمشروع يحتوي على:
- نظرة عامة على البنية المعمارية
- دليل التثبيت (محلي و Docker)
- مرجع API كامل مع أمثلة curl
- **دليل ترقية Odoo (13→19)** مع أمثلة
- أفضل ممارسات الأمان
- تحسين الأداء
- إعداد المراقبة (Prometheus + Grafana)
- إعداد قائمة المهام
- أمثلة WebSocket
- دليل النشر للإنتاج
- حل المشكلات

### 2. خطة دمج gmobile

#### `GMOBILE_INTEGRATION_PLAN.md` (العربية)
خطة شاملة لدمج BridgeCore مع مشروع gmobile:

**المحتويات**:
- ✅ تحليل البنية الحالية لـ gmobile
- ✅ تصميم نظام متوازي (Parallel System)
- ✅ استراتيجية التبديل بين النظامين
- ✅ تطبيق BridgeCore Client في Flutter
- ✅ طبقة الخدمات الموحدة
- ✅ خطة التنفيذ التدريجية (10 أسابيع)
- ✅ Metrics والمقارنة
- ✅ A/B Testing
- ✅ صفحة إعدادات المطورين
- ✅ خطة الانتقال الكامل
- ✅ خطة الطوارئ (Rollback)

**الميزة الرئيسية**:
🔥 **عدم المساس بالمشروع القديم** - النظام المتوازي يسمح لك بتجربة BridgeCore دون أي مخاطر!

### 3. Prompts جاهزة للاستخدام

#### `PROMPT_GMOBILE_ANALYSIS.md` (العربية)
ملف يحتوي على Prompts جاهزة لتحليل gmobile:

**الاستخدام**:
1. انسخ الـ Prompt المناسب
2. افتح محادثة جديدة مع Claude
3. الصق الـ Prompt
4. احصل على تحليل/تصميم/كود شامل

**يحتوي على Prompts لـ**:
- 📊 المرحلة الأولى: التحليل الشامل
- 🏗️ المرحلة الثانية: التصميم المعماري
- 💻 المرحلة الثالثة: التطبيق
- 🧪 المرحلة الرابعة: الاختبار
- 📖 المرحلة الخامسة: التوثيق

---

## 🚀 البدء السريع

### المتطلبات

```bash
# المطلوب
Python 3.10+
PostgreSQL 13+
Redis 6+

# اختياري (للإنتاج)
Docker & Docker Compose
Celery workers
Prometheus & Grafana
```

### التثبيت

```bash
# استنساخ المشروع
git clone https://github.com/geniustep/BridgeCore.git
cd BridgeCore

# إنشاء بيئة افتراضية
python -m venv venv
source venv/bin/activate  # في Windows: venv\Scripts\activate

# تثبيت المتطلبات
pip install -r requirements.txt

# إعداد البيئة
cp .env.example .env
# قم بتحرير .env بإعداداتك

# تشغيل migrations
alembic upgrade head

# تشغيل التطبيق
uvicorn app.main:app --reload

# الوصول إلى التوثيق
# افتح http://localhost:8000/docs
```

### التشغيل بـ Docker

```bash
# بناء وتشغيل مع Docker Compose
docker-compose up -d

# عرض السجلات
docker-compose logs -f app

# إيقاف الخدمات
docker-compose down
```

---

## 📖 دليل الاستخدام السريع

### 1. التسجيل والمصادقة

```bash
# تسجيل الدخول
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "password123"
  }'

# الاستجابة
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 2. تسجيل نظام Odoo

```bash
curl -X POST "http://localhost:8000/api/v1/systems" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "system_id": "odoo_main",
    "system_type": "odoo",
    "system_version": "17.0",
    "name": "Odoo الإنتاج",
    "connection_config": {
      "url": "https://odoo.example.com",
      "database": "production",
      "username": "admin",
      "password": "secret123"
    }
  }'
```

### 3. عمليات CRUD

```bash
# إنشاء عميل جديد
curl -X POST "http://localhost:8000/api/v1/systems/odoo_main/crud" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "create",
    "model": "res.partner",
    "data": {
      "name": "أحمد السعودي",
      "email": "ahmed@example.com",
      "phone": "+966501234567"
    }
  }'

# قراءة العملاء
curl -X POST "http://localhost:8000/api/v1/systems/odoo_main/crud" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "read",
    "model": "res.partner",
    "domain": [["is_company", "=", false]],
    "fields": ["name", "email", "phone"],
    "limit": 10
  }'
```

---

## 🔄 ترقية إصدارات Odoo (13.0 → 19.0)

### المسارات المدعومة

```
13.0 → 14.0 → 15.0 → 16.0 → 17.0 → 18.0 → 19.0
```

### مثال: ترقية تلقائية من 13.0 إلى 19.0

```python
from app.services.version_handler_v2 import EnhancedVersionHandler

handler = EnhancedVersionHandler()

# بيانات من Odoo 13
data = {
    "name": "أحمد السعودي",
    "customer": True,  # تم حذفه في 14.0
    "phone": "+966501234567",  # تم إعادة تسميته في 15.0
    "user_id": 5  # تم إعادة تسميته في 16.0
}

# ترقية تلقائية إلى 19.0 (عبر جميع الإصدارات الوسيطة)
migrated = await handler.migrate_data(
    data=data,
    system_type="odoo",
    from_version="13.0",
    to_version="19.0",
    model="res.partner",
    auto_multi_hop=True
)

# النتيجة:
# {
#     "name": "أحمد السعودي",
#     "type": "contact",  # customer=True تم تحويله
#     "phone_primary": "+966501234567",  # phone تم إعادة تسميته
#     "sales_person_id": 5  # user_id تم إعادة تسميته
# }
```

### الحصول على خطة الترقية (Dry Run)

```python
plan = await handler.get_migration_plan(
    system_type="odoo",
    from_version="13.0",
    to_version="19.0",
    model="res.partner"
)

# يعرض جميع الخطوات والتغييرات المطلوبة
```

---

## 🔧 دمج مع مشروع gmobile

### الخطوات

1. **اقرأ خطة الدمج الشاملة**:
   ```bash
   cat GMOBILE_INTEGRATION_PLAN.md
   ```

2. **استخدم Prompts الجاهزة**:
   - افتح `PROMPT_GMOBILE_ANALYSIS.md`
   - انسخ الـ Prompt الأول (المرحلة الأولى: التحليل)
   - استخدمه مع Claude لتحليل gmobile

3. **راجع النتائج**:
   - راجع التحليل مع فريقك
   - حدد الملفات التي تحتاج تعديل
   - خطط للمراحل القادمة

4. **نفذ النظام المتوازي**:
   - اتبع الخطة في `GMOBILE_INTEGRATION_PLAN.md`
   - أنشئ branch جديد: `feature/bridgecore-integration`
   - طبق التغييرات تدريجياً

5. **اختبر وقارن**:
   - استخدم Developer Settings للتبديل
   - قارن الأداء بين النظامين
   - اجمع metrics

### المزايا الرئيسية للنظام المتوازي

✅ **صفر مخاطر**: النظام القديم لا يتأثر أبداً
✅ **تجربة آمنة**: يمكنك التبديل في أي وقت
✅ **مقارنة حية**: قياس الأداء لكلا النظامين
✅ **انتقال تدريجي**: من 0% إلى 100% تدريجياً
✅ **خطة طوارئ**: rollback فوري إذا لزم الأمر

---

## 📊 المراقبة والـ Metrics

### Prometheus Metrics

```bash
# الوصول إلى metrics
curl http://localhost:8000/metrics
```

**Metrics المتوفرة**:
- `http_requests_total` - إجمالي طلبات HTTP
- `http_request_duration_seconds` - مدة طلبات HTTP
- `cache_hits_total` / `cache_misses_total` - نجاح/فشل الـ cache
- `api_operations_total` - عمليات API حسب النظام/Model
- `circuit_breaker_state` - حالة Circuit Breaker
- `version_migrations_total` - ترقيات الإصدارات

### Sentry للأخطاء

```bash
# في .env
SENTRY_DSN="https://your-key@sentry.io/project-id"
```

---

## 🔐 الأمان

### تشفير البيانات الحساسة

```python
from app.core.encryption import encryption_service

# تشفير إعدادات الاتصال
encrypted = encryption_service.encrypt_config({
    "url": "https://odoo.example.com",
    "username": "admin",
    "password": "secret123"
})

# فك التشفير عند الحاجة
config = encryption_service.decrypt_config(encrypted)
```

### حدود معدل الطلبات (Rate Limits)

- **المصادقة**: 10 طلبات/دقيقة
- **القراءة**: 100 طلبات/دقيقة
- **الكتابة**: 50 طلبات/دقيقة
- **الحذف**: 20 طلبات/دقيقة
- **العمليات الدفعية**: 10 طلبات/دقيقة

---

## 🎯 قائمة المهام (Celery)

### تشغيل Workers

```bash
# تشغيل Celery worker
celery -A app.tasks.celery_app worker --loglevel=info

# تشغيل Celery beat (للمهام الدورية)
celery -A app.tasks.celery_app beat --loglevel=info

# مراقبة المهام مع Flower
celery -A app.tasks.celery_app flower
# الوصول: http://localhost:5555
```

### المهام المتوفرة

- ✅ **عمليات دفعية**: معالجة عدة عمليات في طلب واحد
- ✅ **إنشاء التقارير**: PDF، Excel، CSV
- ✅ **مزامنة البيانات**: بين نظامين
- ✅ **ترقية الإصدارات**: لعدة سجلات
- ✅ **تنظيف السجلات القديمة**: يومياً
- ✅ **تحديث الاتصالات**: كل 30 دقيقة

---

## 🌐 WebSocket للتحديثات الفورية

### الاتصال من JavaScript

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/123');

ws.onopen = () => {
  console.log('متصل');

  // الاشتراك في قناة
  ws.send(JSON.stringify({
    type: 'subscribe',
    channel: 'system_status'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('تم الاستلام:', data);
};
```

### القنوات المتوفرة

- `system_status`: تغييرات حالة الاتصال بالنظام
- `operations`: تقدم العمليات طويلة الأمد
- `audit`: أحداث سجل التدقيق
- `cache`: إلغاء صلاحية الـ cache

---

## 📦 البنية المعمارية

```
┌─────────────────────────────────────────────┐
│           تطبيق Flutter (gmobile)          │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│              BridgeCore API                 │
│  ┌────────────────────────────────────┐    │
│  │  JWT + Rate Limiting + Encryption  │    │
│  └────────────────────────────────────┘    │
│  ┌────────────────────────────────────┐    │
│  │  Field Mapping + Version Handler   │    │
│  └────────────────────────────────────┘    │
│  ┌────────────────────────────────────┐    │
│  │  Cache + Circuit Breaker + Audit   │    │
│  └────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
       │              │              │
       ▼              ▼              ▼
   ┌──────┐      ┌──────┐      ┌──────┐
   │ Odoo │      │ SAP  │      │Salesf│
   │13-19 │      │      │      │ orce │
   └──────┘      └──────┘      └──────┘
```

---

## 🛠️ الملفات الرئيسية

### الخدمات (Services)

- `app/services/system_service.py` - تنسيق العمليات الرئيسية
- `app/services/field_mapping_service.py` - تحويل الحقول
- `app/services/version_handler_v2.py` - ترقية الإصدارات متعددة الخطوات
- `app/services/odoo_versions.py` - قواعد الترقية 13-19

### الأساسيات (Core)

- `app/core/security.py` - مصادقة JWT
- `app/core/encryption.py` - تشفير Fernet
- `app/core/rate_limiter.py` - حد معدل الطلبات
- `app/core/circuit_breaker.py` - Circuit Breaker
- `app/core/monitoring.py` - Sentry + Prometheus
- `app/core/cache.py` - Redis caching

### المحولات (Adapters)

- `app/adapters/odoo_adapter.py` - محول Odoo كامل
- `app/adapters/base_adapter.py` - واجهة المحول الأساسية

### قاعدة البيانات (Models)

- `app/models/user.py` - إدارة المستخدمين
- `app/models/system.py` - إعدادات النظام
- `app/models/audit_log.py` - سجل التدقيق
- `app/models/field_mapping.py` - تعيينات الحقول

---

## 📝 أمثلة الاستخدام

### مثال كامل: من التسجيل إلى CRUD

```python
import httpx

BASE_URL = "http://localhost:8000"

# 1. تسجيل الدخول
async with httpx.AsyncClient() as client:
    response = await client.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"username": "admin", "password": "password123"}
    )
    token = response.json()["access_token"]

    # رأس المصادقة
    headers = {"Authorization": f"Bearer {token}"}

    # 2. تسجيل نظام Odoo
    response = await client.post(
        f"{BASE_URL}/api/v1/systems",
        headers=headers,
        json={
            "system_id": "odoo_main",
            "system_type": "odoo",
            "system_version": "17.0",
            "name": "Odoo الإنتاج",
            "connection_config": {
                "url": "https://odoo.example.com",
                "database": "production",
                "username": "admin",
                "password": "secret123"
            }
        }
    )

    # 3. إنشاء عميل
    response = await client.post(
        f"{BASE_URL}/api/v1/systems/odoo_main/crud",
        headers=headers,
        json={
            "action": "create",
            "model": "res.partner",
            "data": {
                "name": "أحمد السعودي",
                "email": "ahmed@example.com",
                "phone": "+966501234567"
            }
        }
    )
    partner = response.json()["result"]
    print(f"تم إنشاء العميل: {partner['id']}")

    # 4. قراءة العملاء
    response = await client.post(
        f"{BASE_URL}/api/v1/systems/odoo_main/crud",
        headers=headers,
        json={
            "action": "read",
            "model": "res.partner",
            "domain": [["is_company", "=", False]],
            "fields": ["name", "email", "phone"],
            "limit": 10
        }
    )
    partners = response.json()["result"]
    print(f"عدد العملاء: {len(partners)}")
```

---

## 🐛 حل المشكلات

### مشاكل الاتصال

**المشكلة**: لا يمكن الاتصال بنظام Odoo

**الحلول**:
1. تحقق من إمكانية الوصول: `curl https://odoo.example.com`
2. تحقق من بيانات الاعتماد
3. راجع حالة Circuit Breaker: `GET /api/v1/systems/{system_id}/status`
4. راجع سجلات التدقيق للأخطاء

### مشاكل الأداء

**المشكلة**: استجابة API بطيئة

**الحلول**:
1. تحقق من تشغيل Redis: `redis-cli ping`
2. راجع نسبة نجاح الـ cache في metrics
3. راجع أداء استعلامات قاعدة البيانات
4. راقب حالات Circuit Breaker
5. راجع Prometheus metrics

### مشاكل الترقية

**المشكلة**: فشل ترقية الإصدار

**الحلول**:
1. احصل على خطة الترقية أولاً: `await handler.get_migration_plan(...)`
2. راجع التحذيرات في الخطة
3. تحقق من وجود جميع الحقول المطلوبة
4. اختبر مع سجل واحد أولاً
5. راجع سجلات الترقية

---

## 🤝 المساهمة

نرحب بالمساهمات! يرجى:

1. Fork المشروع
2. إنشاء branch للميزة الجديدة
3. Commit التغييرات
4. Push إلى branch
5. فتح Pull Request

---

## 📞 الدعم

للمشاكل والأسئلة:
- **GitHub Issues**: https://github.com/geniustep/BridgeCore/issues
- **البريد الإلكتروني**: support@example.com
- **التوثيق**: راجع `DOCUMENTATION.md`

---

## 📜 الترخيص

MIT License - راجع ملف LICENSE للتفاصيل

---

## 🎯 الخطوات التالية

### للبدء مع BridgeCore:
1. ✅ اقرأ هذا الـ README
2. ✅ راجع `DOCUMENTATION.md` للتوثيق الكامل
3. ✅ نفذ البدء السريع أعلاه
4. ✅ جرب API endpoints

### للدمج مع gmobile:
1. ✅ اقرأ `GMOBILE_INTEGRATION_PLAN.md`
2. ✅ استخدم Prompts من `PROMPT_GMOBILE_ANALYSIS.md`
3. ✅ احصل على تحليل شامل من Claude
4. ✅ نفذ النظام المتوازي
5. ✅ اختبر وقارن
6. ✅ انتقل تدريجياً

---

## 🌟 الميزات القادمة (Roadmap)

- [ ] دعم SAP adapter
- [ ] دعم Salesforce adapter
- [ ] GraphQL API
- [ ] Mobile SDKs (Flutter, React Native)
- [ ] Admin Dashboard
- [ ] Multi-tenancy support
- [ ] Advanced caching strategies
- [ ] Real-time data sync

---

**آخر تحديث**: 2024-01-15
**الإصدار**: 1.0.0
**المؤلف**: BridgeCore Team

</div>
