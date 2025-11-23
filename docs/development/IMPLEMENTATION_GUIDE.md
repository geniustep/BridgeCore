# 🛠️ دليل التنفيذ - bridgecore_flutter Operations

**الهدف:** دليل عملي لتنفيذ العمليات الناقصة  
**التاريخ:** نوفمبر 2024

---

## 📁 هيكل الملفات المقترح

```
lib/src/odoo/
├── odoo_service.dart               ← الواجهة الرئيسية
├── operations/                     ← NEW
│   ├── crud_operations.dart        ← CRUD (read, create, write, unlink)
│   ├── search_operations.dart      ← Search (search, search_read, search_count)
│   ├── advanced_operations.dart    ← Advanced (onchange, read_group, etc.)
│   ├── name_operations.dart        ← Name ops (name_search, name_get, name_create)
│   ├── metadata_operations.dart    ← Metadata (fields_get, default_get)
│   ├── permission_operations.dart  ← Permissions (check_access_rights)
│   └── utility_operations.dart     ← Utilities (copy, exists)
├── models/                         ← NEW
│   ├── onchange_result.dart
│   ├── name_search_result.dart
│   ├── field_info.dart
│   └── read_group_result.dart
├── field_presets.dart
└── field_fallback_strategy.dart
```

---

## 1. CRUD Operations

### File: `lib/src/odoo/operations/crud_operations.dart`

```dart
import 'package:bridgecore_flutter/src/odoo/field_presets.dart';

/// Mixin for CRUD operations
mixin CrudOperations {
  /// Execute RPC call (implemented in OdooService)
  Future<dynamic> executeRpc({
    required String model,
    required String method,
    List<dynamic>? args,
    Map<String, dynamic>? kwargs,
  });

  /// Resolve fields from preset or explicit list
  List<String> resolveFields(
    List<String>? fields,
    FieldPreset? preset,
    String model,
  );

  /// قراءة حقول محددة من سجلات
  ///
  /// Example:
  /// ```dart
  /// final partners = await odoo.read(
  ///   model: 'res.partner',
  ///   ids: [1, 2, 3],
  ///   fields: ['name', 'email', 'phone'],
  /// );
  /// ```
  ///
  /// See: Section 2 in Odoo API Guide
  Future<List<Map<String, dynamic>>> read({
    required String model,
    required List<int> ids,
    List<String>? fields,
    FieldPreset? preset,
  }) async {
    if (ids.isEmpty) return [];

    final effectiveFields = resolveFields(fields, preset, model);

    try {
      final result = await executeRpc(
        model: model,
        method: 'read',
        args: [ids],
        kwargs: {
          if (effectiveFields.isNotEmpty) 'fields': effectiveFields,
        },
      );

      return List<Map<String, dynamic>>.from(result);
    } catch (e) {
      // Handle errors
      rethrow;
    }
  }

  /// إنشاء سجل جديد
  ///
  /// Example:
  /// ```dart
  /// final id = await odoo.create(
  ///   model: 'res.partner',
  ///   values: {'name': 'New Company', 'is_company': true},
  /// );
  /// ```
  Future<int> create({
    required String model,
    required Map<String, dynamic> values,
  }) async {
    final result = await executeRpc(
      model: model,
      method: 'create',
      args: [values],
    );

    return result as int;
  }

  /// تحديث سجل/سجلات
  ///
  /// Example:
  /// ```dart
  /// await odoo.update(
  ///   model: 'res.partner',
  ///   ids: [123],
  ///   values: {'phone': '+966501234567'},
  /// );
  /// ```
  Future<bool> update({
    required String model,
    required List<int> ids,
    required Map<String, dynamic> values,
  }) async {
    if (ids.isEmpty) return false;

    final result = await executeRpc(
      model: model,
      method: 'write',
      args: [ids, values],
    );

    return result as bool;
  }

  /// حذف سجل/سجلات
  ///
  /// Example:
  /// ```dart
  /// await odoo.delete(
  ///   model: 'res.partner',
  ///   ids: [123, 456],
  /// );
  /// ```
  Future<bool> delete({
    required String model,
    required List<int> ids,
  }) async {
    if (ids.isEmpty) return false;

    final result = await executeRpc(
      model: model,
      method: 'unlink',
      args: [ids],
    );

    return result as bool;
  }
}
```

---

## 2. Search Operations

### File: `lib/src/odoo/operations/search_operations.dart`

```dart
import 'package:bridgecore_flutter/src/odoo/field_presets.dart';

