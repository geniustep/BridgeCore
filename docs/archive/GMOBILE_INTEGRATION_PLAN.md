# خطة دمج BridgeCore مع مشروع gmobile - نظام متوازي للتجربة

## نظرة عامة

هذا المستند يحدد خطة شاملة لإنشاء نظام متوازي في مشروع gmobile يستخدم BridgeCore middleware، مع الحفاظ على النظام القديم دون مساس للتجربة والمقارنة.

---

## المرحلة الأولى: تحليل البنية الحالية لـ gmobile

### 1. تحليل طبقة الاتصال الحالية

**الهدف**: فهم كيفية اتصال gmobile مع Odoo حالياً

**المهام المطلوبة**:

```
قم بتحليل مشروع gmobile (https://github.com/geniustep/gmobile/tree/dev) وحدد:

1. **طبقة الخدمات الحالية**:
   - ما هي الملفات المسؤولة عن الاتصال بـ Odoo؟
   - أين يتم استخدام odoo_adapter؟
   - ما هي الـ models التي يتعامل معها التطبيق؟
   - كيف يتم إدارة الجلسات (session management)؟

2. **نقاط النهاية (Endpoints)**:
   - قائمة بجميع الـ API calls الموجودة
   - Models المستخدمة: (res.partner, product.product, sale.order, إلخ)
   - العمليات: (create, read, update, delete, search)

3. **إدارة الحالة (State Management)**:
   - ما هو نظام إدارة الحالة المستخدم؟ (Provider, Bloc, Riverpod, GetX)
   - أين يتم تخزين بيانات Odoo في التطبيق؟
   - كيف يتم التعامل مع الـ cache؟

4. **المصادقة (Authentication)**:
   - كيف يتم تسجيل الدخول؟
   - أين يتم تخزين الـ tokens؟
   - كيف يتم تجديد الجلسة؟

5. **معالجة الأخطاء**:
   - كيف يتم التعامل مع أخطاء الشبكة؟
   - ما هي رسائل الخطأ الموجودة؟
   - هل يوجد retry logic؟

قم بإنشاء تقرير شامل يحتوي على:
- خريطة للملفات المهمة
- رسم بياني للبنية الحالية
- قائمة بجميع الـ dependencies المتعلقة بـ Odoo
```

### 2. تحديد نقاط الضعف والتحديات

**الهدف**: معرفة المشاكل التي يمكن أن يحلها BridgeCore

**المهام المطلوبة**:

```
حدد في مشروع gmobile الحالي:

1. **مشاكل الأداء**:
   - هل توجد مكالمات API متكررة يمكن تحسينها؟
   - هل يوجد caching كافي؟
   - ما هي العمليات البطيئة؟

2. **مشاكل الموثوقية**:
   - كيف يتم التعامل مع انقطاع الاتصال؟
   - هل يوجد circuit breaker أو retry mechanism؟
   - كيف يتم التعامل مع timeouts؟

3. **مشاكل الصيانة**:
   - هل الكود مكرر في أماكن متعددة؟
   - هل يسهل إضافة features جديدة؟
   - كيف يتم التعامل مع تحديثات Odoo؟

4. **مشاكل الأمان**:
   - أين يتم تخزين credentials؟
   - هل البيانات الحساسة مشفرة؟
   - كيف يتم التعامل مع الـ authentication؟
```

---

## المرحلة الثانية: تصميم النظام المتوازي

### 1. البنية المقترحة

**الهدف**: إنشاء طبقة جديدة تستخدم BridgeCore مع الحفاظ على القديمة

**التصميم**:

```
lib/
├── core/
│   ├── api/
│   │   ├── odoo_direct/              # النظام القديم (الحالي)
│   │   │   ├── odoo_adapter.dart
│   │   │   ├── odoo_client.dart
│   │   │   └── models/
│   │   │
│   │   └── bridgecore/               # النظام الجديد (متوازي)
│   │       ├── bridgecore_client.dart
│   │       ├── bridgecore_service.dart
│   │       ├── models/
│   │       └── interceptors/
│   │
│   ├── config/
│   │   └── api_config.dart           # تبديل بين النظامين
│   │
│   └── services/
│       ├── partner_service.dart       # واجهة موحدة
│       ├── product_service.dart       # تستخدم أي من النظامين
│       └── sale_service.dart
│
├── features/
│   └── [features]/
│       └── data/
│           └── repositories/
│               └── [feature]_repository.dart  # يستخدم الواجهة الموحدة
│
└── main.dart
```

### 2. استراتيجية التبديل

**الهدف**: القدرة على التبديل بين النظامين بسهولة

**الكود المقترح**:

