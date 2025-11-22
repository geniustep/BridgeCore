# 🚀 BridgeCore Flutter SDK - Required Improvements

## 📋 Overview

This document outlines the required improvements and updates for the [BridgeCore Flutter SDK](https://github.com/geniustep/bridgecore_flutter) to align with the latest backend API enhancements.

**Repository**: https://github.com/geniustep/bridgecore_flutter

---

## ✅ Current Status

The Flutter SDK currently supports:
- ✅ Authentication (login, refresh, logout)
- ✅ Odoo Fields Check during login
- ✅ Odoo Operations (searchRead, create, update, delete)
- ✅ Auto Token Refresh
- ✅ Field Presets & Smart Fallback
- ✅ Retry Interceptor
- ✅ Caching & Metrics

---

## 🔴 Missing Critical Features

### 1. **Enhanced `/me` Endpoint Support** ⭐ **HIGH PRIORITY**

**Backend Update**: The `/api/v1/auth/tenant/me` endpoint has been significantly enhanced.

#### Current State:
- ❌ SDK does not have a dedicated `/me` endpoint method
- ❌ Missing support for new Odoo integration fields
- ❌ No support for optional `odoo_fields_check` in `/me`

#### Required Changes:

**A. Add `/me` Method to `AuthService`**

```dart
/// Get current user information with enhanced Odoo data
///
/// Returns comprehensive user info including:
/// - User profile from BridgeCore
/// - Tenant information
/// - Odoo partner_id and employee_id
/// - Odoo groups and permissions
/// - Company information
/// - Optional custom Odoo fields
///
/// Example:
/// ```dart
/// // Basic usage (no custom fields)
/// final userInfo = await BridgeCore.instance.auth.me();
/// print('Partner ID: ${userInfo.partnerId}');
/// print('Is Admin: ${userInfo.isAdmin}');
///
/// // With custom fields
/// final userInfoWithFields = await BridgeCore.instance.auth.me(
///   odooFieldsCheck: OdooFieldsCheck(
///     model: 'res.users',
///     listFields: ['shuttle_role', 'phone', 'mobile'],
///   ),
/// );
/// print('Custom Fields: ${userInfoWithFields.odooFieldsData}');
/// ```
Future<TenantMeResponse> me({
  OdooFieldsCheck? odooFieldsCheck,
}) async {
  // Implementation
}
```

**B. Create New Models**

```dart
/// Response model for /me endpoint
class TenantMeResponse {
  final TenantUser user;
  final TenantInfo tenant;
  final int? partnerId;
  final int? employeeId;
  final List<String> groups;
  final bool isAdmin;
  final bool isInternalUser;
  final List<int> companyIds;
  final int? currentCompanyId;
  final Map<String, dynamic>? odooFieldsData;

  TenantMeResponse({
    required this.user,
    required this.tenant,
    this.partnerId,
    this.employeeId,
    required this.groups,
    required this.isAdmin,
    required this.isInternalUser,
    required this.companyIds,
    this.currentCompanyId,
    this.odooFieldsData,
  });

  factory TenantMeResponse.fromJson(Map<String, dynamic> json) {
    return TenantMeResponse(
      user: TenantUser.fromJson(json['user']),
      tenant: TenantInfo.fromJson(json['tenant']),
      partnerId: json['partner_id'],
      employeeId: json['employee_id'],
      groups: List<String>.from(json['groups'] ?? []),
      isAdmin: json['is_admin'] ?? false,
      isInternalUser: json['is_internal_user'] ?? false,
      companyIds: List<int>.from(json['company_ids'] ?? []),
      currentCompanyId: json['current_company_id'],
      odooFieldsData: json['odoo_fields_data'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'user': user.toJson(),
      'tenant': tenant.toJson(),
      'partner_id': partnerId,
      'employee_id': employeeId,
      'groups': groups,
      'is_admin': isAdmin,
      'is_internal_user': isInternalUser,
      'company_ids': companyIds,
      'current_company_id': currentCompanyId,
      'odoo_fields_data': odooFieldsData,
    };
  }

  /// Check if user has a specific group
  bool hasGroup(String groupXmlId) {
    return groups.contains(groupXmlId);
  }

  /// Check if user has any of the specified groups
  bool hasAnyGroup(List<String> groupXmlIds) {
    return groupXmlIds.any((group) => groups.contains(group));
  }

  /// Check if user has all of the specified groups
  bool hasAllGroups(List<String> groupXmlIds) {
    return groupXmlIds.every((group) => groups.contains(group));
  }

  /// Check if user has access to multiple companies
  bool get isMultiCompany => companyIds.length > 1;

  /// Check if user is an employee in Odoo
  bool get isEmployee => employeeId != null;
}

/// User model for /me response
class TenantUser {
  final String id;
  final String email;
  final String fullName;
  final String role;
  final int? odooUserId;
  final DateTime createdAt;
  final DateTime? lastLogin;

  TenantUser({
    required this.id,
    required this.email,
    required this.fullName,
    required this.role,
    this.odooUserId,
    required this.createdAt,
    this.lastLogin,
  });

  factory TenantUser.fromJson(Map<String, dynamic> json) {
    return TenantUser(
      id: json['id'],
      email: json['email'],
      fullName: json['full_name'],
      role: json['role'],
      odooUserId: json['odoo_user_id'],
      createdAt: DateTime.parse(json['created_at']),
      lastLogin: json['last_login'] != null 
          ? DateTime.parse(json['last_login']) 
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'full_name': fullName,
      'role': role,
      'odoo_user_id': odooUserId,
      'created_at': createdAt.toIso8601String(),
      'last_login': lastLogin?.toIso8601String(),
    };
  }
}

/// Tenant info model for /me response
class TenantInfo {
  final String id;
  final String name;
  final String slug;
  final String status;
  final String odooUrl;
  final String odooDatabase;
  final String? odooVersion;

  TenantInfo({
    required this.id,
    required this.name,
    required this.slug,
    required this.status,
    required this.odooUrl,
    required this.odooDatabase,
    this.odooVersion,
  });

  factory TenantInfo.fromJson(Map<String, dynamic> json) {
    return TenantInfo(
      id: json['id'],
      name: json['name'],
      slug: json['slug'],
      status: json['status'],
      odooUrl: json['odoo_url'],
      odooDatabase: json['odoo_database'],
      odooVersion: json['odoo_version'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'slug': slug,
      'status': status,
      'odoo_url': odooUrl,
      'odoo_database': odooDatabase,
      'odoo_version': odooVersion,
    };
  }
}
```

**C. Update Endpoints Constants**

```dart
class BridgeCoreEndpoints {
  // ... existing endpoints ...
  
  /// Get current user information (POST)
  static const String me = '/api/v1/auth/tenant/me';
  
  // ... rest of endpoints ...
}
```

**D. Implementation Example**

```dart
// In auth_service.dart

Future<TenantMeResponse> me({
  OdooFieldsCheck? odooFieldsCheck,
}) async {
  try {
    final token = await _tokenManager.getAccessToken();
    if (token == null) {
      throw UnauthorizedException('No access token available');
    }

    final response = await _httpClient.post(
      BridgeCoreEndpoints.me,
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
      body: odooFieldsCheck != null
          ? jsonEncode({
              'odoo_fields_check': odooFieldsCheck.toJson(),
            })
          : null,
    );

    if (response.statusCode == 200) {
      return TenantMeResponse.fromJson(jsonDecode(response.body));
    } else if (response.statusCode == 401) {
      throw UnauthorizedException('Invalid or expired token');
    } else {
      throw BridgeCoreException(
        'Failed to get user info: ${response.statusCode}',
        statusCode: response.statusCode,
      );
    }
  } catch (e) {
    if (e is BridgeCoreException) rethrow;
    throw BridgeCoreException('Failed to get user info: $e');
  }
}
```

---

### 2. **Update Login Response Model**

**Backend Update**: Login response now includes `odoo_database` and `odoo_version`.

#### Required Changes:

```dart
class LoginResponse {
  final String accessToken;
  final String refreshToken;
  final String tokenType;
  final int expiresIn;
  final UserInfo user;
  final TenantInfo tenant;
  final String odooDatabase;      // ← NEW
  final String? odooVersion;      // ← NEW
  final Map<String, dynamic>? odooFieldsData;

  LoginResponse({
    required this.accessToken,
    required this.refreshToken,
    required this.tokenType,
    required this.expiresIn,
    required this.user,
    required this.tenant,
    required this.odooDatabase,  // ← NEW
    this.odooVersion,            // ← NEW
    this.odooFieldsData,
  });

  factory LoginResponse.fromJson(Map<String, dynamic> json) {
    return LoginResponse(
      accessToken: json['access_token'],
      refreshToken: json['refresh_token'],
      tokenType: json['token_type'],
      expiresIn: json['expires_in'],
      user: UserInfo.fromJson(json['user']),
      tenant: TenantInfo.fromJson(json['tenant']),
      odooDatabase: json['odoo_database'],     // ← NEW
      odooVersion: json['odoo_version'],       // ← NEW
      odooFieldsData: json['odoo_fields_data'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'access_token': accessToken,
      'refresh_token': refreshToken,
      'token_type': tokenType,
      'expires_in': expiresIn,
      'user': user.toJson(),
      'tenant': tenant.toJson(),
      'odoo_database': odooDatabase,          // ← NEW
      'odoo_version': odooVersion,            // ← NEW
      'odoo_fields_data': odooFieldsData,
    };
  }
}
```

---

### 3. **Add Permission Helper Methods**

Add convenience methods for checking permissions:

```dart
/// Extension methods for permission checks
extension TenantMePermissions on TenantMeResponse {
  /// Common Odoo groups
  static const String groupUser = 'base.group_user';
  static const String groupSystem = 'base.group_system';
  static const String groupErpManager = 'base.group_erp_manager';
  static const String groupPartnerManager = 'base.group_partner_manager';
  static const String groupMultiCompany = 'base.group_multi_company';
  
  /// Check if user can access a specific module
  bool canAccessModule(String moduleName) {
    return hasGroup('$moduleName.group_user') || 
           hasGroup('$moduleName.group_manager') ||
           isAdmin;
  }
  
  /// Check if user can manage partners
  bool get canManagePartners => 
      hasGroup(groupPartnerManager) || isAdmin;
  
  /// Check if user has multi-company access
  bool get hasMultiCompanyAccess => 
      hasGroup(groupMultiCompany) || isMultiCompany;
}
```

---

### 4. **Add Caching for `/me` Response**

Implement caching to avoid repeated API calls:

```dart
class AuthService {
  TenantMeResponse? _cachedMeResponse;
  DateTime? _meResponseCachedAt;
  static const Duration _meCacheDuration = Duration(minutes: 5);

  /// Get current user info (with caching)
  Future<TenantMeResponse> me({
    OdooFieldsCheck? odooFieldsCheck,
    bool forceRefresh = false,
  }) async {
    // Return cached response if valid and no custom fields requested
    if (!forceRefresh && 
        odooFieldsCheck == null && 
        _cachedMeResponse != null && 
        _meResponseCachedAt != null &&
        DateTime.now().difference(_meResponseCachedAt!) < _meCacheDuration) {
      return _cachedMeResponse!;
    }

    // Fetch from API
    final response = await _fetchMe(odooFieldsCheck);
    
    // Cache only if no custom fields were requested
    if (odooFieldsCheck == null) {
      _cachedMeResponse = response;
      _meResponseCachedAt = DateTime.now();
    }
    
    return response;
  }

  /// Clear cached /me response
  void clearMeCache() {
    _cachedMeResponse = null;
    _meResponseCachedAt = null;
  }

  /// Logout (clear all caches)
  Future<void> logout() async {
    clearMeCache();
    // ... existing logout logic ...
  }
}
```

---

### 5. **Update Example App**

Add examples demonstrating the new `/me` endpoint:

```dart
// example/lib/pages/profile_page.dart

import 'package:flutter/material.dart';
import 'package:bridgecore_flutter/bridgecore_flutter.dart';

class ProfilePage extends StatefulWidget {
  @override
  _ProfilePageState createState() => _ProfilePageState();
}

class _ProfilePageState extends State<ProfilePage> {
  TenantMeResponse? _userInfo;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadUserInfo();
  }

  Future<void> _loadUserInfo() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      // Fetch user info with custom fields
      final userInfo = await BridgeCore.instance.auth.me(
        odooFieldsCheck: OdooFieldsCheck(
          model: 'res.users',
          listFields: ['phone', 'mobile', 'signature'],
        ),
      );

      if (!mounted) return;
      setState(() {
        _userInfo = userInfo;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return Scaffold(
        appBar: AppBar(title: Text('Profile')),
        body: Center(child: CircularProgressIndicator()),
      );
    }

    if (_error != null) {
      return Scaffold(
        appBar: AppBar(title: Text('Profile')),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.error, size: 64, color: Colors.red),
              SizedBox(height: 16),
              Text(_error!),
              SizedBox(height: 16),
              ElevatedButton(
                onPressed: _loadUserInfo,
                child: Text('Retry'),
              ),
            ],
          ),
        ),
      );
    }

    final user = _userInfo!;

    return Scaffold(
      appBar: AppBar(title: Text('Profile')),
      body: ListView(
        padding: EdgeInsets.all(16),
        children: [
          // User Info
          Card(
            child: ListTile(
              leading: CircleAvatar(
                child: Text(user.user.fullName[0].toUpperCase()),
              ),
              title: Text(user.user.fullName),
              subtitle: Text(user.user.email),
              trailing: Chip(
                label: Text(user.user.role.toUpperCase()),
                backgroundColor: user.isAdmin ? Colors.red : Colors.blue,
              ),
            ),
          ),

          SizedBox(height: 16),

          // Tenant Info
          Card(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Tenant Information',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  Divider(),
                  _buildInfoRow('Name', user.tenant.name),
                  _buildInfoRow('Database', user.tenant.odooDatabase),
                  _buildInfoRow('Odoo Version', user.tenant.odooVersion ?? 'N/A'),
                  _buildInfoRow('Status', user.tenant.status),
                ],
              ),
            ),
          ),

          SizedBox(height: 16),

          // Odoo Integration
          Card(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Odoo Integration',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  Divider(),
                  _buildInfoRow('Partner ID', user.partnerId?.toString() ?? 'N/A'),
                  _buildInfoRow('Employee ID', user.employeeId?.toString() ?? 'Not an employee'),
                  _buildInfoRow('Is Admin', user.isAdmin ? 'Yes' : 'No'),
                  _buildInfoRow('Internal User', user.isInternalUser ? 'Yes' : 'No'),
                  _buildInfoRow('Companies', user.companyIds.join(', ')),
                  _buildInfoRow('Current Company', user.currentCompanyId?.toString() ?? 'N/A'),
                ],
              ),
            ),
          ),

          SizedBox(height: 16),

          // Groups
          Card(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Groups (${user.groups.length})',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  Divider(),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: user.groups.map((group) {
                      return Chip(
                        label: Text(
                          group.split('.').last,
                          style: TextStyle(fontSize: 12),
                        ),
                      );
                    }).toList(),
                  ),
                ],
              ),
            ),
          ),

          // Custom Fields
          if (user.odooFieldsData != null) ...[
            SizedBox(height: 16),
            Card(
              child: Padding(
                padding: EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Custom Fields',
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                    Divider(),
                    ...user.odooFieldsData!.entries.map((entry) {
                      return _buildInfoRow(entry.key, entry.value.toString());
                    }).toList(),
                  ],
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              '$label:',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
          ),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }
}
```

---

### 6. **Add Tests**

Add comprehensive tests for the new `/me` endpoint:

```dart
// test/auth_service_test.dart