/// Mixin for search operations
mixin SearchOperations {
  Future<dynamic> executeRpc({
    required String model,
    required String method,
    List<dynamic>? args,
    Map<String, dynamic>? kwargs,
  });

  List<String> resolveFields(
    List<String>? fields,
    FieldPreset? preset,
    String model,
  );

  /// بحث يرجع IDs فقط
  ///
  /// Example:
  /// ```dart
  /// final ids = await odoo.search(
  ///   model: 'res.partner',
  ///   domain: [['is_company', '=', true]],
  ///   limit: 100,
  ///   order: 'name ASC',
  /// );
  /// ```
  ///
  /// See: Section 3 in Odoo API Guide
  Future<List<int>> search({
    required String model,
    List<dynamic>? domain,
    int? limit,
    int? offset,
    String? order,
  }) async {
    try {
      final result = await executeRpc(
        model: model,
        method: 'search',
        args: [domain ?? []],
        kwargs: {
          if (limit != null) 'limit': limit,
          if (offset != null) 'offset': offset,
          if (order != null) 'order': order,
        },
      );

      return List<int>.from(result);
    } catch (e) {
      rethrow;
    }
  }

  /// بحث وقراءة في عملية واحدة
  ///
  /// Example:
  /// ```dart
  /// final partners = await odoo.searchRead(
  ///   model: 'res.partner',
  ///   domain: [['is_company', '=', true]],
  ///   fields: ['name', 'email'],
  ///   limit: 50,
  /// );
  /// ```
  Future<List<Map<String, dynamic>>> searchRead({
    required String model,
    List<dynamic>? domain,
    List<String>? fields,
    FieldPreset? preset,
    int? limit,
    int? offset,
    String? order,
    bool useSmartFallback = true,
  }) async {
    final effectiveFields = resolveFields(fields, preset, model);

    try {
      final result = await executeRpc(
        model: model,
        method: 'search_read',
        args: [domain ?? []],
        kwargs: {
          if (effectiveFields.isNotEmpty) 'fields': effectiveFields,
          if (limit != null) 'limit': limit,
          if (offset != null) 'offset': offset,
          if (order != null) 'order': order,
        },
      );

      return List<Map<String, dynamic>>.from(result);
    } catch (e) {
      if (useSmartFallback) {
        // Apply smart fallback
        // ... implementation
      }
      rethrow;
    }
  }

  /// عد السجلات المطابقة
  ///
  /// Example:
  /// ```dart
  /// final count = await odoo.searchCount(
  ///   model: 'res.partner',
  ///   domain: [['is_company', '=', true]],
  /// );
  /// ```
  Future<int> searchCount({
    required String model,
    List<dynamic>? domain,
  }) async {
    try {
      final result = await executeRpc(
        model: model,
        method: 'search_count',
        args: [domain ?? []],
      );

      return result as int;
    } catch (e) {
      rethrow;
    }
  }
}
```

---

## 3. Advanced Operations

### File: `lib/src/odoo/operations/advanced_operations.dart`

```dart
import 'package:bridgecore_flutter/src/odoo/models/onchange_result.dart';