```dart
// lib/core/config/api_config.dart

enum ApiMode {
  odoo_direct,    // الاتصال المباشر بـ Odoo (النظام القديم)
  bridgecore,     // عبر BridgeCore middleware (النظام الجديد)
}

class ApiConfig {
  static ApiMode currentMode = ApiMode.odoo_direct; // افتراضي: النظام القديم

  // يمكن التبديل من الإعدادات
  static bool get useBridgeCore => currentMode == ApiMode.bridgecore;

  // URLs
  static String get odooUrl => 'https://odoo.example.com';
  static String get bridgeCoreUrl => 'https://api.bridgecore.com';

  // للتجربة A/B Testing
  static bool get enableABTesting => true;
  static double get bridgeCoreUserPercentage => 0.10; // 10% من المستخدمين
}
```

```dart
// lib/core/api/base_api_client.dart

abstract class BaseApiClient {
  Future<Map<String, dynamic>> create(String model, Map<String, dynamic> data);
  Future<List<dynamic>> read(String model, List<dynamic> domain);
  Future<bool> update(String model, int id, Map<String, dynamic> data);
  Future<bool> delete(String model, int id);
}

class ApiClientFactory {
  static BaseApiClient create() {
    if (ApiConfig.useBridgeCore) {
      return BridgeCoreClient();
    } else {
      return OdooDirectClient();
    }
  }
}
```

### 3. تطبيق BridgeCore Client

**الهدف**: إنشاء client للاتصال بـ BridgeCore

**الكود المقترح**:

```dart
// lib/core/api/bridgecore/bridgecore_client.dart

import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class BridgeCoreClient extends BaseApiClient {
  final Dio _dio;
  final FlutterSecureStorage _storage;
  final String _baseUrl = ApiConfig.bridgeCoreUrl;

  String? _accessToken;
  String? _systemId;

  BridgeCoreClient()
    : _dio = Dio(),
      _storage = FlutterSecureStorage() {
    _setupInterceptors();
  }

  void _setupInterceptors() {
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        // إضافة token
        if (_accessToken != null) {
          options.headers['Authorization'] = 'Bearer $_accessToken';
        }
        return handler.next(options);
      },
      onError: (error, handler) async {
        // تجديد token عند انتهاء الصلاحية
        if (error.response?.statusCode == 401) {
          if (await _refreshToken()) {
            // إعادة المحاولة
            return handler.resolve(await _retry(error.requestOptions));
          }
        }
        return handler.next(error);
      },
    ));
  }

  Future<void> authenticate(String username, String password) async {
    try {
      final response = await _dio.post(
        '$_baseUrl/api/v1/auth/login',
        data: {
          'username': username,
          'password': password,
        },
      );

      _accessToken = response.data['access_token'];
      final refreshToken = response.data['refresh_token'];

      // حفظ في secure storage
      await _storage.write(key: 'access_token', value: _accessToken);
      await _storage.write(key: 'refresh_token', value: refreshToken);
    } catch (e) {
      throw ApiException('Authentication failed: $e');
    }
  }

  Future<bool> _refreshToken() async {
    try {
      final refreshToken = await _storage.read(key: 'refresh_token');
      if (refreshToken == null) return false;

      final response = await _dio.post(
        '$_baseUrl/api/v1/auth/refresh',
        options: Options(
          headers: {'Authorization': 'Bearer $refreshToken'},
        ),
      );

      _accessToken = response.data['access_token'];
      await _storage.write(key: 'access_token', value: _accessToken);

      return true;
    } catch (e) {
      return false;
    }
  }

  Future<Response> _retry(RequestOptions requestOptions) async {
    final options = Options(
      method: requestOptions.method,
      headers: {
        ...requestOptions.headers,
        'Authorization': 'Bearer $_accessToken',
      },
    );

    return _dio.request(
      requestOptions.path,
      data: requestOptions.data,
      queryParameters: requestOptions.queryParameters,
      options: options,
    );
  }

  @override
  Future<Map<String, dynamic>> create(String model, Map<String, dynamic> data) async {
    try {
      final response = await _dio.post(
        '$_baseUrl/api/v1/systems/$_systemId/crud',
        data: {
          'action': 'create',
          'model': model,
          'data': data,
        },
      );

      return response.data['result'];
    } catch (e) {
      throw ApiException('Create failed: $e');
    }
  }

  @override
  Future<List<dynamic>> read(String model, List<dynamic> domain) async {
    try {
      final response = await _dio.post(
        '$_baseUrl/api/v1/systems/$_systemId/crud',
        data: {
          'action': 'read',
          'model': model,
          'domain': domain,
        },
      );

      return response.data['result'];
    } catch (e) {
      throw ApiException('Read failed: $e');
    }
  }

  @override
  Future<bool> update(String model, int id, Map<String, dynamic> data) async {
    try {
      await _dio.post(
        '$_baseUrl/api/v1/systems/$_systemId/crud',
        data: {
          'action': 'update',
          'model': model,
          'record_id': id,
          'data': data,
        },
      );

      return true;
    } catch (e) {
      throw ApiException('Update failed: $e');
    }
  }

  @override
  Future<bool> delete(String model, int id) async {
    try {
      await _dio.post(
        '$_baseUrl/api/v1/systems/$_systemId/crud',
        data: {
          'action': 'delete',
          'model': model,
          'record_id': id,
        },
      );

      return true;
    } catch (e) {
      throw ApiException('Delete failed: $e');
    }
  }

  // دعم WebSocket للتحديثات الفورية
  Future<void> connectWebSocket(Function(dynamic) onMessage) async {
    // TODO: تطبيق WebSocket connection
  }
}
```

