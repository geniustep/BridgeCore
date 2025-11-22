# Odoo Fields Check Feature

## Overview
خيار اختياري في endpoint تسجيل الدخول للتحقق من وجود model وحقول معينة في Odoo وإرجاع قيمها.

## Endpoint
```
POST /api/v1/auth/tenant/login
```

## Request Body

### تسجيل دخول عادي (بدون فحص حقول)
```json
{
  "email": "user@company.com",
  "password": "password123"
}
```

### تسجيل دخول مع فحص حقول Odoo (اختياري)
```json
{
  "email": "user@company.com",
  "password": "password123",
  "odoo_fields_check": {
    "model": "res.users",
    "list_fields": ["name", "login", "email", "lang", "tz"]
  }
}
```

## Response Structure

### عند عدم طلب فحص الحقول
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": { ... },
  "tenant": { ... },
  "odoo_fields_data": null
}
```

### عند طلب فحص الحقول - حالة النجاح
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": { ... },
  "tenant": { ... },
  "odoo_fields_data": {
    "success": true,
    "model_exists": true,
    "model_name": "User",
    "fields_exist": true,
    "fields_info": {
      "name": {
        "id": 1145,
        "name": "name",
        "field_description": "Name",
        "ttype": "char"
      },
      "email": {
        "id": 1146,
        "name": "email",
        "field_description": "Email",
        "ttype": "char"
      }
    },
    "data": {
      "id": 2,
      "name": "Administrator",
      "login": "done",
      "email": "admin@example.com",
      "lang": "fr_FR",
      "tz": "Africa/Casablanca"
    }
  }
}
```

### عند عدم وجود Model
```json
{
  "odoo_fields_data": {
    "success": false,
    "error": "Model 'custom.model' not found in Odoo",
    "model_exists": false
  }
}
```

### عند وجود حقول ناقصة
```json
{
  "odoo_fields_data": {
    "success": false,
    "model_exists": true,
    "fields_exist": false,
    "existing_fields": ["name", "email"],
    "missing_fields": ["custom_field1", "custom_field2"],
    "error": "Missing fields: custom_field1, custom_field2"
  }
}
```

## Use Cases

### 1. التحقق من Custom Fields عند تسجيل الدخول
```json
{
  "email": "user@company.com",
  "password": "password123",
  "odoo_fields_check": {
    "model": "res.users",
    "list_fields": ["x_custom_field1", "x_custom_field2", "x_custom_field3"]
  }
}
```

### 2. الحصول على معلومات إضافية من الموظف
```json
{
  "email": "user@company.com",
  "password": "password123",
  "odoo_fields_check": {
    "model": "hr.employee",
    "list_fields": ["name", "department_id", "job_id", "work_phone"]
  }
}
```

### 3. التحقق من إعدادات الشركة
```json
{
  "email": "user@company.com",
  "password": "password123",
  "odoo_fields_check": {
    "model": "res.company",
    "list_fields": ["name", "currency_id", "country_id"]
  }
}
```

## Features

### ✅ التحقق من وجود Model
- يتحقق من وجود الـ model في Odoo قبل محاولة الوصول إليه
- يرجع خطأ واضح إذا كان الـ model غير موجود

### ✅ التحقق من وجود الحقول
- يتحقق من وجود كل حقل في قائمة `list_fields`
- يرجع قائمة بالحقول الموجودة والحقول الناقصة
- يرجع معلومات عن كل حقل (type, description)

### ✅ إرجاع البيانات
- إذا كانت كل الحقول موجودة، يقوم بجلب البيانات من Odoo
- يرجع قيم الحقول المطلوبة للمستخدم الحالي

### ✅ معالجة الأخطاء
- يتعامل مع أخطاء الاتصال بـ Odoo
- يتعامل مع أخطاء المصادقة
- يتعامل مع أخطاء الاستعلام

## Implementation Details

### الخطوات التي يتم تنفيذها:

1. **تسجيل الدخول العادي**: يتم أولاً التحقق من بيانات المستخدم في BridgeCore
2. **الاتصال بـ Odoo**: يتم إنشاء اتصال مع Odoo باستخدام بيانات الـ tenant
3. **التحقق من Model**: استعلام `ir.model` للتحقق من وجود الـ model
4. **التحقق من الحقول**: استعلام `ir.model.fields` للتحقق من وجود الحقول
5. **جلب البيانات**: إذا نجحت كل الخطوات، يتم جلب البيانات من الـ model المطلوب
6. **إرجاع النتيجة**: يتم إرجاع النتيجة مع response تسجيل الدخول

### Performance Considerations

- ⚠️ هذا الخيار **اختياري** ولا يؤثر على سرعة تسجيل الدخول العادي
- ⚠️ عند استخدامه، يضيف حوالي 1-2 ثانية لوقت الاستجابة (بسبب استعلامات Odoo الإضافية)
- ✅ يستخدم نفس session الـ authentication، لا يحتاج اتصال إضافي

## Examples

### مثال 1: Flutter App - التحقق من Custom Fields
```dart
final response = await http.post(
  Uri.parse('https://api.bridgecore.com/api/v1/auth/tenant/login'),
  headers: {'Content-Type': 'application/json'},
  body: jsonEncode({
    'email': 'user@company.com',
    'password': 'password123',
    'odoo_fields_check': {
      'model': 'res.users',
      'list_fields': ['x_employee_code', 'x_department', 'x_manager_id']
    }
  }),
);

final data = jsonDecode(response.body);
if (data['odoo_fields_data']?['success'] == true) {
  final customFields = data['odoo_fields_data']['data'];
  print('Employee Code: ${customFields['x_employee_code']}');
}
```

### مثال 2: JavaScript - التحقق من وجود Model
```javascript
const response = await fetch('https://api.bridgecore.com/api/v1/auth/tenant/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@company.com',
    password: 'password123',
    odoo_fields_check: {
      model: 'custom.module.model',
      list_fields: ['field1', 'field2']
    }
  })
});

const data = await response.json();
if (!data.odoo_fields_data.model_exists) {
  console.error('Custom module not installed in Odoo!');
}
```

## Best Practices

1. **استخدمه فقط عند الحاجة**: لا تستخدم هذا الخيار في كل تسجيل دخول، فقط عندما تحتاج التحقق من الحقول
2. **Cache النتائج**: إذا كانت الحقول ثابتة، قم بحفظ النتيجة في local storage
3. **معالجة الأخطاء**: تأكد من معالجة حالة عدم وجود الحقول في تطبيقك
4. **حدد الحقول المطلوبة فقط**: لا تطلب حقول غير ضرورية لتحسين الأداء

## Error Codes

| الحالة | `success` | `model_exists` | `fields_exist` | الوصف |
|--------|-----------|----------------|----------------|--------|
| نجاح كامل | `true` | `true` | `true` | كل شيء موجود والبيانات متاحة |
| Model غير موجود | `false` | `false` | - | الـ model غير موجود في Odoo |
| حقول ناقصة | `false` | `true` | `false` | الـ model موجود لكن بعض الحقول ناقصة |
| خطأ في الاتصال | `false` | - | - | خطأ في الاتصال بـ Odoo |
| خطأ في المصادقة | `false` | - | - | فشل في المصادقة مع Odoo |