/// Mixin for advanced operations
mixin AdvancedOperations {
  Future<dynamic> executeRpc({
    required String model,
    required String method,
    List<dynamic>? args,
    Map<String, dynamic>? kwargs,
  });

  /// تنفيذ onchange لحساب القيم التلقائية
  ///
  /// Example:
  /// ```dart
  /// final result = await odoo.onchange(
  ///   model: 'sale.order.line',
  ///   ids: [],
  ///   values: {
  ///     'product_id': 123,
  ///     'product_uom_qty': 5.0,
  ///   },
  ///   field: 'product_id',
  ///   spec: {
  ///     'product_id': '1',
  ///     'price_unit': '1',
  ///   },
  /// );
  ///
  /// // استخدام القيم المحدثة
  /// final updatedPrice = result.value['price_unit'];
  /// ```
  ///
  /// See: Section 8 in Odoo API Guide
  Future<OnchangeResult> onchange({
    required String model,
    List<int> ids = const [],
    required Map<String, dynamic> values,
    required String field,
    required Map<String, dynamic> spec,
  }) async {
    try {
      final result = await executeRpc(
        model: model,
        method: 'onchange',
        args: [
          ids,
          values,
          field,
          spec,
        ],
      );

      return OnchangeResult.fromMap(result as Map<String, dynamic>);
    } catch (e) {
      rethrow;
    }
  }

  /// قراءة بيانات مجمعة (للتقارير)
  ///
  /// Example:
  /// ```dart
  /// final report = await odoo.readGroup(
  ///   model: 'sale.order',
  ///   domain: [['state', '=', 'sale']],
  ///   fields: ['amount_total'],
  ///   groupby: ['partner_id'],
  ///   orderby: 'amount_total desc',
  /// );
  /// ```
  ///
  /// See: Section 4 in Odoo API Guide
  Future<List<Map<String, dynamic>>> readGroup({
    required String model,
    List<dynamic> domain = const [],
    required List<String> fields,
    required List<String> groupby,
    int? offset,
    int? limit,
    String? orderby,
    bool lazy = true,
  }) async {
    try {
      final result = await executeRpc(
        model: model,
        method: 'read_group',
        args: [domain, fields, groupby],
        kwargs: {
          if (offset != null) 'offset': offset,
          if (limit != null) 'limit': limit,
          if (orderby != null) 'orderby': orderby,
          'lazy': lazy,
        },
      );

      return List<Map<String, dynamic>>.from(result);
    } catch (e) {
      rethrow;
    }
  }

  /// نسخ سجل مع قيم مخصصة
  ///
  /// Example:
  /// ```dart
  /// final newId = await odoo.copy(
  ///   model: 'sale.order',
  ///   id: 123,
  ///   defaults: {'date_order': '2024-12-01'},
  /// );
  /// ```
  Future<int> copy({
    required String model,
    required int id,
    Map<String, dynamic>? defaults,
  }) async {
    try {
      final result = await executeRpc(
        model: model,
        method: 'copy',
        args: [id, defaults ?? {}],
      );

      return result as int;
    } catch (e) {
      rethrow;
    }
  }
}
```

---

## 4. Name Operations

### File: `lib/src/odoo/operations/name_operations.dart`

```dart
import 'package:bridgecore_flutter/src/odoo/models/name_search_result.dart';