### 4. طبقة الخدمات الموحدة

**الهدف**: واجهة موحدة تعمل مع كلا النظامين

**الكود المقترح**:

```dart
// lib/core/services/partner_service.dart

class PartnerService {
  final BaseApiClient _apiClient = ApiClientFactory.create();

  Future<Partner> createPartner(Partner partner) async {
    final data = await _apiClient.create(
      'res.partner',
      partner.toJson(),
    );

    return Partner.fromJson(data);
  }

  Future<List<Partner>> getPartners({List<dynamic>? domain}) async {
    final data = await _apiClient.read(
      'res.partner',
      domain ?? [],
    );

    return data.map((e) => Partner.fromJson(e)).toList();
  }

  Future<bool> updatePartner(int id, Partner partner) async {
    return await _apiClient.update(
      'res.partner',
      id,
      partner.toJson(),
    );
  }

  Future<bool> deletePartner(int id) async {
    return await _apiClient.delete('res.partner', id);
  }
}
```

---

## المرحلة الثالثة: خطة التنفيذ التدريجية

### الأسبوع 1-2: التحضير

**المهام**:
1. تحليل كامل لمشروع gmobile
2. تحديد الملفات والكود المطلوب تعديله
3. إنشاء branch جديد: `feature/bridgecore-integration`
4. إعداد بيئة التطوير

### الأسبوع 3-4: بناء البنية المتوازية

**المهام**:
1. إنشاء مجلد `bridgecore/` في `lib/core/api/`
2. تطبيق `BridgeCoreClient`
3. إنشاء `ApiClientFactory`
4. تطبيق نظام التبديل `ApiConfig`

### الأسبوع 5-6: دمج الخدمات

**المهام**:
1. تحديث `PartnerService` لاستخدام الواجهة الموحدة
2. تحديث `ProductService`
3. تحديث `SaleService`
4. إضافة unit tests

### الأسبوع 7-8: الاختبار

**المهام**:
1. اختبار النظام القديم (التأكد من عدم كسره)
2. اختبار النظام الجديد (BridgeCore)
3. اختبار التبديل بين النظامين
4. اختبار الأداء والمقارنة

### الأسبوع 9-10: التجربة الميدانية

**المهام**:
1. إطلاق beta لـ 10% من المستخدمين
2. جمع metrics والمقارنة
3. معالجة المشاكل
4. التوسع تدريجياً

---

## المرحلة الرابعة: الاختبار والمقارنة

### 1. Metrics المطلوب قياسها

**الأداء**:
- زمن الاستجابة (Response Time)
- عدد الطلبات الفاشلة (Failed Requests)
- استهلاك البيانات (Data Usage)
- استهلاك البطارية

**الموثوقية**:
- معدل النجاح (Success Rate)
- التعامل مع الأخطاء
- إعادة المحاولات التلقائية

**تجربة المستخدم**:
- سرعة التحميل
- سلاسة الواجهة
- رضا المستخدمين

### 2. أدوات القياس

