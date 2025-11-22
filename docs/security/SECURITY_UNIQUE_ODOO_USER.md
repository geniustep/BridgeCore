# 🔒 Security Enhancement: Unique Odoo User Constraint

**تاريخ التطبيق:** 22 نوفمبر 2025

## 🎯 الهدف

منع إنشاء حسابات متعددة في BridgeCore لنفس الـ Odoo user ضمن نفس الـ Tenant، لتحسين الأمان والتتبع.

---

## ⚠️ المشكلة الأمنية

### السيناريو الخطير:
```python
# ❌ قبل التحديث: كان ممكناً:
tenant_users = [
    {
        "tenant_id": "uuid-1",
        "email": "john@company.com",
        "odoo_user_id": 5,
        "role": "user"
    },
    {
        "tenant_id": "uuid-1",  # ← نفس الـ tenant
        "email": "john.admin@company.com",
        "odoo_user_id": 5,  # ← نفس الـ Odoo user!
        "role": "admin"  # ← صلاحيات مختلفة!
    }
]
```

### المخاطر:
1. **🔴 Security Bypass**: تجاوز الصلاحيات والحصول على admin access
2. **🔴 Audit Confusion**: فوضى في السجلات - من فعل ماذا؟
3. **🔴 Rate Limiting Bypass**: تجاوز الحدود المفروضة
4. **🔴 Data Inconsistency**: عدم اتساق البيانات

---

## ✅ الحل المطبق

### 1️⃣ Database Constraint

**تم إضافة Unique Constraint:**
```sql
ALTER TABLE tenant_users 
ADD CONSTRAINT uq_tenant_odoo_user 
UNIQUE (tenant_id, odoo_user_id);
```

**النتيجة:**
- ✅ كل `odoo_user_id` يمكن أن يظهر **مرة واحدة فقط** لكل tenant
- ✅ يمكن لنفس الـ `odoo_user_id` أن يكون في **tenants مختلفة** (حالات مشروعة)

---

### 2️⃣ Model Update

**في `app/models/tenant_user.py`:**
```python
from sqlalchemy import UniqueConstraint

class TenantUser(Base, TimestampMixin):
    # ... existing columns ...
    
    __table_args__ = (
        UniqueConstraint(
            'tenant_id', 
            'odoo_user_id',
            name='uq_tenant_odoo_user'
        ),
    )
```

---

### 3️⃣ API Validation

**في `app/api/routes/admin/tenant_users.py`:**
```python
# Check if odoo_user_id already exists for this tenant
if user_data.odoo_user_id:
    result = await db.execute(
        select(TenantUser).where(
            TenantUser.tenant_id == user_data.tenant_id,
            TenantUser.odoo_user_id == user_data.odoo_user_id
        )
    )
    existing_odoo_user = result.scalar_one_or_none()
    if existing_odoo_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Odoo user ID {user_data.odoo_user_id} is already linked..."
        )
```

**Error Response:**
```json
{
  "detail": "Odoo user ID 5 is already linked to another BridgeCore user (john@company.com) in this tenant. Each Odoo user can only have one BridgeCore account per tenant."
}
```

---

### 4️⃣ Service Layer Protection

**في `app/services/tenant_service.py`:**
```python
# Check if this odoo_user_id is already linked
odoo_user_check = await self.session.execute(
    select(TenantUser).where(
        TenantUser.tenant_id == tenant.id,
        TenantUser.odoo_user_id == uid
    )
)
existing_odoo_link = odoo_user_check.scalar_one_or_none()

if existing_odoo_link:
    result["admin_user_created"] = False
    result["admin_user_exists"] = True
    logger.warning(f"Odoo user {uid} already linked to {existing_odoo_link.email}")
```

---

## 📊 الحالات المسموحة vs المرفوضة

### ✅ **مسموح: Tenants مختلفة**

```python
# ✅ مستشار يعمل مع عدة شركات
accounts = [
    {
        "tenant": "Company A",
        "odoo_database": "company_a_db",
        "email": "consultant@company-a.com",
        "odoo_user_id": 15
    },
    {
        "tenant": "Company B",
        "odoo_database": "company_b_db",
        "email": "consultant@company-b.com",
        "odoo_user_id": 8  # ← Different Odoo instance
    }
]
```

**السبب:** كل tenant = كيان عمل منفصل مع Odoo instance مختلف (غالباً)

---

### ❌ **مرفوض: نفس الـ Tenant**

```python
# ❌ محاولة إنشاء حسابين في نفس الـ tenant
accounts = [
    {
        "tenant_id": "uuid-1",
        "email": "user@company.com",
        "odoo_user_id": 5,
        "role": "user"
    },
    {
        "tenant_id": "uuid-1",  # ← Same tenant
        "email": "admin@company.com",
        "odoo_user_id": 5,  # ← Same Odoo user
        "role": "admin"  # ← Trying to escalate privileges
    }
]
```

**النتيجة:** 
```
❌ HTTP 400: Odoo user ID 5 is already linked to another BridgeCore user...
```

---

## 🧪 الاختبار