/// Mixin for name-related operations
mixin NameOperations {
  Future<dynamic> executeRpc({
    required String model,
    required String method,
    List<dynamic>? args,
    Map<String, dynamic>? kwargs,
  });

  /// بحث بالاسم (للـ autocomplete)
  ///
  /// Example:
  /// ```dart
  /// final results = await odoo.nameSearch(
  ///   model: 'res.partner',
  ///   name: 'ahmed',
  ///   domain: [['is_company', '=', true]],
  ///   limit: 10,
  /// );
  /// ```
  ///
  /// See: Section 4 in Odoo API Guide
  Future<List<NameSearchResult>> nameSearch({
    required String model,
    String name = '',
    List<dynamic>? domain,
    String operator = 'ilike',
    int limit = 100,
  }) async {
    try {
      final result = await executeRpc(
        model: model,
        method: 'name_search',
        args: [name, domain ?? [], operator, limit],
      );

      return (result as List)
          .map((item) => NameSearchResult(
                id: item[0] as int,
                displayName: item[1] as String,
              ))
          .toList();
    } catch (e) {
      rethrow;
    }
  }

  /// الحصول على اسم العرض
  ///
  /// Example:
  /// ```dart
  /// final names = await odoo.nameGet(
  ///   model: 'res.partner',
  ///   ids: [1, 2, 3],
  /// );
  /// ```
  Future<List<NameSearchResult>> nameGet({
    required String model,
    required List<int> ids,
  }) async {
    if (ids.isEmpty) return [];

    try {
      final result = await executeRpc(
        model: model,
        method: 'name_get',
        args: [ids],
      );

      return (result as List)
          .map((item) => NameSearchResult(
                id: item[0] as int,
                displayName: item[1] as String,
              ))
          .toList();
    } catch (e) {
      rethrow;
    }
  }

  /// إنشاء سجل بالاسم فقط
  ///
  /// Example:
  /// ```dart
  /// final result = await odoo.nameCreate(
  ///   model: 'res.partner',
  ///   name: 'New Partner',
  /// );
  /// ```
  Future<NameSearchResult> nameCreate({
    required String model,
    required String name,
  }) async {
    try {
      final result = await executeRpc(
        model: model,
        method: 'name_create',
        args: [name],
      );

      return NameSearchResult(
        id: result[0] as int,
        displayName: result[1] as String,
      );
    } catch (e) {
      rethrow;
    }
  }
}
```

---

## 5. Models

### File: `lib/src/odoo/models/onchange_result.dart`

```dart
/// نتيجة عملية onchange
class OnchangeResult {
  /// القيم المحدثة
  final Map<String, dynamic> value;

  /// تحذيرات إن وجدت
  final OnchangeWarning? warning;

  /// Domains محدثة للحقول
  final Map<String, dynamic>? domain;

  OnchangeResult({
    required this.value,
    this.warning,
    this.domain,
  });

  factory OnchangeResult.fromMap(Map<String, dynamic> map) {
    return OnchangeResult(
      value: Map<String, dynamic>.from(map['value'] ?? {}),
      warning: map['warning'] != null
          ? OnchangeWarning.fromMap(map['warning'])
          : null,
      domain: map['domain'] != null
          ? Map<String, dynamic>.from(map['domain'])
          : null,
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'value': value,
      if (warning != null) 'warning': warning!.toMap(),
      if (domain != null) 'domain': domain,
    };
  }
}

/// تحذير من onchange
class OnchangeWarning {
  final String title;
  final String message;
  final String? type;

  OnchangeWarning({
    required this.title,
    required this.message,
    this.type,
  });

  factory OnchangeWarning.fromMap(Map<String, dynamic> map) {
    return OnchangeWarning(
      title: map['title'] ?? '',
      message: map['message'] ?? '',
      type: map['type'],
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'title': title,
      'message': message,
      if (type != null) 'type': type,
    };
  }
}
```

### File: `lib/src/odoo/models/name_search_result.dart`

```dart
/// نتيجة name_search أو name_get
class NameSearchResult {
  final int id;
  final String displayName;

  NameSearchResult({
    required this.id,
    required this.displayName,
  });

  @override
  String toString() => displayName;

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is NameSearchResult && other.id == id;
  }

  @override
  int get hashCode => id.hashCode;
}
```

### File: `lib/src/odoo/models/field_info.dart`

```dart
/// معلومات حقل
class FieldInfo {
  /// اسم العرض
  final String string;

  /// نوع الحقل (char, integer, many2one, etc.)
  final String type;

  /// هل الحقل مطلوب
  final bool required;

  /// نص المساعدة
  final String? help;

  /// هل الحقل للقراءة فقط
  final bool readonly;

  /// حجم الحقل (للـ char)
  final int? size;

  /// القيمة الافتراضية
  final dynamic defaultValue;

  FieldInfo({
    required this.string,
    required this.type,
    this.required = false,
    this.help,
    this.readonly = false,
    this.size,
    this.defaultValue,
  });

