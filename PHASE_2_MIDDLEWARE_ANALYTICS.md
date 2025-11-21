# BridgeCore Phase 2: Middleware & Analytics - Complete

## 📊 **Implementation Status: Phase 2 Complete (20%)**

---

## ✅ **What Has Been Completed in Phase 2**

### 1. **Middleware (3 New Middleware Components)** ✅

#### **1.1 Usage Tracking Middleware** (`app/middleware/usage_tracking.py`)
Automatically tracks all tenant API requests for analytics.

**Features:**
- Tracks every tenant API request
- Records endpoint, method, response time
- Captures request/response sizes
- Logs status codes, IP addresses, user agents
- Automatically identifies model names from requests
- Skips tracking for admin routes and health checks
- Asynchronous logging to avoid blocking requests

**What it tracks:**
```python
- tenant_id: UUID
- user_id: UUID (if available)
- endpoint: /api/v1/systems/read
- method: GET, POST, PUT, DELETE
- model_name: res.partner, sale.order, etc.
- request_size_bytes: Size of request payload
- response_size_bytes: Size of response payload
- response_time_ms: Time taken to process request
- status_code: 200, 404, 500, etc.
- ip_address: Client IP
- user_agent: Client browser/app info
- timestamp: When request occurred
```

#### **1.2 Tenant Context Middleware** (`app/middleware/tenant_context.py`)
Validates tenant context and attaches tenant information to requests.

**Features:**
- Extracts tenant_id from JWT token
- Validates tenant exists in database
- Checks tenant status (active, suspended, deleted)
- Blocks suspended/deleted tenants automatically
- Updates tenant's last_active_at timestamp
- Attaches tenant object to request.state for downstream use
- Skips validation for public/admin routes

**Status Handling:**
- **ACTIVE**: Request proceeds normally
- **SUSPENDED**: Returns 403 Forbidden with message
- **DELETED**: Returns 410 Gone
- **TRIAL**: Allowed (with potential future restrictions)

#### **1.3 Rate Limiting Middleware** (`app/middleware/tenant_rate_limit.py`)
Enforces per-tenant rate limits based on subscription plans.

**Features:**
- Hourly rate limiting per tenant
- Daily rate limiting per tenant
- Uses Redis for fast counter storage
- Respects tenant's subscription plan limits
- Can override limits per tenant
- Returns 429 Too Many Requests when exceeded
- Includes Retry-After header
- Adds rate limit info to response headers

**Default Limits:**
- Hourly: 1,000 requests/hour (configurable)
- Daily: 10,000 requests/day (configurable)

**Redis Keys:**
```
rate_limit:tenant:{tenant_id}:hour:{YYYYMMDDHH}
rate_limit:tenant:{tenant_id}:day:{YYYYMMDD}
```

**Response Headers:**
```
X-RateLimit-Hourly-Remaining: 850
X-RateLimit-Daily-Remaining: 8500
Retry-After: 3600  (when limit exceeded)
```

---

### 2. **Services (2 New Services)** ✅

#### **2.1 Logging Service** (`app/services/logging_service.py`)
Manages usage and error logs with comprehensive querying capabilities.

**Usage Log Functions:**
- `get_usage_logs()` - Query logs with filters
- `get_usage_stats_summary()` - Get usage summary for period
- Count total/successful/failed requests
- Calculate average response times
- Measure data transfer volumes
- Identify most used endpoints

**Error Log Functions:**
- `log_error()` - Create new error log
- `get_error_logs()` - Query errors with filters
- `resolve_error()` - Mark error as resolved
- `get_error_summary()` - Error statistics
- Filter by severity (low, medium, high, critical)
- Filter unresolved errors only

**Error Severity Levels:**
```python
class ErrorSeverity(str, enum.Enum):
    LOW = "low"          # Minor issues, doesn't affect functionality
    MEDIUM = "medium"    # Notable issues, may need attention
    HIGH = "high"        # Serious issues, affects functionality
    CRITICAL = "critical" # System-breaking issues, immediate action required
```

#### **2.2 Analytics Service** (`app/services/analytics_service.py`)
Generates comprehensive statistics and insights.

**System-Wide Analytics (Admin):**
- `get_system_overview()` - Overall platform metrics
  - Total tenants by status
  - 24-hour request volume
  - Success rates
  - Average response times
  - Data transfer totals