import 'package:flutter_test/flutter_test.dart';
import 'package:bridgecore_flutter/bridgecore_flutter.dart';

void main() {
  group('AuthService - /me endpoint', () {
    test('me() returns user info without custom fields', () async {
      // Test implementation
    });

    test('me() returns user info with custom fields', () async {
      // Test implementation
    });

    test('me() uses cache when available', () async {
      // Test implementation
    });

    test('me() bypasses cache with forceRefresh', () async {
      // Test implementation
    });

    test('me() throws UnauthorizedException on 401', () async {
      // Test implementation
    });

    test('TenantMeResponse.hasGroup() works correctly', () {
      // Test implementation
    });

    test('TenantMeResponse.hasAnyGroup() works correctly', () {
      // Test implementation
    });

    test('TenantMeResponse.hasAllGroups() works correctly', () {
      // Test implementation
    });
  });
}
```

---

## 📚 Documentation Updates Required

### 1. Update README.md

Add section for the new `/me` endpoint:

```markdown
### Get Current User Info

```dart
// Basic usage
final userInfo = await BridgeCore.instance.auth.me();
print('Partner ID: ${userInfo.partnerId}');
print('Is Admin: ${userInfo.isAdmin}');
print('Groups: ${userInfo.groups}');

// With custom fields
final userInfoWithFields = await BridgeCore.instance.auth.me(
  odooFieldsCheck: OdooFieldsCheck(
    model: 'res.users',
    listFields: ['shuttle_role', 'phone', 'mobile'],
  ),
);
print('Custom Fields: ${userInfoWithFields.odooFieldsData}');

// Force refresh (bypass cache)
final freshInfo = await BridgeCore.instance.auth.me(forceRefresh: true);
```

