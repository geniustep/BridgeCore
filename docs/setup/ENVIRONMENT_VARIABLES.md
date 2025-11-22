# BridgeCore Environment Variables

## Overview

This document describes all environment variables used by BridgeCore. Copy `env.example` to `.env` and configure according to your environment.

---

## Application Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `APP_NAME` | Application name (shown in logs/UI) | `BridgeCore` | No |
| `ENVIRONMENT` | Environment mode | `development` | Yes |
| `DEBUG` | Enable debug mode | `True` | Yes |
| `HOST` | API host binding | `0.0.0.0` | No |
| `PORT` | API port | `8000` | No |

### Values for ENVIRONMENT

| Value | Description |
|-------|-------------|
| `development` | Local development with hot reload |
| `staging` | Pre-production testing |
| `production` | Production deployment |

**Example:**
```env
APP_NAME=BridgeCore
ENVIRONMENT=production
DEBUG=False
HOST=0.0.0.0
PORT=8000
```

---

## Security Keys

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Application secret key for encryption | Yes |
| `JWT_SECRET_KEY` | Secret for tenant JWT tokens | Yes |
| `ADMIN_SECRET_KEY` | Secret for admin JWT tokens | Yes |

### Generating Secure Keys

```bash
# Using Python
python -c "import secrets; print(secrets.token_urlsafe(64))"

# Using OpenSSL
openssl rand -base64 64
```

**Example:**
```env
SECRET_KEY=your-very-long-random-secret-key-here-change-in-production
JWT_SECRET_KEY=another-very-long-random-secret-key-for-tenant-jwt-tokens
ADMIN_SECRET_KEY=third-very-long-random-secret-key-for-admin-jwt-tokens
```

**Security Notes:**
- Never commit real keys to version control
- Use different keys for each environment
- Rotate keys periodically in production
- Store keys securely (vault, secrets manager)

---

## Database Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | - | Yes |
| `DB_POOL_SIZE` | Connection pool size | `20` | No |
| `DB_MAX_OVERFLOW` | Max overflow connections | `10` | No |
| `DB_POOL_TIMEOUT` | Pool timeout in seconds | `30` | No |
| `DB_ECHO` | Log SQL queries | `False` | No |

### Database URL Format

```
postgresql+asyncpg://username:password@host:port/database
```

**Examples:**
```env
# Local development
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/bridgecore_db

# Docker
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/bridgecore_db

# Remote server
DATABASE_URL=postgresql+asyncpg://bridgecore:secure_password@db.example.com:5432/bridgecore_prod

# With SSL
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db?ssl=require
```

**Pool Configuration:**
```env
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_ECHO=False
```

---

## Redis Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `REDIS_URL` | Redis connection string | - | Yes |
| `REDIS_PASSWORD` | Redis password | - | No |
| `CACHE_TTL` | Default cache TTL in seconds | `300` | No |
| `REDIS_MAX_CONNECTIONS` | Max Redis connections | `10` | No |

### Redis URL Format

```
redis://[:password@]host:port/database
```

**Examples:**
```env
# Local without password
REDIS_URL=redis://localhost:6379/0

# Docker
REDIS_URL=redis://redis:6379/0

# With password
REDIS_URL=redis://:your_password@localhost:6379/0
REDIS_PASSWORD=your_password

# Remote with SSL
REDIS_URL=rediss://:password@redis.example.com:6379/0
```

**Cache Configuration:**
```env
CACHE_TTL=300
REDIS_MAX_CONNECTIONS=10
```

---

## JWT Configuration

### Tenant JWT (for API users)

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `JWT_SECRET_KEY` | Secret key for signing | - | Yes |
| `JWT_ALGORITHM` | Signing algorithm | `HS256` | No |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | `30` | No |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime | `7` | No |

