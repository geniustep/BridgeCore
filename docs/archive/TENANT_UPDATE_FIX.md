# 🔧 Tenant Update Fix - Datetime Timezone Issue

## ✅ Problem Solved

**Issue:** When updating a tenant through the Admin Dashboard, the API returned a 500 Internal Server Error.

**Error Message:**
```
invalid input for query argument $3: datetime.datetime(2025, 12, 22, 0, 4, 18... 
(can't subtract offset-naive and offset-aware datetimes)
```

## 🐛 Root Cause

The problem occurred because:

1. **Frontend** sends datetime fields (like `trial_ends_at`) with timezone information (UTC)
   ```json
   "trial_ends_at": "2025-12-22T00:04:18.887Z"
   ```

2. **Database** columns are defined as `TIMESTAMP WITHOUT TIME ZONE`
   ```sql
   trial_ends_at TIMESTAMP WITHOUT TIME ZONE
   ```

3. **SQLAlchemy** couldn't convert between timezone-aware and timezone-naive datetimes

## 🛠️ Solution Applied

Modified `/opt/BridgeCore/app/services/tenant_service.py` in the `update_tenant` method to automatically strip timezone information before saving to database:

```python
# Convert timezone-aware datetime to naive for database
datetime_fields = ["trial_ends_at", "subscription_ends_at"]
for field in datetime_fields:
    if field in data and data[field] is not None:
        if isinstance(data[field], datetime) and data[field].tzinfo is not None:
            # Remove timezone info (convert to naive datetime)
            data[field] = data[field].replace(tzinfo=None)
```

## ✅ What Was Fixed

1. ✅ `trial_ends_at` field can now be updated
2. ✅ `subscription_ends_at` field can now be updated
3. ✅ All other tenant fields work correctly
4. ✅ No more 500 errors when updating tenants

## 🧪 Test Results

### Test 1: Update Basic Fields
```bash
curl -X PUT "https://bridgecore.geniura.com/admin/tenants/{tenant_id}" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"name":"Done Company Updated","description":"Test company - Updated"}'
```
**Result:** ✅ Success (200 OK)

### Test 2: Update trial_ends_at
```bash
curl -X PUT "https://bridgecore.geniura.com/admin/tenants/{tenant_id}" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"trial_ends_at":"2025-12-31T23:59:59.000Z"}'
```
**Result:** ✅ Success (200 OK)

### Test 3: Update All Fields (from Admin Dashboard)
```json
{
  "name": "Done Company",
  "slug": "done-company",
  "description": "Test company",
  "status": "active",
  "contact_email": "contact@geniura.com",
  "odoo_url": "https://app.propanel.ma",
  "odoo_database": "shuttlebee",
  "odoo_version": "16.0",
  "odoo_username": "done",
  "odoo_password": ",,07Genius",
  "plan_id": "72ca8838-b92d-4de9-85fa-115652608a63",
  "trial_ends_at": "2025-12-22T00:04:18.887Z"
}
```
**Result:** ✅ Success (200 OK)

## 📋 Technical Details

### Before Fix
```python
# Update fields
for key, value in data.items():
    if hasattr(tenant, key):
        setattr(tenant, key, value)  # ❌ Fails with timezone-aware datetime
```

### After Fix
```python
# Convert timezone-aware datetime to naive for database
datetime_fields = ["trial_ends_at", "subscription_ends_at"]
for field in datetime_fields:
    if field in data and data[field] is not None:
        if isinstance(data[field], datetime) and data[field].tzinfo is not None:
            data[field] = data[field].replace(tzinfo=None)

# Update fields
for key, value in data.items():
    if hasattr(tenant, key):
        setattr(tenant, key, value)  # ✅ Works with naive datetime
```

## 🔍 Why This Happens

1. **Pydantic** (used for request validation) automatically parses ISO 8601 datetime strings with timezone
2. **PostgreSQL** `TIMESTAMP WITHOUT TIME ZONE` doesn't store timezone information
3. **SQLAlchemy** needs consistent datetime types (either all naive or all aware)

## 💡 Best Practices

### Option 1: Use Naive Datetimes (Current Solution)
- ✅ Simple and works with existing database schema
- ✅ No migration needed
- ⚠️ Assumes all times are in UTC

### Option 2: Use Timezone-Aware Datetimes (Future Enhancement)
- Change database columns to `TIMESTAMP WITH TIME ZONE`
- Update all datetime fields in the codebase
- Requires database migration

## 📝 Files Modified

1. **`/opt/BridgeCore/app/services/tenant_service.py`**
   - Added timezone stripping logic in `update_tenant` method
   - Lines 177-182

## 🎯 Impact

- ✅ Tenant updates now work correctly from Admin Dashboard
- ✅ No breaking changes to existing functionality
- ✅ Backward compatible with existing data

## 🚀 Deployment

Changes have been applied and tested:
```bash
cd /opt/BridgeCore/docker
docker-compose restart api
```

## ✅ Verification

To verify the fix is working:

1. Open Admin Dashboard: `https://bridgecore.geniura.com/admin/`
2. Navigate to Tenants
3. Click on any tenant to edit
4. Update any field (including trial_ends_at)
5. Click Save
6. ✅ Should see success message (not 500 error)

## 📚 Related Documentation

- SQLAlchemy Datetime Handling: https://docs.sqlalchemy.org/en/20/core/type_basics.html#sqlalchemy.types.DateTime
- PostgreSQL Timestamp Types: https://www.postgresql.org/docs/current/datatype-datetime.html
- Pydantic Datetime Parsing: https://docs.pydantic.dev/latest/api/types/#pydantic.types.AwareDatetime

---

**Date Fixed:** November 22, 2025  
**Status:** ✅ Resolved  
**Tested:** ✅ All tenant update operations working