- `get_top_tenants()` - Most active tenants
  - Ranked by request volume
  - Configurable time period
  - Includes performance metrics

**Tenant-Specific Analytics:**
- `get_tenant_analytics()` - Comprehensive tenant metrics
  - Request statistics (total, success, failure)
  - Performance metrics (avg/min/max response time)
  - Data transfer volumes (bytes, MB, GB)
  - Top 5 endpoints used
  - Top 5 Odoo models accessed
  - Unique user count

- `get_tenant_daily_stats()` - Time-series data
  - Daily breakdown of requests
  - Daily performance trends
  - Can use aggregated or raw data

---

### 3. **API Routes (2 New Route Modules)** ✅

#### **3.1 Analytics Routes** (`/admin/analytics/*`)

**Endpoints:**

1. **GET /admin/analytics/overview**
   - System-wide overview
   - Tenant counts, usage stats, success rates
   - No parameters required

2. **GET /admin/analytics/top-tenants**
   - Top tenants by activity
   - Query params: `limit` (1-50), `days` (1-90)

3. **GET /admin/analytics/tenants/{tenant_id}**
   - Comprehensive tenant analytics
   - Query params: `days` (1-365)
   - Returns: summary, performance, data_transfer, top endpoints/models

4. **GET /admin/analytics/tenants/{tenant_id}/daily**
   - Daily time-series statistics
   - Query params: `days` (1-90)
   - Perfect for charts and graphs

**Example Response (GET /admin/analytics/tenants/{id}):**
```json
{
  "summary": {
    "total_requests": 15420,
    "successful_requests": 14890,
    "failed_requests": 530,
    "success_rate_percent": 96.56,
    "unique_users": 45
  },
  "performance": {
    "avg_response_time_ms": 235.67,
    "max_response_time_ms": 3450,
    "min_response_time_ms": 12
  },
  "data_transfer": {
    "total_bytes": 45678912,
    "total_mb": 43.56,
    "total_gb": 0.043
  },
  "top_endpoints": [
    {"endpoint": "/api/v1/systems/read", "count": 8950},
    {"endpoint": "/api/v1/systems/create", "count": 2340}
  ],
  "top_models": [
    {"model": "res.partner", "count": 5670},
    {"model": "sale.order", "count": 3210}
  ],
  "period_days": 30
}
```

#### **3.2 Logs Routes** (`/admin/logs/*`)

**Endpoints:**

1. **GET /admin/logs/usage**
   - Query usage logs
   - Filters: tenant_id, skip, limit, start_date, end_date, method, status_code
   - Pagination support (1-500 records)

2. **GET /admin/logs/usage/summary**
   - Usage statistics summary
   - Query params: `tenant_id` (required), `days`

3. **GET /admin/logs/errors**
   - Query error logs
   - Filters: tenant_id, skip, limit, severity, unresolved_only
   - Severity: low, medium, high, critical

4. **GET /admin/logs/errors/summary**
   - Error statistics summary
   - Query params: `tenant_id` (required), `days`

5. **POST /admin/logs/errors/{error_id}/resolve**
   - Mark error as resolved
   - Body: `resolution_notes` (optional)

**Example Response (GET /admin/logs/usage):**
```json
[
  {
    "id": 12345,
    "tenant_id": "uuid...",
    "user_id": "uuid...",
    "timestamp": "2025-11-21T10:30:45Z",
    "endpoint": "/api/v1/systems/read",
    "method": "POST",
    "model_name": "res.partner",
    "request_size_bytes": 512,
    "response_size_bytes": 8192,
    "response_time_ms": 235,
    "status_code": 200,
    "ip_address": "192.168.1.100"
  }
]
```

---

### 4. **Background Tasks (Celery)** ✅

#### **4.1 Stats Aggregation Tasks** (`app/tasks/stats_aggregation.py`)

**Three Scheduled Tasks:**

1. **aggregate_hourly_stats**
   - Runs: Every hour at :05 (e.g., 01:05, 02:05, 03:05)
   - Purpose: Aggregate raw usage logs into hourly statistics
   - Creates/updates UsageStats records (hour field set)
   - Processes all active tenants

