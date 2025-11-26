# Moodle Integration Guide

## Overview

BridgeCore now supports **multi-system architecture**, allowing tenants to connect to multiple external systems including:
- **Odoo ERP** (existing)
- **Moodle LMS** (new)
- **SAP ERP** (coming soon)
- **Salesforce CRM** (coming soon)

This guide explains how to integrate and use Moodle LMS with BridgeCore.

---

## Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Admin Panel Setup](#admin-panel-setup)
- [API Usage](#api-usage)
- [Moodle Endpoints](#moodle-endpoints)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

---

## Architecture

### Multi-System Architecture

```
┌──────────────────────────────────────────────┐
│           BridgeCore Middleware              │
│                                              │
│  ┌────────────────────────────────────┐     │
│  │          Tenant 1                  │     │
│  │  ├─ Odoo ERP (primary)             │     │
│  │  └─ Moodle LMS                     │     │
│  └────────────────────────────────────┘     │
│                                              │
│  ┌────────────────────────────────────┐     │
│  │          Tenant 2                  │     │
│  │  ├─ Moodle LMS (primary)           │     │
│  │  ├─ Odoo ERP                       │     │
│  │  └─ SAP ERP                        │     │
│  └────────────────────────────────────┘     │
└──────────────────────────────────────────────┘
```

### Key Concepts

1. **ExternalSystem**: A catalog of available system types (Odoo, Moodle, SAP, etc.)
2. **TenantSystem**: Many-to-many relationship between tenants and systems
3. **MoodleAdapter**: Implementation of Moodle Web Services API

---

## Prerequisites

### Moodle Requirements

1. **Moodle Version**: 3.5 or higher
2. **Web Services**: Must be enabled
3. **Protocol**: REST protocol enabled
4. **Token**: Web services token generated

### Enabling Web Services in Moodle

**Step 1: Enable Web Services**

```
Site Administration → Advanced Features
→ Enable web services ✓
```

**Step 2: Enable REST Protocol**

```
Site Administration → Plugins → Web Services → Manage Protocols
→ Enable REST protocol ✓
```

**Step 3: Create Web Service User**

```
Site Administration → Users → Add New User
→ Username: bridgecore_api
→ Email: api@yourdomain.com
→ Assign system role: Manager (or custom role with appropriate permissions)
```

**Step 4: Generate Token**

```
Site Administration → Plugins → Web Services → Manage Tokens
→ Add Token
→ User: bridgecore_api
→ Service: moodle_mobile_app (or custom service)
→ Save
→ Copy generated token
```

---

## Admin Panel Setup

### 1. Login to Admin Panel

```bash
https://your-bridgecore.com/admin
```

### 2. Navigate to Tenant Details

1. Go to **Tenants** page
2. Click on the tenant you want to configure
3. Scroll to **Connected Systems** section

### 3. Add Moodle Connection

Click **[+ Add System]** and configure:

```json
{
  "system_type": "moodle",
  "connection_config": {
    "url": "https://lms.yourschool.com",
    "token": "your_moodle_token_here",
    "service": "moodle_mobile_app"
  },
  "is_active": true,
  "is_primary": false
}
```

**Field Descriptions:**
- `url`: Your Moodle instance URL (without trailing slash)
- `token`: Web services token from Moodle
- `service`: Moodle service name (default: `moodle_mobile_app`)
- `is_active`: Enable/disable the connection
- `is_primary`: Set as primary system for this tenant

### 4. Test Connection

After adding, click **[Test Connection]** to verify:

```json
{
  "success": true,
  "message": "Connection successful",
  "system_info": {
    "type": "moodle",
    "sitename": "Your School LMS",
    "version": "4.1.5",
    "url": "https://lms.yourschool.com"
  }
}
```

---

## API Usage

### Authentication

All Moodle endpoints require tenant user authentication:

```bash
# 1. Login as tenant user
POST /api/v1/auth/tenant/login
Content-Type: application/json

{
  "email": "user@school.com",
  "password": "password123"
}

# Response
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}

# 2. Use token in requests
GET /api/v1/moodle/courses
Authorization: Bearer eyJ...
```

---

## Moodle Endpoints

### Course Management

#### Get All Courses

```bash
GET /api/v1/moodle/courses
Authorization: Bearer {token}

# Response
[
  {
    "id": 2,
    "fullname": "Introduction to Programming",
    "shortname": "CS101",
    "categoryid": 1,
    "categoryname": "Computer Science",
    "visible": 1,
    "enrolledusercount": 45
  }
]
```

#### Get Specific Course

```bash
GET /api/v1/moodle/courses/{course_id}
Authorization: Bearer {token}
```

#### Create Course

```bash
POST /api/v1/moodle/courses
Authorization: Bearer {token}
Content-Type: application/json

{
  "fullname": "Web Development Basics",
  "shortname": "WEB101",
  "categoryid": 1,
  "summary": "Learn HTML, CSS, and JavaScript",
  "format": "topics",
  "visible": 1
}

# Response
{
  "success": true,
  "id": 5,
  "message": "Course created successfully"
}
```

#### Update Course

```bash
PUT /api/v1/moodle/courses/{course_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "fullname": "Advanced Web Development",
  "visible": 1
}
```

#### Delete Course

```bash
DELETE /api/v1/moodle/courses/{course_id}
Authorization: Bearer {token}
```

### User Management

#### Get Users

```bash
GET /api/v1/moodle/users?email=student@school.com
Authorization: Bearer {token}

# Response
[
  {
    "id": 15,
    "username": "student1",
    "firstname": "John",
    "lastname": "Doe",
    "email": "student@school.com",
    "city": "New York",
    "country": "US"
  }
]
```

#### Create User

```bash
POST /api/v1/moodle/users
Authorization: Bearer {token}
Content-Type: application/json

{
  "username": "newstudent",
  "password": "SecurePass123!",
  "firstname": "Jane",
  "lastname": "Smith",
  "email": "jane@school.com",
  "city": "Boston",
  "country": "US",
  "lang": "en"
}
```

#### Update User

```bash
PUT /api/v1/moodle/users/{user_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "email": "newemail@school.com",
  "city": "San Francisco"
}
```

### Enrolment Management

#### Get Enrolled Users

```bash
GET /api/v1/moodle/courses/{course_id}/users
Authorization: Bearer {token}

# Response
[
  {
    "id": 15,
    "fullname": "John Doe",
    "email": "john@school.com",
    "roles": [{"roleid": 5, "name": "Student"}]
  }
]
```

#### Enrol User in Course

```bash
POST /api/v1/moodle/courses/{course_id}/enrol
Authorization: Bearer {token}
Content-Type: application/json

{
  "user_id": 15,
  "role_id": 5  // 5 = Student, 3 = Teacher
}
```

### System Information

#### Get Site Info

```bash
GET /api/v1/moodle/site-info
Authorization: Bearer {token}

# Response
{
  "sitename": "Your School LMS",
  "username": "bridgecore_api",
  "userid": 2,
  "siteurl": "https://lms.yourschool.com",
  "release": "4.1.5 (Build: 20230915)",
  "version": "2022112805"
}
```

#### Check Connection Health

```bash
GET /api/v1/moodle/health
Authorization: Bearer {token}

# Response
{
  "status": "connected",
  "latency_ms": 145.32,
  "timestamp": 1701020400
}
```

### Advanced: Call Any Moodle Function

```bash
POST /api/v1/moodle/call
Authorization: Bearer {token}
Content-Type: application/json

{
  "function_name": "core_course_get_categories",
  "params": {
    "criteria": [
      {"key": "name", "value": "Computer Science"}
    ]
  }
}
```

---

## Examples

### Flutter Integration

```dart
import 'package:bridgecore_flutter/bridgecore_flutter.dart';

void main() async {
  // Initialize BridgeCore
  BridgeCore.initialize(
    baseUrl: 'https://api.bridgecore.com',
  );

  // Login
  await BridgeCore.instance.auth.login(
    email: 'user@school.com',
    password: 'password123',
  );

  // Get Moodle courses
  final courses = await BridgeCore.instance.moodle.getCourses();
  print('Found ${courses.length} courses');

  // Create new user
  final newUser = await BridgeCore.instance.moodle.createUser(
    username: 'student123',
    password: 'SecurePass123!',
    firstname: 'Alice',
    lastname: 'Johnson',
    email: 'alice@school.com',
  );

  // Enrol user in course
  await BridgeCore.instance.moodle.enrolUser(
    courseId: 2,
    userId: newUser.id,
    roleId: 5, // Student
  );
}
```

### Python Integration

```python
import requests

BASE_URL = "https://api.bridgecore.com"

# Login
response = requests.post(f"{BASE_URL}/api/v1/auth/tenant/login", json={
    "email": "user@school.com",
    "password": "password123"
})
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Get courses
courses = requests.get(f"{BASE_URL}/api/v1/moodle/courses", headers=headers)
print(f"Courses: {courses.json()}")

# Create course
new_course = requests.post(
    f"{BASE_URL}/api/v1/moodle/courses",
    headers=headers,
    json={
        "fullname": "Python Programming",
        "shortname": "PY101",
        "categoryid": 1,
        "summary": "Learn Python from scratch",
        "visible": 1
    }
)
print(f"Created course ID: {new_course.json()['id']}")
```

---

## Troubleshooting

### Connection Failed

**Error**: `"Moodle is not configured for this tenant"`

**Solution**: Add Moodle connection in Admin Panel:
1. Admin Panel → Tenants → Select Tenant
2. Connected Systems → Add System → Select Moodle
3. Configure URL and token

---

### Invalid Token

**Error**: `"exception": "Invalid token"`

**Solution**:
1. Check token is correctly copied from Moodle
2. Verify web services are enabled in Moodle
3. Regenerate token if needed

---

### Permission Denied

**Error**: `"exception": "Access control exception"`

**Solution**:
1. Check API user has appropriate role in Moodle
2. Verify capabilities for the operation
3. Use Manager or custom role with required permissions

---

### Course Not Found

**Error**: `"Course {id} not found"`

**Solution**:
1. Verify course ID exists in Moodle
2. Check API user has access to the course
3. Ensure course is not deleted

---

## Migration from Legacy Odoo-Only Setup

If you have existing tenants with Odoo configured:

### Automatic Migration

Existing Odoo configuration is preserved:
- Legacy `odoo_url`, `odoo_database`, etc. fields still work
- New tenants should use multi-system architecture
- Existing tenants can gradually migrate

### Manual Migration Steps

1. **Create Odoo System Connection** (optional):
```bash
POST /admin/tenants/{tenant_id}/systems
{
  "system_id": "{odoo_system_id}",
  "connection_config": {
    "url": "tenant.odoo_url",
    "database": "tenant.odoo_database",
    "username": "tenant.odoo_username",
    "password": "tenant.odoo_password"
  },
  "is_primary": true
}
```

2. **Add Moodle**:
```bash
POST /admin/tenants/{tenant_id}/systems
{
  "system_id": "{moodle_system_id}",
  "connection_config": {
    "url": "https://lms.school.com",
    "token": "your_token"
  }
}
```

---

## Database Schema

### New Tables

#### `external_systems`
```sql
id                UUID PRIMARY KEY
system_type       ENUM (odoo, moodle, sap, salesforce, dynamics, custom)
name              VARCHAR(255)
description       TEXT
version           VARCHAR(50)
status            ENUM (active, inactive, error, testing)
is_enabled        BOOLEAN
default_config    JSON
capabilities      JSON
created_at        TIMESTAMP
updated_at        TIMESTAMP
```

#### `tenant_systems`
```sql
id                          UUID PRIMARY KEY
tenant_id                   UUID REFERENCES tenants(id)
system_id                   UUID REFERENCES external_systems(id)
connection_config           JSON (encrypted)
is_active                   BOOLEAN
is_primary                  BOOLEAN
last_connection_test        TIMESTAMP
last_successful_connection  TIMESTAMP
connection_error            TEXT
custom_config               JSON
created_by                  UUID REFERENCES admins(id)
created_at                  TIMESTAMP
updated_at                  TIMESTAMP
```

---

## Security Considerations

1. **Token Storage**: Moodle tokens are encrypted at rest
2. **HTTPS Only**: All Moodle connections must use HTTPS
3. **Token Rotation**: Regularly rotate Moodle tokens
4. **Minimal Permissions**: Use role with only required capabilities
5. **Rate Limiting**: Moodle endpoints have rate limiting

---

## Support

For issues or questions:
- 📧 Email: support@bridgecore.com
- 📖 Documentation: https://docs.bridgecore.com
- 🐛 GitHub Issues: https://github.com/geniustep/BridgeCore/issues

---

## Changelog

### v1.1.0 (2025-11-26)
- ✨ Added multi-system architecture
- ✨ Added Moodle LMS integration
- ✨ Added admin API for system management
- 📝 Added Moodle documentation
- 🔄 Backward compatible with legacy Odoo setup
