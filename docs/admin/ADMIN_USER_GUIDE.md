# BridgeCore Admin User Guide

## Introduction

Welcome to the BridgeCore Admin Panel! This guide will help you understand how to use the admin dashboard to manage tenants, monitor system health, and analyze usage patterns.

---

## Getting Started

### Accessing the Admin Panel

1. Open your browser and navigate to: `http://localhost:3000` (or your configured admin URL)
2. You will see the login page

### First Login

Use the default credentials (change these immediately after first login):
- **Email**: `admin@bridgecore.local`
- **Password**: `admin123`

### Changing Your Password

1. Click on your profile icon in the top-right corner
2. Select "Profile Settings"
3. Enter your current password and new password
4. Click "Save Changes"

---

## Dashboard Overview

The dashboard provides a quick overview of your BridgeCore platform.

### Statistics Cards

| Card | Description |
|------|-------------|
| **Total Tenants** | Number of registered tenants |
| **Active Tenants** | Tenants with active status |
| **API Requests (24h)** | Total API requests in last 24 hours |
| **Error Rate** | Percentage of failed requests |

### Quick Actions

- **Add Tenant**: Create a new tenant
- **View Analytics**: Go to analytics dashboard
- **View Logs**: Check recent API logs

---

## Tenant Management

### Viewing Tenants

1. Click **Tenants** in the sidebar
2. You'll see a list of all tenants with:
   - Name and slug
   - Contact email
   - Status (Active, Trial, Suspended, Deleted)
   - Odoo URL
   - Actions

### Filtering Tenants

Use the filter dropdown to show only:
- **Active**: Currently active tenants
- **Trial**: Tenants in trial period
- **Suspended**: Temporarily disabled tenants
- **Deleted**: Soft-deleted tenants

### Creating a New Tenant

1. Click **Add Tenant** button
2. Fill in the required information:

#### Basic Information
| Field | Description | Required |
|-------|-------------|----------|
| Tenant Name | Display name for the tenant | Yes |
| Slug | URL-friendly identifier (auto-generated) | Yes |
| Description | Brief description | No |

#### Contact Information
| Field | Description | Required |
|-------|-------------|----------|
| Contact Email | Primary contact email | Yes |
| Contact Phone | Phone number | No |

#### Odoo Connection
| Field | Description | Required |
|-------|-------------|----------|
| Odoo URL | Full URL to Odoo instance | Yes |
| Database Name | Odoo database name | Yes |
| Odoo Version | Select from dropdown | No |
| Username | Odoo API username | Yes |
| Password | Odoo API password | Yes |

#### Subscription
| Field | Description | Required |
|-------|-------------|----------|
| Plan | Select subscription plan | Yes |
| Max Requests/Day | Override plan limit | No |
| Max Requests/Hour | Override plan limit | No |

#### Advanced Settings
| Field | Description |
|-------|-------------|
| Allowed Models | Restrict which Odoo models can be accessed |
| Allowed Features | Enable/disable specific features |
| Trial End Date | When trial period expires |
| Subscription End Date | When subscription expires |

3. Click **Create Tenant**

### Editing a Tenant

1. Click on the tenant name or **Edit** button
2. Modify the desired fields
3. Click **Save Changes**

**Note**: The slug cannot be changed after creation.

### Testing Odoo Connection

1. Go to the tenant's edit page or list view
2. Click **Test Connection**
3. The system will verify:
   - Odoo URL is reachable
   - Credentials are valid
   - Database exists
4. You'll see a success or error message

### Suspending a Tenant

Suspending blocks all API access without deleting data.

1. Click the **Suspend** button next to the tenant
2. Confirm the action
3. Tenant status changes to "Suspended"

**Effects of suspension:**
- All API requests return 403 Forbidden
- Tenant users cannot login
- Data is preserved

### Activating a Tenant

1. Click the **Activate** button next to a suspended tenant
2. Confirm the action
3. Tenant status changes to "Active"

### Deleting a Tenant

**Warning**: This is a soft delete. Data is preserved but tenant becomes inaccessible.

1. Click the **Delete** button
2. Type the tenant name to confirm
3. Click **Confirm Delete**

---

## Analytics Dashboard

### Accessing Analytics

Click **Analytics** in the sidebar to view system-wide analytics.

### Time Period Selection

Use the dropdown to select time period:
- Last 24 hours
- Last 7 days
- Last 30 days
- Last 90 days

### Available Charts

#### Requests Over Time
- **Type**: Line chart
- **Shows**: Total requests and errors over time
- **Use**: Identify traffic patterns and error spikes

#### Status Code Distribution
- **Type**: Pie chart
- **Shows**: Breakdown of HTTP status codes
- **Colors**:
  - Green: 2xx (Success)
  - Yellow: 4xx (Client Error)
  - Red: 5xx (Server Error)

#### Response Time by Hour
- **Type**: Bar chart
- **Shows**: Average response time per hour
- **Use**: Identify slow periods

### Tables

#### Top Tenants
Shows the most active tenants with:
- Tenant name
- Total requests
- Average response time
- Success rate
- Error count

#### Top Endpoints
Shows the most used API endpoints with:
- Endpoint path
- Request count
- Average response time
- Error rate

---

## Usage Logs

### Viewing Usage Logs

1. Click **Logs** > **Usage Logs** in the sidebar
2. You'll see a table of all API requests

### Log Information