```dart
// lib/core/analytics/performance_tracker.dart

class PerformanceTracker {
  static final Map<String, List<Duration>> _measurements = {};

  static Future<T> track<T>(
    String operation,
    Future<T> Function() function,
  ) async {
    final stopwatch = Stopwatch()..start();

    try {
      final result = await function();
      stopwatch.stop();

      _recordMeasurement(operation, stopwatch.elapsed);
      _logToAnalytics(operation, stopwatch.elapsed, success: true);

      return result;
    } catch (e) {
      stopwatch.stop();
      _logToAnalytics(operation, stopwatch.elapsed, success: false);
      rethrow;
    }
  }

  static void _recordMeasurement(String operation, Duration duration) {
    if (!_measurements.containsKey(operation)) {
      _measurements[operation] = [];
    }
    _measurements[operation]!.add(duration);
  }

  static Map<String, dynamic> getReport() {
    return _measurements.map((operation, durations) {
      final avg = durations.reduce((a, b) => a + b) / durations.length;
      final min = durations.reduce((a, b) => a < b ? a : b);
      final max = durations.reduce((a, b) => a > b ? a : b);

      return MapEntry(operation, {
        'average': avg.inMilliseconds,
        'min': min.inMilliseconds,
        'max': max.inMilliseconds,
        'count': durations.length,
      });
    });
  }

  static void _logToAnalytics(String operation, Duration duration, {required bool success}) {
    // إرسال إلى Firebase Analytics أو أي نظام آخر
    final apiMode = ApiConfig.useBridgeCore ? 'bridgecore' : 'odoo_direct';

    // FirebaseAnalytics.instance.logEvent(
    //   name: 'api_call',
    //   parameters: {
    //     'operation': operation,
    //     'duration_ms': duration.inMilliseconds,
    //     'api_mode': apiMode,
    //     'success': success,
    //   },
    // );
  }
}

// الاستخدام
final partners = await PerformanceTracker.track(
  'fetch_partners',
  () => partnerService.getPartners(),
);
```

### 3. A/B Testing

```dart
// lib/core/config/ab_testing.dart

class ABTesting {
  static bool shouldUseBridgeCore(String userId) {
    if (!ApiConfig.enableABTesting) {
      return ApiConfig.useBridgeCore;
    }

    // استخدام hash للحصول على توزيع عادل
    final hash = userId.hashCode.abs();
    final percentage = (hash % 100) / 100.0;

    return percentage < ApiConfig.bridgeCoreUserPercentage;
  }
}

// في main.dart أو عند تسجيل الدخول
void setupApiMode(String userId) {
  if (ABTesting.shouldUseBridgeCore(userId)) {
    ApiConfig.currentMode = ApiMode.bridgecore;
  } else {
    ApiConfig.currentMode = ApiMode.odoo_direct;
  }
}
```

---

## المرحلة الخامسة: صفحة الإعدادات للمطورين

### Developer Settings Screen

```dart
// lib/features/settings/presentation/pages/developer_settings_page.dart

class DeveloperSettingsPage extends StatefulWidget {
  @override
  _DeveloperSettingsPageState createState() => _DeveloperSettingsPageState();
}

class _DeveloperSettingsPageState extends State<DeveloperSettingsPage> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('إعدادات المطورين')),
      body: ListView(
        children: [
          SwitchListTile(
            title: Text('استخدام BridgeCore Middleware'),
            subtitle: Text(ApiConfig.useBridgeCore
              ? 'يتم الاتصال عبر BridgeCore'
              : 'الاتصال المباشر بـ Odoo'),
            value: ApiConfig.useBridgeCore,
            onChanged: (value) {
              setState(() {
                ApiConfig.currentMode = value
                  ? ApiMode.bridgecore
                  : ApiMode.odoo_direct;
              });
            },
          ),

          Divider(),

          ListTile(
            title: Text('إحصائيات الأداء'),
            subtitle: Text('عرض metrics المقارنة'),
            trailing: Icon(Icons.chevron_right),
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => PerformanceStatsPage(),
                ),
              );
            },
          ),

          ListTile(
            title: Text('مسح Cache'),
            subtitle: Text('حذف جميع البيانات المخزنة مؤقتاً'),
            trailing: Icon(Icons.delete_outline),
            onTap: () async {
              // مسح cache
              await showDialog(
                context: context,
                builder: (_) => AlertDialog(
                  title: Text('تم مسح Cache'),
                  actions: [
                    TextButton(
                      onPressed: () => Navigator.pop(context),
                      child: Text('حسناً'),
                    ),
                  ],
                ),
              );
            },
          ),

          Divider(),

          SwitchListTile(
            title: Text('تفعيل A/B Testing'),
            subtitle: Text('التبديل التلقائي بين النظامين'),
            value: ApiConfig.enableABTesting,
            onChanged: (value) {
              setState(() {
                ApiConfig.enableABTesting = value;
              });
            },
          ),

          if (ApiConfig.enableABTesting)
            ListTile(
              title: Text('نسبة مستخدمي BridgeCore'),
              subtitle: Slider(
                value: ApiConfig.bridgeCoreUserPercentage,
                min: 0.0,
                max: 1.0,
                divisions: 10,
                label: '${(ApiConfig.bridgeCoreUserPercentage * 100).toInt()}%',
                onChanged: (value) {
                  setState(() {
                    ApiConfig.bridgeCoreUserPercentage = value;
                  });
                },
              ),
            ),
        ],
      ),
    );
  }
}

// صفحة إحصائيات الأداء
class PerformanceStatsPage extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final report = PerformanceTracker.getReport();

    return Scaffold(
      appBar: AppBar(title: Text('إحصائيات الأداء')),
      body: ListView.builder(
        itemCount: report.length,
        itemBuilder: (context, index) {
          final entry = report.entries.elementAt(index);
          final operation = entry.key;
          final stats = entry.value;

          return Card(
            margin: EdgeInsets.all(8),
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    operation,
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  SizedBox(height: 8),
                  Text('متوسط الوقت: ${stats['average']} ms'),
                  Text('أقل وقت: ${stats['min']} ms'),
                  Text('أطول وقت: ${stats['max']} ms'),
                  Text('عدد المرات: ${stats['count']}'),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}
```