### Admin JWT

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ADMIN_SECRET_KEY` | Secret key for admin tokens | - | Yes |
| `ADMIN_TOKEN_EXPIRE_HOURS` | Admin token lifetime | `24` | No |

**Example:**
```env
# Tenant JWT
JWT_SECRET_KEY=your-tenant-jwt-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Admin JWT
ADMIN_SECRET_KEY=your-admin-jwt-secret-key
ADMIN_TOKEN_EXPIRE_HOURS=24
```

---

## CORS Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `CORS_ORIGINS` | Allowed origins (comma-separated) | `*` | Yes |
| `CORS_ALLOW_CREDENTIALS` | Allow credentials | `True` | No |
| `CORS_ALLOW_METHODS` | Allowed HTTP methods | `*` | No |
| `CORS_ALLOW_HEADERS` | Allowed headers | `*` | No |

**Examples:**
```env
# Development (allow all)
CORS_ORIGINS=*

# Production (specific origins)
CORS_ORIGINS=https://admin.bridgecore.com,https://app.bridgecore.com

# Multiple origins
CORS_ORIGINS=http://localhost:3000,http://localhost:8080,https://admin.example.com
```

---

## Rate Limiting

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `RATE_LIMIT_ENABLED` | Enable rate limiting | `True` | No |
| `DEFAULT_RATE_LIMIT_PER_HOUR` | Default hourly limit | `1000` | No |
| `DEFAULT_RATE_LIMIT_PER_DAY` | Default daily limit | `10000` | No |
| `RATE_LIMIT_STORAGE` | Storage backend | `redis` | No |

**Example:**
```env
RATE_LIMIT_ENABLED=True
DEFAULT_RATE_LIMIT_PER_HOUR=1000
DEFAULT_RATE_LIMIT_PER_DAY=10000
RATE_LIMIT_STORAGE=redis
```

**Note:** Per-tenant rate limits can override these defaults in the admin panel.

---

## Celery Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `CELERY_BROKER_URL` | Message broker URL | - | Yes |
| `CELERY_RESULT_BACKEND` | Result backend URL | - | No |
| `CELERY_TASK_ALWAYS_EAGER` | Run tasks synchronously | `False` | No |
| `CELERY_WORKER_CONCURRENCY` | Worker concurrency | `4` | No |

**Example:**
```env
# Using Redis as broker
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Docker
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# With password
CELERY_BROKER_URL=redis://:password@localhost:6379/1
```

---

## Logging Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `LOG_FORMAT` | Log format | `json` | No |
| `LOG_FILE` | Log file path | - | No |
| `LOG_ROTATION` | Log rotation size | `10 MB` | No |
| `LOG_RETENTION` | Log retention days | `30` | No |

### Log Levels

| Level | Description |
|-------|-------------|
| `DEBUG` | Detailed debugging information |
| `INFO` | General information |
| `WARNING` | Warning messages |
| `ERROR` | Error messages |
| `CRITICAL` | Critical errors |

**Example:**
```env
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/var/log/bridgecore/app.log
LOG_ROTATION=10 MB
LOG_RETENTION=30
```

---

## Monitoring Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `PROMETHEUS_ENABLED` | Enable Prometheus metrics | `True` | No |
| `PROMETHEUS_PORT` | Metrics port | `9090` | No |
| `SENTRY_DSN` | Sentry error tracking DSN | - | No |
| `SENTRY_ENVIRONMENT` | Sentry environment name | - | No |

**Example:**
```env
# Prometheus
PROMETHEUS_ENABLED=True
PROMETHEUS_PORT=9090

# Sentry (optional)
SENTRY_DSN=https://key@sentry.io/project
SENTRY_ENVIRONMENT=production
```

---

## Admin Dashboard Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `VITE_API_URL` | Backend API URL | `http://localhost:8000` | Yes |
| `VITE_APP_NAME` | Application name in UI | `BridgeCore Admin` | No |

**Example:**
```env
# Development
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=BridgeCore Admin

# Production
VITE_API_URL=https://api.bridgecore.com
VITE_APP_NAME=BridgeCore Admin
```

