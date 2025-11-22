# 🚀 BridgeCore Admin Dashboard - Quick Start

## 📍 Access URLs

### Production (Recommended)
```
https://bridgecore.geniura.com/admin/
```

### Local Development
```
http://localhost:8001/admin/
```

## 🔐 Login Credentials

### Admin Dashboard
```
Email:    admin@bridgecore.com
Password: admin123
```

### Tenant API (for testing)
```
Email:    user@done.com
Password: done123
```

## 🎯 Quick Actions

### 1. View All Tenants
Navigate to: `https://bridgecore.geniura.com/admin/tenants`

### 2. Edit Tenant
Navigate to: `https://bridgecore.geniura.com/admin/tenants/23c1a19e-410a-4a57-a1b4-98580921d27e/edit`

### 3. View Plans
Navigate to: `https://bridgecore.geniura.com/admin/plans`

### 4. View Analytics
Navigate to: `https://bridgecore.geniura.com/admin/analytics`

## 🔧 Common Commands

### Restart Services
```bash
cd /opt/BridgeCore/docker
docker-compose restart api admin
```

### View Logs
```bash
# API logs
docker logs bridgecore_api --tail 50 -f

# Admin Dashboard logs
docker logs bridgecore_admin --tail 50 -f
```

### Rebuild After Changes
```bash
cd /opt/BridgeCore/docker
docker-compose build admin api
docker-compose up -d
```

## 📊 Test Data

### Tenant Information
- **Name:** Done Company
- **Slug:** done-company
- **ID:** 23c1a19e-410a-4a57-a1b4-98580921d27e
- **Odoo URL:** https://odoo.geniura.com
- **Odoo Database:** done
- **Status:** Active

### Plan Information
- **Name:** Free Plan
- **Max Requests/Day:** 1000
- **Max Users:** 5
- **Price:** $0/month

## 🧪 API Testing

### Login as Admin
```bash
curl -X POST "https://bridgecore.geniura.com/admin/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@bridgecore.com","password":"admin123"}'
```

### Get Tenant Details
```bash
TOKEN="<your_token>"
curl -X GET "https://bridgecore.geniura.com/admin/tenants/23c1a19e-410a-4a57-a1b4-98580921d27e" \
  -H "Authorization: Bearer $TOKEN"
```

### Login as Tenant User
```bash
curl -X POST "https://bridgecore.geniura.com/api/v1/auth/tenant/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@done.com","password":"done123"}'
```

## 📁 Important Files

| File | Purpose |
|------|---------|
| `/opt/BridgeCore/docker/docker-compose.yml` | Main Docker Compose configuration |
| `/opt/BridgeCore/admin/nginx.conf` | Nginx configuration for Admin Dashboard |
| `/opt/BridgeCore/admin/vite.config.ts` | Vite build configuration |
| `/opt/routy-traefik/traefik-dynamic.yml` | Traefik routing configuration |
| `/opt/BridgeCore/app/core/config.py` | API configuration (CORS, etc.) |

## 🐛 Troubleshooting

### Problem: Can't access admin dashboard
**Solution:** Check if containers are running:
```bash
docker ps | grep bridgecore
```

### Problem: CORS errors in browser
**Solution:** Restart API after CORS changes:
```bash
cd /opt/BridgeCore/docker
docker-compose restart api
```

### Problem: 404 for assets
**Solution:** Rebuild admin container:
```bash
cd /opt/BridgeCore/docker
docker-compose build admin
docker-compose up -d admin
```

## 📚 Full Documentation

For detailed setup and troubleshooting, see:
- `ADMIN_DASHBOARD_SETUP.md` - Complete setup guide
- `LOGIN_CREDENTIALS.md` - All login credentials
- `NEXT_STEPS_GUIDE.md` - Next development steps

## ✅ Verification

To verify everything is working:

1. ✅ Open `https://bridgecore.geniura.com/admin/` in browser
2. ✅ Login with `admin@bridgecore.com` / `admin123`
3. ✅ Navigate to Tenants page
4. ✅ Click on "Done Company" tenant
5. ✅ Verify tenant details load correctly

## 🎉 Success!

You're all set! The Admin Dashboard is fully operational.

For support or questions, check the full documentation in `ADMIN_DASHBOARD_SETUP.md`.