---

## المرحلة السادسة: خطة الانتقال الكامل

### السيناريو المثالي

**المرحلة 1 (شهر 1-2)**: التطوير والاختبار الداخلي
- بناء البنية المتوازية
- اختبار شامل
- نسبة BridgeCore: 0%

**المرحلة 2 (شهر 3)**: Beta Testing
- إطلاق لفريق التطوير والمختبرين
- نسبة BridgeCore: 5%
- جمع feedback ومعالجة المشاكل

**المرحلة 3 (شهر 4)**: Soft Launch
- إطلاق لمجموعة محددة من المستخدمين
- نسبة BridgeCore: 20%
- مراقبة مستمرة

**المرحلة 4 (شهر 5)**: التوسع التدريجي
- زيادة النسبة تدريجياً
- نسبة BridgeCore: 50%
- مقارنة شاملة للنتائج

**المرحلة 5 (شهر 6)**: الانتقال الكامل
- نسبة BridgeCore: 100%
- إيقاف النظام القديم (اختياري - يمكن الإبقاء عليه كـ fallback)

### خطة الطوارئ (Rollback Plan)

```dart
// في حالة وجود مشاكل حرجة
class EmergencyRollback {
  static Future<void> rollbackToDirect() async {
    ApiConfig.currentMode = ApiMode.odoo_direct;
    ApiConfig.enableABTesting = false;

    // إشعار المستخدمين
    await showNotification(
      'تم التبديل مؤقتاً للنظام القديم لحل مشكلة تقنية',
    );

    // إرسال تقرير للفريق
    await reportIssue('Emergency rollback executed');
  }
}
```

---

## الملخص التنفيذي

### الفوائد المتوقعة من BridgeCore

✅ **الأداء**:
- تحسين السرعة بفضل Redis caching
- تقليل استهلاك البيانات
- استجابة أسرع

✅ **الموثوقية**:
- Circuit breaker لمنع الفشل المتتالي
- Retry logic ذكي
- معالجة أفضل للأخطاء

✅ **الأمان**:
- تشفير البيانات الحساسة
- Rate limiting لمنع الإساءة
- JWT tokens محسّنة

✅ **الصيانة**:
- كود أنظف وأسهل للصيانة
- إضافة features أسرع
- دعم لعدة أنظمة ERP

✅ **المراقبة**:
- Metrics تفصيلية مع Prometheus
- Error tracking مع Sentry
- Real-time updates عبر WebSocket

### المخاطر وطرق التخفيف

⚠️ **خطر**: انقطاع الخدمة
✅ **التخفيف**: نظام متوازي + rollback فوري

⚠️ **خطر**: مشاكل في الأداء
✅ **التخفيف**: A/B testing + metrics مستمرة

⚠️ **خطر**: bugs في النظام الجديد
✅ **التخفيف**: إطلاق تدريجي + testing شامل

---

## الخطوات التالية

1. **مراجعة هذا المستند** مع الفريق
2. **تحليل gmobile** بناءً على النقاط المذكورة
3. **إنشاء تقدير للوقت والتكلفة**
4. **البدء في المرحلة الأولى**: التحليل
5. **إعداد بيئة التطوير** لـ BridgeCore

---

## ملاحظات مهمة

- هذا النظام المتوازي يضمن **عدم المساس بالنظام القديم**
- يمكن التبديل في أي وقت بين النظامين
- جميع التغييرات backwards-compatible
- النظام القديم يبقى كـ **safety net**
- التجربة والاختبار قبل الانتقال الكامل

---

**تاريخ الإنشاء**: 2024-01-15
**الإصدار**: 1.0
**المؤلف**: BridgeCore Team
