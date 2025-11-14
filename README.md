# FastAPI Middleware - BridgeCore

A powerful middleware API built with FastAPI to bridge Flutter applications with external ERP/CRM systems (Odoo, SAP, Salesforce, etc.).

## Features

### Core Features
- 🔐 **Secure Authentication**: JWT-based authentication with refresh tokens
- 🔄 **Data Unification**: Automatic field mapping between different system versions
- 🎯 **Multi-System Support**: Odoo (13/16/18), SAP, Salesforce, and more
- ⚡ **High Performance**: Redis caching + Connection pooling + Async operations
- 📝 **Audit Trail**: Complete logging of all operations with user tracking
- 🧪 **Well Tested**: Comprehensive test coverage with unit & integration tests
- 🐳 **Docker Ready**: Full Docker and Docker Compose support
- 📊 **Auto Documentation**: Interactive API docs with Swagger/ReDoc

### Advanced Features
- 🔄 **Version Migration**: Automatic data transformation between system versions (e.g., Odoo 13 → 18)
- 🎯 **Smart Field Fallback**: Intelligent field mapping with automatic fallback options
- 📦 **Batch Operations**: Execute multiple CRUD operations in a single request
- 📁 **File Management**: Upload/download files with attachment support
- 📊 **Report Generation**: Generate PDF, Excel, and CSV reports (Sales, Inventory, Partners)
- 🔍 **Barcode Integration**: Product lookup and inventory management via barcode
- 🌍 **Multi-Language Support**: API responses in English, Arabic, and French
- 🎨 **Universal Schema**: Unified data models across different ERP/CRM systems
- ⚙️ **Connection Retry Logic**: Automatic retry with exponential backoff
- 🔌 **Adapter Pattern**: Easy integration with new systems

## Technology Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL (async with asyncpg)
- **Cache**: Redis
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Logging**: Loguru
- **Testing**: Pytest + httpx
- **Security**: JWT (python-jose) + bcrypt

## Project Structure

```
BridgeCore/
├── app/
│   ├── api/
│   │   └── routes/          # API endpoints
│   ├── core/                # Core configuration
│   ├── db/                  # Database setup
│   ├── models/              # SQLAlchemy models
│   ├── repositories/        # Data access layer
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   ├── middleware/          # Custom middleware
│   ├── utils/               # Utilities
│   └── main.py              # Application entry point
├── tests/
│   ├── unit/                # Unit tests
│   └── integration/         # Integration tests
├── docker/                  # Docker configuration
├── alembic/                 # Database migrations
├── logs/                    # Application logs
├── requirements.txt         # Dependencies
└── Makefile                 # Command shortcuts
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/BridgeCore.git
cd BridgeCore
```

2. **Setup environment**

```bash
make setup
```

This creates a `.env` file and logs directory. Update `.env` with your configuration.

3. **Install dependencies**

```bash
make install
```

4. **Run database migrations**

```bash
make migrate
```

5. **Start the development server**

```bash
make run
```

The API will be available at `http://localhost:8000`

- API Documentation: `http://localhost:8000/docs`
- Alternative Docs: `http://localhost:8000/redoc`

### Docker Setup

Run everything with Docker:

```bash
# Start all services
make docker-up

# View logs
make docker-logs

# Stop all services
make docker-down
```

## Configuration

Edit `.env` file:

```env
# Application
APP_NAME=FastAPI Middleware
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/middleware_db

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-jwt-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Logging
LOG_LEVEL=INFO
LOG_FILE_PATH=logs/app.log
```

## API Usage

### Authentication

1. **Login**

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "system_credentials": {
      "system_type": "odoo",
      "system_version": "16.0",
      "credentials": {
        "url": "https://demo.odoo.com",
        "database": "demo",
        "username": "admin",
        "password": "admin"
      }
    }
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

2. **Use the token**

```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Health Checks

```bash
# Basic health check
curl http://localhost:8000/health

# Database health
curl http://localhost:8000/health/db

# Redis health
curl http://localhost:8000/health/redis
```

### CRUD Operations

#### Create Record

```bash
curl -X POST "http://localhost:8000/systems/odoo-prod/create?model=res.partner" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ahmed Ali",
    "email": "ahmed@example.com",
    "phone": "+966501234567"
  }'
```

#### Read Records

```bash
curl -X GET "http://localhost:8000/systems/odoo-prod/read?model=res.partner&limit=10&fields=name,email,phone" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Update Record

```bash
curl -X PUT "http://localhost:8000/systems/odoo-prod/update/42?model=res.partner" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+966502222222"}'
```

#### Delete Record

