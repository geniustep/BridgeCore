# Admin Dashboard Setup - Complete Guide

## 🎯 Overview

The BridgeCore Admin Dashboard is now fully integrated and accessible through multiple endpoints:

- **Production (HTTPS)**: `https://bridgecore.geniura.com/admin/`
- **Local Development**: `http://localhost:8001/admin/`

## 🔐 Login Credentials

### Admin User
```
Email: admin@bridgecore.com
Password: admin123
```

### Tenant User (for testing)
```
Email: user@done.com
Password: done123
Tenant ID: 23c1a19e-410a-4a57-a1b4-98580921d27e
```

## 🏗️ Architecture

### Production Setup (Traefik)

```
Browser → Traefik → Admin Dashboard (Nginx) → API (FastAPI)
          (HTTPS)    (Port 3000)              (Port 8000)
```

**Traefik Configuration:**
- Host: `bridgecore.geniura.com`
- Path: `/admin`
- SSL/TLS: Enabled with Let's Encrypt
- No `stripPrefix` middleware (keeps `/admin` prefix)

**Admin Dashboard (Nginx):**
- Serves static files from `/usr/share/nginx/html`
- Routes `/admin/assets/*` to `/assets/*` using `alias`
- Proxies `/admin/(auth|tenants|plans|analytics|logs)` to API
- SPA routing for all other `/admin/*` routes

**API (FastAPI):**
- Admin endpoints: `/admin/auth/*`, `/admin/tenants/*`, etc.
- CORS enabled for:
  - `https://bridgecore.geniura.com`
  - `http://localhost:8001`
  - `http://localhost:3000`

### Local Development Setup

```
Browser → Admin Dashboard (Vite Dev Server) → API (FastAPI)
          (Port 8001)                          (Port 8000)
```

## 📁 Key Files

### 1. Traefik Configuration
**File:** `/opt/routy-traefik/traefik-dynamic.yml`

```yaml
routers:
  bridgecore-admin:
    rule: "Host(`bridgecore.geniura.com`) && PathPrefix(`/admin`)"
    entryPoints:
      - websecure
    service: bridgecore-admin
    tls:
      certResolver: lehttp

services:
  bridgecore-admin:
    loadBalancer:
      servers:
        - url: "http://bridgecore_admin:3000"
```

### 2. Admin Dashboard Nginx
**File:** `/opt/BridgeCore/admin/nginx.conf`

```nginx
# Admin API proxy
location ~ ^/admin/(auth|tenants|plans|analytics|logs) {
    proxy_pass http://api:8000;
    # ... proxy headers
}

# Admin static assets
location ^~ /admin/assets/ {
    alias /usr/share/nginx/html/assets/;
    try_files $uri =404;
}

# Admin SPA routes
location /admin/ {
    try_files $uri $uri/ /index.html;
}
```

### 3. Vite Configuration
**File:** `/opt/BridgeCore/admin/vite.config.ts`

```typescript
export default defineConfig({
  plugins: [react()],
  base: '/admin/',  // Important: Sets base path for assets
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

### 4. Docker Compose
**File:** `/opt/BridgeCore/docker/docker-compose.yml`

```yaml
admin:
  build:
    context: ..
    dockerfile: admin/Dockerfile
  container_name: bridgecore_admin
  environment:
    - VITE_API_URL=/api
    - VITE_APP_NAME=BridgeCore Admin
  networks:
    - middleware_network
    - routy-traefik_web
  labels:
    - "traefik.enable=true"
    - "traefik.docker.network=routy-traefik_web"
    - "traefik.http.routers.bridgecore-admin.rule=Host(`bridgecore.geniura.com`) && PathPrefix(`/admin`)"
    - "traefik.http.services.bridgecore-admin.loadbalancer.server.port=3000"