2. **aggregate_daily_stats**
   - Runs: Daily at 00:30 UTC
   - Purpose: Aggregate hourly stats into daily summaries
   - Creates/updates UsageStats records (hour field NULL)
   - Calculates peak hours and trends

3. **cleanup_old_logs**
   - Runs: Daily at 02:00 UTC
   - Purpose: Delete usage logs older than 90 days
   - Keeps database size manageable
   - Retains aggregated stats permanently

**What Gets Aggregated:**
```python
UsageStats:
  - date: Date of statistics
  - hour: Hour (0-23) or NULL for daily
  - total_requests: Count of all requests
  - successful_requests: 2xx status codes
  - failed_requests: 4xx/5xx status codes
  - total_data_transferred_bytes: Sum of request + response sizes
  - avg_response_time_ms: Average response time
  - unique_users: Count of unique user_ids
  - most_used_model: Most frequently accessed Odoo model
  - peak_hour: Hour with most traffic (daily stats only)
```

#### **4.2 Celery Configuration** (`app/core/celery_app.py`)

**Beat Schedule:**
```python
beat_schedule = {
    "aggregate-hourly-stats": {
        "task": "aggregate_hourly_stats",
        "schedule": crontab(minute=5)  # Every hour
    },
    "aggregate-daily-stats": {
        "task": "aggregate_daily_stats",
        "schedule": crontab(hour=0, minute=30)  # Daily at 00:30
    },
    "cleanup-old-logs": {
        "task": "cleanup_old_logs",
        "schedule": crontab(hour=2, minute=0)  # Daily at 02:00
    }
}
```

**To Run Celery Worker:**
```bash
# Start worker
celery -A app.core.celery_app worker --loglevel=info

# Start beat scheduler
celery -A app.core.celery_app beat --loglevel=info
```

---

### 5. **Main Application Integration** ✅

Updated `app/main.py` to include:

**Middleware Registration:**
```python
from app.middleware.usage_tracking import UsageTrackingMiddleware
from app.middleware.tenant_context import TenantContextMiddleware
from app.middleware.tenant_rate_limit import TenantRateLimitMiddleware

app.add_middleware(UsageTrackingMiddleware)
app.add_middleware(TenantContextMiddleware)
app.add_middleware(TenantRateLimitMiddleware)
```

**Route Registration:**
```python
from app.api.routes.admin import analytics as admin_analytics
from app.api.routes.admin import logs as admin_logs

app.include_router(admin_analytics.router)  # /admin/analytics/*
app.include_router(admin_logs.router)      # /admin/logs/*
```

---

## 🔄 **How It All Works Together**

### **Request Flow:**

```
1. Client Request
   ↓
2. CORS Middleware
   ↓
3. GZip Middleware
   ↓
4. Prometheus Middleware
   ↓
5. [NEW] Usage Tracking Middleware ← Logs request details
   ↓
6. [NEW] Tenant Context Middleware ← Validates tenant
   ↓
7. [NEW] Rate Limit Middleware ← Checks limits
   ↓
8. Logging Middleware
   ↓
9. Route Handler (Process Request)
   ↓
10. Response
    ↓
11. Usage Tracking Middleware ← Logs response details
    ↓
12. Client
```

### **Data Flow:**

```
1. Raw Usage Logs (UsageLog table)
   - Every API request creates a log entry
   - Tracked by Usage Tracking Middleware
   ↓
2. Hourly Aggregation (runs every hour)
   - Celery task: aggregate_hourly_stats
   - Creates UsageStats (with hour field)
   ↓
3. Daily Aggregation (runs daily at 00:30)
   - Celery task: aggregate_daily_stats
   - Creates UsageStats (hour = NULL)
   ↓
4. Analytics Service
   - Queries aggregated stats for fast performance
   - Falls back to raw logs if needed
   ↓
5. Admin Dashboard
   - Displays charts, graphs, metrics
```

---

## 🚀 **How to Use Phase 2 Features**

### **1. Start Required Services**

```bash
# Redis (for rate limiting)
redis-server

# Celery Worker (for background tasks)
celery -A app.core.celery_app worker --loglevel=info

# Celery Beat (for scheduled tasks)
celery -A app.core.celery_app beat --loglevel=info

# FastAPI Server
uvicorn app.main:app --reload
```