---

## Docker-Specific Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_DB` | PostgreSQL database name | `bridgecore` |
| `POSTGRES_USER` | PostgreSQL username | `postgres` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `postgres` |
| `GRAFANA_PASSWORD` | Grafana admin password | `admin` |

**Example:**
```env
POSTGRES_DB=bridgecore
POSTGRES_USER=bridgecore
POSTGRES_PASSWORD=secure_database_password
GRAFANA_PASSWORD=secure_grafana_password
```

---

## Complete Example (.env)

```env
# =================================
# BridgeCore Environment Variables
# =================================

# Application
APP_NAME=BridgeCore
ENVIRONMENT=production
DEBUG=False
HOST=0.0.0.0
PORT=8000

# Security Keys (CHANGE THESE!)
SECRET_KEY=generate-a-64-character-random-string-here
JWT_SECRET_KEY=generate-another-64-character-random-string
ADMIN_SECRET_KEY=generate-third-64-character-random-string

# Database
DATABASE_URL=postgresql+asyncpg://bridgecore:secure_password@db:5432/bridgecore
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://:redis_password@redis:6379/0
REDIS_PASSWORD=redis_password
CACHE_TTL=300

# JWT Configuration
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ADMIN_TOKEN_EXPIRE_HOURS=24

# CORS
CORS_ORIGINS=https://admin.bridgecore.com,https://app.bridgecore.com

# Rate Limiting
RATE_LIMIT_ENABLED=True
DEFAULT_RATE_LIMIT_PER_HOUR=1000
DEFAULT_RATE_LIMIT_PER_DAY=10000

# Celery
CELERY_BROKER_URL=redis://:redis_password@redis:6379/1
CELERY_RESULT_BACKEND=redis://:redis_password@redis:6379/2

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Monitoring
PROMETHEUS_ENABLED=True
SENTRY_DSN=
SENTRY_ENVIRONMENT=production

# Docker (if using docker-compose)
POSTGRES_DB=bridgecore
POSTGRES_USER=bridgecore
POSTGRES_PASSWORD=secure_password
GRAFANA_PASSWORD=secure_grafana_password

# Admin Dashboard
VITE_API_URL=https://api.bridgecore.com
VITE_APP_NAME=BridgeCore Admin
```

---

## Environment-Specific Configurations

### Development (.env.development)

```env
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/bridgecore_dev
REDIS_URL=redis://localhost:6379/0
CORS_ORIGINS=*
RATE_LIMIT_ENABLED=False
```

### Staging (.env.staging)

```env
ENVIRONMENT=staging
DEBUG=False
LOG_LEVEL=INFO
DATABASE_URL=postgresql+asyncpg://bridgecore:pass@staging-db:5432/bridgecore_staging
REDIS_URL=redis://:pass@staging-redis:6379/0
CORS_ORIGINS=https://staging-admin.bridgecore.com
RATE_LIMIT_ENABLED=True
```

### Production (.env.production)

```env
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=WARNING
DATABASE_URL=postgresql+asyncpg://bridgecore:secure@prod-db:5432/bridgecore_prod
REDIS_URL=redis://:secure@prod-redis:6379/0
CORS_ORIGINS=https://admin.bridgecore.com
RATE_LIMIT_ENABLED=True
SENTRY_DSN=https://key@sentry.io/project
```

---

## Validation

BridgeCore validates environment variables at startup. Missing required variables will prevent the application from starting.

### Check Configuration

```bash
# Validate environment
python -c "from app.core.config import settings; print(settings)"

# Docker
docker-compose exec api python -c "from app.core.config import settings; print(settings)"
```

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `SECRET_KEY not set` | Missing secret key | Add SECRET_KEY to .env |
| `Invalid DATABASE_URL` | Wrong format | Check URL format |
| `Redis connection refused` | Redis not running | Start Redis service |
| `CORS origin invalid` | Malformed URL | Check CORS_ORIGINS format |