```

### 5. CORS Configuration
**File:** `/opt/BridgeCore/app/core/config.py`

```python
CORS_ORIGINS: List[str] = Field(
    default=[
        "https://bridgecore.geniura.com",
        "http://bridgecore.geniura.com",
        "http://localhost:3000",
        "http://localhost:8001",
        "http://localhost:8080"
    ],
    env="CORS_ORIGINS"
)
```

## 🚀 Deployment

### Production (with Traefik)

```bash
cd /opt/BridgeCore/docker
docker-compose build admin api
docker-compose up -d admin api
```

### Local Development

```bash
cd /opt/BridgeCore/admin
npm install
npm run dev  # Starts on http://localhost:8001
```

## 🧪 Testing

### 1. Test Admin Login (Production)
```bash
curl -X POST "https://bridgecore.geniura.com/admin/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@bridgecore.com","password":"admin123"}'
```

### 2. Test Admin Login (Local)
```bash
curl -X POST "http://localhost:8001/admin/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@bridgecore.com","password":"admin123"}'
```

### 3. Test Tenant Details
```bash
TOKEN="<your_token_here>"
curl -X GET "https://bridgecore.geniura.com/admin/tenants/23c1a19e-410a-4a57-a1b4-98580921d27e" \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Test Static Assets
```bash
curl -I "https://bridgecore.geniura.com/admin/assets/index-BdOndhxL.css"
# Should return: HTTP/2 200
```

## 🐛 Troubleshooting

### Issue: 404 for static assets
**Solution:** Check that `base: '/admin/'` is set in `vite.config.ts` and rebuild:
```bash
cd /opt/BridgeCore/docker
docker-compose build admin
docker-compose up -d admin
```

### Issue: CORS errors
**Solution:** Add the origin to `CORS_ORIGINS` in `/opt/BridgeCore/app/core/config.py` and restart API:
```bash
cd /opt/BridgeCore/docker
docker-compose restart api
```

### Issue: 405 Method Not Allowed
**Solution:** Check that the admin API routes are correctly proxied in `nginx.conf`:
```nginx
location ~ ^/admin/(auth|tenants|plans|analytics|logs) {
    proxy_pass http://api:8000;
}
```

### Issue: Traefik not routing
**Solution:** Check Traefik logs and ensure the admin service is in the correct network:
```bash
docker logs routy-traefik-traefik-1 --tail 50
docker network inspect routy-traefik_web
```

## 📊 Database

The admin panel uses the `bridgecore` database with the following tables:
- `admins` - Admin users
- `plans` - Subscription plans
- `tenants` - Tenant organizations
- `tenant_users` - Tenant users
- `admin_audit_logs` - Audit trail
- `usage_logs` - API usage tracking

## 🔄 Updates

To update the admin dashboard:

1. Make changes to the code in `/opt/BridgeCore/admin/`
2. Rebuild the container:
   ```bash
   cd /opt/BridgeCore/docker
   docker-compose build admin
   docker-compose up -d admin
   ```

To update the API:

1. Make changes to the code in `/opt/BridgeCore/app/`
2. Rebuild and restart:
   ```bash
   cd /opt/BridgeCore/docker
   docker-compose build api
   docker-compose up -d api
   ```

## ✅ Success Checklist

- [x] Admin Dashboard accessible on `https://bridgecore.geniura.com/admin/`
- [x] Static assets (CSS, JS) load correctly
- [x] Admin login works
- [x] Tenant details API works
- [x] CORS configured for local development
- [x] Traefik routing configured
- [x] SSL/TLS enabled
- [x] Database migrations applied
- [x] Test data created

## 📝 Notes

- The admin dashboard is a React SPA built with Vite
- It uses Tailwind CSS for styling
- The API is built with FastAPI and uses PostgreSQL
- Traefik handles SSL/TLS termination and routing
- Nginx serves the static files and proxies API requests

## 🎉 Success!

The BridgeCore Admin Dashboard is now fully operational and accessible at:
- **Production**: https://bridgecore.geniura.com/admin/
- **Local Dev**: http://localhost:8001/admin/

Login with `admin@bridgecore.com` / `admin123` to start managing tenants!