  factory FieldInfo.fromMap(Map<String, dynamic> map) {
    return FieldInfo(
      string: map['string'] ?? '',
      type: map['type'] ?? 'char',
      required: map['required'] ?? false,
      help: map['help'],
      readonly: map['readonly'] ?? false,
      size: map['size'],
      defaultValue: map['default'],
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'string': string,
      'type': type,
      'required': required,
      if (help != null) 'help': help,
      'readonly': readonly,
      if (size != null) 'size': size,
      if (defaultValue != null) 'default': defaultValue,
    };
  }
}
```

---

## 6. OdooService Integration

### File: `lib/src/odoo/odoo_service.dart` (Updated)

```dart
import 'operations/crud_operations.dart';
import 'operations/search_operations.dart';
import 'operations/advanced_operations.dart';
import 'operations/name_operations.dart';
import 'operations/metadata_operations.dart';
import 'operations/permission_operations.dart';
import 'operations/utility_operations.dart';

/// خدمة Odoo الرئيسية
class OdooService
    with
        CrudOperations,
        SearchOperations,
        AdvancedOperations,
        NameOperations,
        MetadataOperations,
        PermissionOperations,
        UtilityOperations {
  final HttpClient _client;

  OdooService(this._client);

  /// تنفيذ استدعاء RPC
  @override
  Future<dynamic> executeRpc({
    required String model,
    required String method,
    List<dynamic>? args,
    Map<String, dynamic>? kwargs,
  }) async {
    // Implementation using _client
    // ...
  }

  /// حل الحقول من preset أو قائمة
  @override
  List<String> resolveFields(
    List<String>? fields,
    FieldPreset? preset,
    String model,
  ) {
    if (fields != null && fields.isNotEmpty) {
      return fields;
    }

    if (preset != null) {
      return FieldPresetsManager.getFields(model, preset);
    }

    return [];
  }

  // جميع العمليات متاحة الآن من الـ mixins
  // - read(), create(), update(), delete() من CrudOperations
  // - search(), searchRead(), searchCount() من SearchOperations
  // - onchange(), readGroup(), copy() من AdvancedOperations
  // - nameSearch(), nameGet(), nameCreate() من NameOperations
  // - etc.
}
```

---

## 7. Testing Template

### File: `test/unit/crud_test.dart`

```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:bridgecore_flutter/bridgecore_flutter.dart';

void main() {
  group('CRUD Operations', () {
    late OdooService odoo;

    setUp(() {
      // Setup mock client
      odoo = OdooService(MockHttpClient());
    });

    test('read() returns correct data', () async {
      // Arrange
      final ids = [1, 2, 3];
      final fields = ['name', 'email'];

      // Act
      final result = await odoo.read(
        model: 'res.partner',
        ids: ids,
        fields: fields,
      );

      // Assert
      expect(result, isA<List<Map<String, dynamic>>>());
      expect(result.length, equals(3));
      expect(result[0]['id'], equals(1));
    });

    test('read() with empty ids returns empty list', () async {
      // Act
      final result = await odoo.read(
        model: 'res.partner',
        ids: [],
        fields: ['name'],
      );

      // Assert
      expect(result, isEmpty);
    });

    test('create() returns new id', () async {
      // Arrange
      final values = {'name': 'Test Partner', 'email': 'test@example.com'};

      // Act
      final id = await odoo.create(
        model: 'res.partner',
        values: values,
      );

      // Assert
      expect(id, isA<int>());
      expect(id, greaterThan(0));
    });

    // ... more tests
  });
}
```

---

## 8. Example Usage

### File: `example/complete_example.dart`

```dart
import 'package:bridgecore_flutter/bridgecore_flutter.dart';