Each log entry shows:
| Column | Description |
|--------|-------------|
| Timestamp | When the request occurred |
| Tenant | Which tenant made the request |
| Method | HTTP method (GET, POST, etc.) |
| Endpoint | API endpoint called |
| Status | HTTP status code |
| Response Time | How long the request took |
| IP Address | Client IP address |

### Filtering Logs

Use the filter bar to narrow results:

| Filter | Options |
|--------|---------|
| Tenant | Select specific tenant |
| Method | GET, POST, PUT, PATCH, DELETE |
| Status Code | 200, 201, 400, 401, 403, 404, 500 |
| Date Range | Select start and end dates |

Click **Apply** to filter, or **Reset** to clear filters.

### Viewing Log Details

1. Click **View** on any log entry
2. A drawer opens with full details:
   - Request ID
   - Full endpoint path
   - User agent
   - Request/response sizes
   - Odoo model and method (if applicable)
   - Error message (if any)

### Exporting Logs

1. Apply desired filters
2. Click **Export CSV**
3. Download the file

---

## Error Logs

### Viewing Error Logs

1. Click **Logs** > **Error Logs** in the sidebar
2. You'll see a list of application errors

### Error Information

Each error shows:
| Column | Description |
|--------|-------------|
| Timestamp | When the error occurred |
| Severity | Low, Medium, High, Critical |
| Tenant | Affected tenant |
| Error Type | Exception type |
| Message | Error description |
| Status | Open or Resolved |

### Severity Levels

| Level | Color | Description |
|-------|-------|-------------|
| Critical | Red | System-wide impact, immediate attention |
| High | Orange | Significant impact, urgent |
| Medium | Gold | Moderate impact, should be addressed |
| Low | Blue | Minor issues, can be addressed later |

### Filtering Errors

| Filter | Description |
|--------|-------------|
| Tenant | Filter by specific tenant |
| Severity | Filter by severity level |
| Unresolved Only | Show only open errors |

### Viewing Error Details

1. Click **View** on any error
2. See full details including:
   - Complete error message
   - Stack trace
   - Request data that caused the error
   - Related request information

### Resolving Errors

1. Click **Resolve** on an error (or open details and click **Mark Resolved**)
2. Enter resolution notes explaining:
   - What caused the error
   - How it was fixed
   - Any follow-up actions
3. Click **Mark Resolved**

The error will be marked with:
- Resolved timestamp
- Who resolved it
- Resolution notes

---

## Subscription Plans

### Available Plans

| Plan | Daily Limit | Hourly Limit | Users | Storage |
|------|-------------|--------------|-------|---------|
| Free | 1,000 | 100 | 5 | 1 GB |
| Starter | 10,000 | 1,000 | 25 | 10 GB |
| Professional | 100,000 | 10,000 | 100 | 100 GB |
| Enterprise | Unlimited | Unlimited | Unlimited | Unlimited |

### Plan Features

Each plan includes different features:

| Feature | Free | Starter | Professional | Enterprise |
|---------|------|---------|--------------|------------|
| Basic CRUD | Yes | Yes | Yes | Yes |
| Webhooks | No | Yes | Yes | Yes |
| Smart Sync | No | Yes | Yes | Yes |
| Analytics | No | No | Yes | Yes |
| Priority Support | No | No | No | Yes |

### Changing Tenant Plan

1. Edit the tenant
2. Select new plan from dropdown
3. Rate limits will auto-update (unless overridden)
4. Save changes

---

## Best Practices

### Security

1. **Change default credentials** immediately after installation
2. **Use strong passwords** for admin accounts
3. **Regularly review** tenant access and permissions
4. **Monitor error logs** for suspicious activity

### Performance

1. **Set appropriate rate limits** based on tenant needs
2. **Monitor response times** in analytics
3. **Review top endpoints** for optimization opportunities
4. **Archive old logs** regularly

### Tenant Management

1. **Verify Odoo connections** after creating tenants
2. **Start with trial status** for new tenants
3. **Document tenant configurations** externally
4. **Review suspended tenants** periodically

### Error Handling

1. **Prioritize critical errors** for immediate attention
2. **Document resolutions** for future reference
3. **Look for patterns** in recurring errors
4. **Notify tenants** of issues affecting their service

---

## Troubleshooting

### Cannot Login

1. Verify email and password are correct
2. Check if your admin account is active
3. Clear browser cache and cookies
4. Try incognito/private mode

### Tenant Connection Test Fails

1. Verify Odoo URL is correct (no trailing slash)
2. Check Odoo credentials
3. Ensure Odoo instance is running
4. Check firewall/network access
5. Verify database name is correct

### Missing Data in Analytics

1. Check date range selection
2. Verify tenants have activity in the period
3. Wait for background jobs to aggregate data
4. Check Celery worker logs

### Slow Dashboard Loading

1. Reduce date range for analytics
2. Check database performance
3. Verify Redis is running
4. Check network latency

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + /` | Toggle sidebar |
| `Ctrl + K` | Quick search |
| `Esc` | Close modals/drawers |

---

## Getting Help

### Documentation
- API Documentation: `/docs/API_DOCUMENTATION.md`
- Deployment Guide: `/docs/DEPLOYMENT_GUIDE.md`
- Environment Variables: `/docs/ENVIRONMENT_VARIABLES.md`

### Support
- GitHub Issues: [Report bugs](https://github.com/geniustep/BridgeCore/issues)
- Email: support@bridgecore.com

### Logs Location
- API Logs: `docker logs bridgecore-api`
- Admin Logs: Browser console (F12)