### **2. Test Rate Limiting**

```bash
# Make requests to a tenant endpoint
# After exceeding limit, you'll get:
{
  "detail": "Hourly rate limit exceeded (1000 requests/hour)"
}
```

### **3. View Analytics**

```bash
# Get system overview
curl -X GET "http://localhost:8000/admin/analytics/overview" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"

# Get tenant analytics
curl -X GET "http://localhost:8000/admin/analytics/tenants/{tenant_id}?days=30" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"

# Get top tenants
curl -X GET "http://localhost:8000/admin/analytics/top-tenants?limit=10&days=7" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### **4. View Logs**

```bash
# Get usage logs for a tenant
curl -X GET "http://localhost:8000/admin/logs/usage?tenant_id={id}&limit=100" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"

# Get error logs (unresolved only)
curl -X GET "http://localhost:8000/admin/logs/errors?unresolved_only=true" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"

# Mark error as resolved
curl -X POST "http://localhost:8000/admin/logs/errors/123/resolve" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"resolution_notes": "Fixed in v1.2.3"}'
```

---

## 📊 **Database Impact**

### **New Data Being Stored:**

1. **UsageLog table:**
   - ~1-10 million records/month (depends on traffic)
   - Automatically cleaned up after 90 days
   - Indexed for fast queries

2. **UsageStats table:**
   - Hourly stats: ~720 records/month/tenant (24 hours × 30 days)
   - Daily stats: ~30 records/month/tenant
   - Kept permanently (small size)

3. **ErrorLog table:**
   - Depends on error frequency
   - Kept until resolved
   - Indexed by tenant, severity, status

### **Storage Estimates:**

- **UsageLog:** ~200-500 bytes per record
- **1M records** ≈ 200-500 MB
- With cleanup, max ~3-4 GB for 90 days of logs

---

## 🎯 **Performance Considerations**

### **Middleware Performance:**
- **Usage Tracking:** Async logging, doesn't block requests (~1-2ms overhead)
- **Tenant Context:** Single DB query, cached in request state (~10-20ms)
- **Rate Limiting:** Redis lookup, very fast (~1-2ms)
- **Total Overhead:** ~15-25ms per request

### **Analytics Performance:**
- Queries use aggregated stats (fast)
- Raw logs only for detailed analysis
- Indexes on all frequently queried fields

---

## 📝 **Configuration**

### **Environment Variables:**

Already added in `.env.example`:
```env
# Tenant Rate Limiting
DEFAULT_TENANT_RATE_LIMIT_PER_HOUR=1000
DEFAULT_TENANT_RATE_LIMIT_PER_DAY=10000

# Redis (for rate limiting)
REDIS_URL=redis://localhost:6379/0

# Celery (for background tasks)
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

---

## 🎉 **Summary**

**Phase 2 is complete!** You now have:

✅ **3 Middleware Components:**
  - Usage tracking (automatic logging)
  - Tenant context validation
  - Per-tenant rate limiting

✅ **2 New Services:**
  - Logging service (usage & errors)
  - Analytics service (stats & insights)

✅ **8 New API Endpoints:**
  - 4 analytics endpoints
  - 4 logs endpoints (5 with error resolution)

✅ **3 Background Tasks:**
  - Hourly stats aggregation
  - Daily stats aggregation
  - Old log cleanup

✅ **Complete Request Tracking:**
  - Every tenant request logged
  - Real-time analytics
  - Historical trends

---

**Total Phase 2 Files Created:** 9 new files
**Total Phase 2 API Endpoints:** 8 new endpoints
**Total Lines of Code:** ~1,500+ lines

**Next Phase (Phase 3):** React Admin Dashboard UI (30%)

---

## 🔗 **Testing the Features**

Visit the API docs to test all endpoints:
- **Swagger UI:** http://localhost:8000/docs
- **Analytics Section:** Look for "Admin Analytics" tag
- **Logs Section:** Look for "Admin Logs" tag

All endpoints require admin JWT token (from Phase 1).

---

**⚠️ Important Notes:**
1. Redis must be running for rate limiting
2. Celery worker must be running for background tasks
3. Celery beat must be running for scheduled aggregation
4. Database migration from Phase 1 must be applied