### 2. Update NEW_FEATURES.md

Add entry for the `/me` endpoint enhancement.

### 3. Create ME_ENDPOINT.md

Create a dedicated documentation file explaining the `/me` endpoint in detail (similar to the backend's `TENANT_ME_ENDPOINT.md`).

---

## 🔄 Migration Guide

For users upgrading from previous versions:

```dart
// Before (no /me endpoint)
// Users had to manually fetch user data after login
final loginResponse = await BridgeCore.instance.auth.login(...);
// No easy way to get groups, partner_id, etc.

// After (with /me endpoint)
final loginResponse = await BridgeCore.instance.auth.login(...);
final userInfo = await BridgeCore.instance.auth.me();
print('Partner ID: ${userInfo.partnerId}');
print('Is Admin: ${userInfo.isAdmin}');
print('Groups: ${userInfo.groups}');
```

---

## ✅ Checklist

- [ ] Add `me()` method to `AuthService`
- [ ] Create `TenantMeResponse` model
- [ ] Create `TenantUser` model
- [ ] Create `TenantInfo` model (or update existing)
- [ ] Update `LoginResponse` model with `odooDatabase` and `odooVersion`
- [ ] Add `/me` endpoint to `BridgeCoreEndpoints`
- [ ] Implement caching for `/me` response
- [ ] Add permission helper methods
- [ ] Update example app with profile page
- [ ] Add comprehensive tests
- [ ] Update README.md
- [ ] Update NEW_FEATURES.md
- [ ] Create ME_ENDPOINT.md documentation
- [ ] Update CHANGELOG.md
- [ ] Bump version number
- [ ] Publish to pub.dev

---

## 📦 Suggested Version Bump

Current version: (check `pubspec.yaml`)

**Suggested**: `1.1.0` (minor version bump for new features)

**Breaking Changes**: None (all changes are additive)

---

## 🎯 Priority

**HIGH PRIORITY** - This is a critical feature that significantly enhances the SDK's capabilities and aligns it with the latest backend API.

---

## 📞 Contact

For questions or clarifications, please open an issue on the repository or contact the BridgeCore team.

---

## 📖 Related Backend Documentation

- [TENANT_ME_ENDPOINT.md](https://github.com/geniustep/BridgeCore/blob/main/TENANT_ME_ENDPOINT.md)
- [AUTHENTICATION_GUIDE.md](https://github.com/geniustep/BridgeCore/blob/main/AUTHENTICATION_GUIDE.md)
- [ODOO_FIELDS_CHECK.md](https://github.com/geniustep/BridgeCore/blob/main/ODOO_FIELDS_CHECK.md)

---

**Last Updated**: 2025-11-22

**Requested By**: BridgeCore Backend Team

**Status**: 🔴 Pending Implementation

