# دليل إعداد BridgeCore

## نظرة عامة

BridgeCore هو API middleware مبني بـ FastAPI لربط تطبيقات Flutter مع أنظمة ERP/CRM الخارجية (Odoo, SAP, Salesforce).

## المتطلبات

- Docker و Docker Compose
- Git
- صلاحيات root (sudo)

## الإعداد السريع

### 1. تشغيل سكريبت الإعداد

```bash
cd /opt/BridgeCore
sudo ./setup.sh
```

سكريبت الإعداد سيقوم بـ:
- إنشاء ملف `.env` مع مفاتيح آمنة
- إنشاء مجلدات logs و SSL
- بناء صور Docker
- تشغيل الحاويات
- تشغيل migrations قاعدة البيانات

### 2. التحقق من الحالة

```bash
cd /opt/BridgeCore/docker
docker-compose ps
```

يجب أن ترى 4 حاويات تعمل:
- `bridgecore_api` - تطبيق FastAPI
- `bridgecore_db` - قاعدة بيانات PostgreSQL
- `bridgecore_redis` - Redis للـ caching
- `bridgecore_nginx` - Nginx كـ reverse proxy

### 3. التحقق من الوصول

```bash
# Health check
curl http://localhost/health

# API Documentation
curl http://localhost/docs
```

## إعداد DNS

لربط النطاق `bridgecore.geniura.com` بالخادم:

1. **إعداد DNS A Record:**
   ```
   Type: A
   Name: bridgecore
   Value: YOUR_SERVER_IP
   TTL: 3600
   ```

2. **التحقق من DNS:**
   ```bash
   dig bridgecore.geniura.com
   # أو
   nslookup bridgecore.geniura.com
   ```

## إعداد SSL (HTTPS)

لإضافة شهادة SSL:

### باستخدام Let's Encrypt (Certbot)

```bash
# تثبيت Certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# الحصول على شهادة SSL
sudo certbot --nginx -d bridgecore.geniura.com

# أو يدوياً
sudo certbot certonly --standalone -d bridgecore.geniura.com
```

بعد الحصول على الشهادة:

1. نسخ الملفات إلى مجلد SSL:
   ```bash
   sudo cp /etc/letsencrypt/live/bridgecore.geniura.com/fullchain.pem /opt/BridgeCore/docker/ssl/
   sudo cp /etc/letsencrypt/live/bridgecore.geniura.com/privkey.pem /opt/BridgeCore/docker/ssl/
   sudo chmod 644 /opt/BridgeCore/docker/ssl/*.pem
   ```

2. تحديث `nginx.conf` لإضافة إعدادات HTTPS

## الأوامر المفيدة

### عرض السجلات

```bash
cd /opt/BridgeCore/docker

# جميع السجلات
docker-compose logs -f

# سجلات API فقط
docker-compose logs -f api

# سجلات قاعدة البيانات
docker-compose logs -f db
```

### إعادة تشغيل الخدمات

```bash
cd /opt/BridgeCore/docker

# إعادة تشغيل جميع الخدمات
docker-compose restart

# إعادة تشغيل خدمة محددة
docker-compose restart api
```

### إيقاف الخدمات

```bash
cd /opt/BridgeCore/docker
docker-compose down
```

### تحديث المشروع

```bash
cd /opt/BridgeCore
git pull
cd docker
docker-compose build
docker-compose up -d
```

### تشغيل Migrations

```bash
cd /opt/BridgeCore/docker
docker-compose exec api alembic upgrade head
```

## إعدادات البيئة (.env)

ملف `.env` يحتوي على جميع إعدادات التطبيق. يمكنك تعديله حسب الحاجة:

```bash
nano /opt/BridgeCore/.env
```

المتغيرات الرئيسية:
- `SECRET_KEY` - مفتاح سري للتطبيق
- `JWT_SECRET_KEY` - مفتاح JWT للمصادقة
- `DATABASE_URL` - رابط قاعدة البيانات
- `REDIS_URL` - رابط Redis
- `CORS_ORIGINS` - النطاقات المسموح بها

## استكشاف الأخطاء

### الحاويات لا تبدأ

```bash
# فحص السجلات
cd /opt/BridgeCore/docker
docker-compose logs

# فحص حالة الحاويات
docker-compose ps
```

### مشاكل قاعدة البيانات

```bash
# فحص اتصال قاعدة البيانات
docker-compose exec db psql -U postgres -d middleware_db -c "SELECT 1;"
```

### مشاكل Redis

```bash
# فحص Redis
docker-compose exec redis redis-cli ping
```

### مشاكل Nginx

```bash
# فحص إعدادات Nginx
docker-compose exec nginx nginx -t

# إعادة تحميل Nginx
docker-compose exec nginx nginx -s reload
```

## الوصول إلى API

بعد الإعداد، يمكنك الوصول إلى:

- **API Base URL:** `http://bridgecore.geniura.com`
- **API Documentation:** `http://bridgecore.geniura.com/docs`
- **ReDoc:** `http://bridgecore.geniura.com/redoc`
- **Health Check:** `http://bridgecore.geniura.com/health`

## الأمان

1. **تغيير كلمات المرور الافتراضية:**
   - قم بتغيير `POSTGRES_PASSWORD` في docker-compose.yml
   - استخدم مفاتيح آمنة في `.env`

2. **إعداد Firewall:**
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

3. **تحديث النظام:**
   ```bash
   sudo apt-get update && sudo apt-get upgrade
   ```

## الدعم

للمساعدة أو الإبلاغ عن مشاكل:
- GitHub Issues: https://github.com/geniustep/BridgeCore/issues