### Test 1: محاولة إنشاء حساب مكرر

```bash
# 1. Create first user
curl -X POST https://bridgecore.geniura.com/admin/tenant-users \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "uuid-tenant-1",
    "email": "john@company.com",
    "password": "password123",
    "full_name": "John Doe",
    "role": "user",
    "odoo_user_id": 5
  }'

# ✅ Success: User created

# 2. Try to create second user with same odoo_user_id
curl -X POST https://bridgecore.geniura.com/admin/tenant-users \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "uuid-tenant-1",
    "email": "john.admin@company.com",
    "password": "password123",
    "full_name": "John Doe Admin",
    "role": "admin",
    "odoo_user_id": 5
  }'

# ❌ Error 400: Odoo user ID 5 is already linked...
```

---

### Test 2: Test Connection مع Odoo user موجود

```bash
# إذا كان هناك user بـ odoo_user_id = 2 موجود
# ونجرب test connection بنفس الـ Odoo credentials

curl -X POST https://bridgecore.geniura.com/admin/tenants/{tenant_id}/test-connection \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# النتيجة:
{
  "success": true,
  "admin_user_created": false,
  "admin_user_exists": true,
  "message": "Connection successful! Admin user already exists with this Odoo account."
}
```

---

### Test 3: حسابات في tenants مختلفة (مسموح)

```bash
# 1. Create user in Tenant A
curl -X POST https://bridgecore.geniura.com/admin/tenant-users \
  -d '{
    "tenant_id": "uuid-tenant-a",
    "odoo_user_id": 5,
    ...
  }'
# ✅ Success

# 2. Create user in Tenant B with same odoo_user_id
curl -X POST https://bridgecore.geniura.com/admin/tenant-users \
  -d '{
    "tenant_id": "uuid-tenant-b",
    "odoo_user_id": 5,  # ← Same ID, different tenant
    ...
  }'
# ✅ Success - مسموح لأن الـ tenants مختلفة
```

---

## 📝 Migration Details

**File:** `alembic/versions/004_add_unique_constraint_odoo_user.py`

**Revision ID:** `004_unique_odoo_user`

**What it does:**
1. Removes any duplicate entries (keeps oldest)
2. Adds unique constraint
3. Updates alembic version

**Rollback:**
```bash
docker-compose exec fastapi alembic downgrade -1
```

---

## 🔧 Files Changed

| File | Change |
|------|--------|
| `app/models/tenant_user.py` | Added `UniqueConstraint` |
| `app/api/routes/admin/tenant_users.py` | Added validation check |
| `app/services/tenant_service.py` | Added safety check in auto-create |
| `alembic/versions/004_*.py` | New migration |

---

## 📊 Impact Analysis

### ✅ Benefits:

1. **Security**: 
   - ✅ Prevents privilege escalation
   - ✅ Enforces one-to-one mapping
   - ✅ Clear accountability

2. **Data Integrity**:
   - ✅ Consistent user identity
   - ✅ Reliable audit trails
   - ✅ Accurate rate limiting

3. **Compliance**:
   - ✅ Better GDPR compliance
   - ✅ Clear data ownership
   - ✅ Audit-ready logs

### ⚠️ Breaking Changes:

**None** - This is a new constraint that enforces best practices. Existing valid data is preserved.

**Edge Case:** If duplicate entries existed (shouldn't happen), the migration keeps the oldest record.

---

## 🎯 Use Cases

### ✅ Valid Use Case: Multi-Company Consultant

```
Ahmed works with 3 different companies:
├── Tenant A (Company A's Odoo) → ahmed@company-a.com (odoo_user_id: 10)
├── Tenant B (Company B's Odoo) → ahmed@company-b.com (odoo_user_id: 15)
└── Tenant C (Company C's Odoo) → ahmed@company-c.com (odoo_user_id: 20)

✅ Allowed: Different tenants, different Odoo instances
```

### ❌ Invalid Use Case: Privilege Escalation

```
John tries to get admin access:
├── john@company.com (role: user, odoo_user_id: 5)
└── john.admin@company.com (role: admin, odoo_user_id: 5) ← ❌ BLOCKED

❌ Blocked: Same tenant, same Odoo user
```

---

## 🔍 Monitoring

### Check for violations:
```sql
-- This should return 0 rows after the constraint
SELECT tenant_id, odoo_user_id, COUNT(*) 
FROM tenant_users 
WHERE odoo_user_id IS NOT NULL
GROUP BY tenant_id, odoo_user_id 
HAVING COUNT(*) > 1;
```

### Check constraint exists:
```sql
SELECT constraint_name, constraint_type 
FROM information_schema.table_constraints 
WHERE table_name = 'tenant_users' 
AND constraint_name = 'uq_tenant_odoo_user';
```

---

## 📚 Related Documentation

- `TENANT_USER_MANAGEMENT_FIX.md` - Overall user management improvements
- `AUTHENTICATION_GUIDE.md` - Authentication flow
- `TENANT_USERS_API.md` - API documentation

---

**Status:** ✅ **Applied and Active**

**Last Updated:** 22 نوفمبر 2025