Future<void> main() async {
  // Initialize
  BridgeCore.initialize(
    baseUrl: 'https://api.example.com',
    debugMode: true,
  );

  // Login
  await BridgeCore.instance.auth.login(
    email: 'user@company.com',
    password: 'password',
  );

  final odoo = BridgeCore.instance.odoo;

  // Example 1: Search + Read Pattern
  print('\n=== Search + Read Pattern ===');
  final partnerIds = await odoo.search(
    model: 'res.partner',
    domain: [['is_company', '=', true]],
    limit: 5,
  );
  print('Found ${partnerIds.length} partners');

  final partners = await odoo.read(
    model: 'res.partner',
    ids: partnerIds,
    fields: ['name', 'email', 'phone'],
  );
  for (var partner in partners) {
    print('  - ${partner['name']} (${partner['email']})');
  }

  // Example 2: Onchange for Price Calculation
  print('\n=== Onchange Example ===');
  final onchangeResult = await odoo.onchange(
    model: 'sale.order.line',
    ids: [],
    values: {
      'product_id': 1,
      'product_uom_qty': 5.0,
    },
    field: 'product_id',
    spec: {
      'product_id': '1',
      'price_unit': '1',
      'discount': '1',
    },
  );
  print('Updated price: ${onchangeResult.value['price_unit']}');
  if (onchangeResult.warning != null) {
    print('Warning: ${onchangeResult.warning!.message}');
  }

  // Example 3: Name Search for Autocomplete
  print('\n=== Name Search Example ===');
  final searchResults = await odoo.nameSearch(
    model: 'res.partner',
    name: 'tech',
    domain: [['is_company', '=', true]],
    limit: 5,
  );
  print('Autocomplete results:');
  for (var result in searchResults) {
    print('  [${result.id}] ${result.displayName}');
  }

  // Example 4: Read Group for Reports
  print('\n=== Read Group Example ===');
  final salesReport = await odoo.readGroup(
    model: 'sale.order',
    domain: [['state', 'in', ['sale', 'done']]],
    fields: ['amount_total'],
    groupby: ['partner_id'],
    orderby: 'amount_total desc',
    limit: 10,
  );
  print('Top 10 customers by sales:');
  for (var group in salesReport) {
    print('  ${group['partner_id'][1]}: \$${group['amount_total']}');
  }

  // Example 5: Check Permissions
  print('\n=== Permissions Check ===');
  final canDelete = await odoo.checkAccessRights(
    model: 'sale.order',
    operation: 'unlink',
  );
  print('Can delete sale orders: $canDelete');

  // Example 6: Copy Record
  print('\n=== Copy Record ===');
  final newOrderId = await odoo.copy(
    model: 'sale.order',
    id: 1,
    defaults: {
      'date_order': DateTime.now().toIso8601String(),
    },
  );
  print('New order created with ID: $newOrderId');

  // Logout
  await BridgeCore.instance.auth.logout();
}
```

---

## 🎯 خطوات التنفيذ

### Week 1: Critical Operations
1. ✅ إنشاء ملف `crud_operations.dart` مع `read()`
2. ✅ إنشاء ملف `search_operations.dart` مع `search()`
3. ✅ إنشاء ملف `advanced_operations.dart` مع `onchange()`
4. ✅ إنشاء models المطلوبة
5. ✅ Tests لكل عملية
6. ✅ Documentation

### Week 2: Important Operations
1. ✅ `name_operations.dart`
2. ✅ `metadata_operations.dart`
3. ✅ `permission_operations.dart`
4. ✅ Tests + Examples

### Week 3: Polish
1. ✅ Code review
2. ✅ Refactoring
3. ✅ Complete documentation
4. ✅ Integration tests

---

## 📊 Checklist

- [ ] Create operations/ folder
- [ ] Create models/ folder
- [ ] Implement CrudOperations mixin
- [ ] Implement SearchOperations mixin
- [ ] Implement AdvancedOperations mixin
- [ ] Implement NameOperations mixin
- [ ] Implement MetadataOperations mixin
- [ ] Implement PermissionOperations mixin
- [ ] Implement UtilityOperations mixin
- [ ] Update OdooService to use mixins
- [ ] Create OnchangeResult model
- [ ] Create NameSearchResult model
- [ ] Create FieldInfo model
- [ ] Write unit tests for each operation
- [ ] Write integration tests
- [ ] Update README with new operations
- [ ] Create examples
- [ ] Update CHANGELOG

---

**Status:** 🟢 Ready for Implementation  
**Last Updated:** نوفمبر 2024