```bash
curl -X DELETE "http://localhost:8000/systems/odoo-prod/delete/42?model=res.partner" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Batch Operations

Execute multiple operations in one request:

```bash
curl -X POST "http://localhost:8000/batch" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "system_id": "odoo-prod",
    "operations": [
      {
        "action": "create",
        "model": "res.partner",
        "data": {"name": "Partner 1", "email": "p1@example.com"}
      },
      {
        "action": "update",
        "model": "res.partner",
        "record_id": 42,
        "data": {"phone": "+966501234567"}
      },
      {
        "action": "read",
        "model": "product.product",
        "domain": [["type", "=", "product"]],
        "fields": ["name", "list_price"]
      }
    ]
  }'
```

### Barcode Operations

```bash
# Lookup product by barcode
curl -X GET "http://localhost:8000/barcode/odoo-prod/lookup/6281234567890" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Search products
curl -X GET "http://localhost:8000/barcode/odoo-prod/search?name=laptop&limit=5" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### File Operations

```bash
# Upload file
curl -X POST "http://localhost:8000/files/odoo-prod/upload?model=res.partner&record_id=42" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/image.jpg"

# Download file
curl -X GET "http://localhost:8000/files/odoo-prod/download/123" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  --output downloaded_file.jpg

# Get attachments
curl -X GET "http://localhost:8000/files/odoo-prod/attachments?model=res.partner&record_id=42" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Report Generation

```bash
# Sales report
curl -X GET "http://localhost:8000/files/odoo-prod/report/sales?format=xlsx&start_date=2024-01-01&end_date=2024-12-31" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  --output sales_report.xlsx

# Inventory report
curl -X GET "http://localhost:8000/files/odoo-prod/report/inventory?format=xlsx" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  --output inventory_report.xlsx

# Partners report
curl -X GET "http://localhost:8000/files/odoo-prod/report/partners?format=csv" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  --output partners_report.csv
```

### Export Data

```bash
curl -X POST "http://localhost:8000/files/odoo-prod/export" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "res.partner",
    "domain": [["is_company", "=", true]],
    "fields": ["name", "email", "phone", "city"],
    "format": "xlsx"
  }' \
  --output export.xlsx
```

## Development

### Running Tests

```bash
# Run all tests
make test

# Run unit tests only
make test-unit

# Run integration tests only
make test-integration
```

### Code Quality

```bash
# Lint code
make lint

# Format code
make format
```

### Database Migrations

```bash
# Create new migration
make migrate-create

# Apply migrations
make migrate

# Rollback one migration
make migrate-downgrade
```

## Architecture

### Key Components

1. **Logging System** (`app/utils/logger.py`)
   - Console logging for development
   - File logging with rotation
   - Error-only logging
   - JSON logging for production

2. **Audit Service** (`app/services/audit_service.py`)
   - Tracks all operations
   - User activity monitoring
   - Failed operation tracking

3. **Cache Service** (`app/services/cache_service.py`)
   - Redis-based caching
   - Automatic caching decorator
   - Pattern-based deletion

4. **Repository Pattern** (`app/repositories/`)
   - Optimized database queries
   - Eager loading to avoid N+1
   - Bulk operations support

5. **Middleware**
   - Logging middleware for request/response tracking
   - CORS middleware
   - Error handling middleware

## Performance Features

- **Connection Pooling**: Optimized database connection management
- **Redis Caching**: Fast data retrieval
- **Async/Await**: Non-blocking I/O operations
- **Background Tasks**: Non-blocking operation execution
- **Query Optimization**: Eager loading, bulk operations

## Security

- JWT-based authentication
- Password hashing with bcrypt
- SQL injection prevention (parameterized queries)
- CORS configuration
- Rate limiting ready
- Secure headers

## Monitoring & Logging

All requests are logged with:
- Unique request ID
- Client IP address
- User agent
- Request duration
- Response status

Logs are stored in:
- `logs/app.log` - All logs
- `logs/errors.log` - Errors only
- `logs/app.json` - JSON format (production)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run tests and linting
6. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: https://github.com/yourusername/BridgeCore/issues
- Email: support@example.com

## Roadmap

- [ ] Support for more external systems (SAP, Salesforce)
- [ ] GraphQL API support
- [ ] WebSocket support for real-time updates
- [ ] Advanced field mapping UI
- [ ] Performance monitoring dashboard
- [ ] Multi-tenancy support
- [ ] API rate limiting implementation
- [ ] Kubernetes deployment configs

## Authors

- Your Name - Initial work

## Acknowledgments

- FastAPI framework
- SQLAlchemy team
- Python community
