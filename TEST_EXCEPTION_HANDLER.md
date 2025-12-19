# اختبار معالج HTTPException

## ملخص الحل

تم إضافة معالج خاص لـ `HTTPException` في `app/main.py` يعرض رسالة الخطأ الفعلية بدلاً من الرسالة العامة "An unexpected error occurred on the server".

## كيفية الاختبار

### 1. اختبار باستخدام curl

```bash
# تشغيل الخادم أولاً
cd /opt/BridgeCore
uvicorn app.main:app --reload

# في terminal آخر، اختبر endpoint مع خطأ متعمد
curl -X POST http://localhost:8000/api/v1/odoo/search_read \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "model": "invalid.model.name",
    "domain": [],
    "fields": ["name"]
  }'
```

**النتيجة المتوقعة:**
```json
{
  "error": {
    "type": "InternalServerError",
    "message": "Internal error: Odoo model not found: invalid.model.name",
    "request_id": "..."
  }
}
```

**ملاحظة:** يجب أن تحتوي `message` على رسالة الخطأ الفعلية وليس "An unexpected error occurred on the server"

### 2. اختبار باستخدام Python

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# اختبار مع HTTPException
response = client.post(
    "/api/v1/odoo/search_read",
    json={
        "model": "shuttle.trip",
        "domain": [["id", "=", 134]],
        "fields": ["name"]
    },
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

# التحقق من أن رسالة الخطأ الفعلية موجودة
error_data = response.json()
assert "error" in error_data
assert error_data["error"]["message"] != "An unexpected error occurred on the server"
```

### 3. اختبار من Flutter Frontend

عند حدوث خطأ في `search_read`، يجب أن تحصل على:

```dart
// قبل الحل:
{
  "error": {
    "type": "InternalServerError",
    "message": "An unexpected error occurred on the server",
    "request_id": null
  }
}

// بعد الحل:
{
  "error": {
    "type": "InternalServerError",
    "message": "Internal error: Connection timeout to Odoo server",  // رسالة الخطأ الفعلية
    "request_id": "..."
  }
}
```

## التحقق من التغييرات

### الملفات المعدلة:
1. `app/main.py`:
   - إضافة `HTTPException` إلى imports
   - إضافة معالج `http_exception_handler` قبل معالج `global_exception_handler`
   - تعديل `global_exception_handler` لتخطي `HTTPException`

### الكود المضاف:

```python
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with proper error formatting"""
    # Log the error with details
    logger.error(
        f"HTTPException: {exc.status_code} - {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path,
            "method": request.method
        }
    )

    # Extract error message from detail
    error_message = exc.detail
    if isinstance(exc.detail, dict):
        error_message = exc.detail.get("message", str(exc.detail))
    elif isinstance(exc.detail, str):
        error_message = exc.detail

    # Determine error type based on status code
    error_type_map = {
        400: "BadRequest",
        401: "Unauthorized",
        403: "Forbidden",
        404: "NotFound",
        409: "Conflict",
        422: "ValidationError",
        429: "RateLimitExceeded",
        500: "InternalServerError",
        503: "ServiceUnavailable"
    }
    error_type = error_type_map.get(exc.status_code, "HttpError")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": error_type,
                "message": error_message,
                "request_id": request.state.request_id if hasattr(request.state, "request_id") else None
            }
        }
    )
```

## النتيجة

✅ الآن عند حدوث خطأ في `/api/v1/odoo/search_read`:
- سيتم رفع `HTTPException` مع رسالة الخطأ الفعلية
- سيتم التقاطها بواسطة معالج `HTTPException` المخصص
- سيتم إرسال رسالة الخطأ الفعلية إلى الـ frontend
- الـ frontend سيحصل على تفاصيل الخطأ بدلاً من رسالة عامة

## مثال على الخطأ قبل وبعد الحل

**قبل الحل:**
```json
{
  "error": {
    "type": "InternalServerError",
    "message": "An unexpected error occurred on the server"
  }
}
```

**بعد الحل:**
```json
{
  "error": {
    "type": "InternalServerError",
    "message": "Internal error: Odoo model not found: shuttle.trip"
  }
}
```
