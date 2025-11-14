# FastAPI Middleware - BridgeCore

A powerful middleware API built with FastAPI to bridge Flutter applications with external ERP/CRM systems (Odoo, SAP, Salesforce, etc.).

## Features

- 🔐 **Secure Authentication**: JWT-based authentication with refresh tokens
- 🔄 **Data Unification**: Automatic field mapping between different system versions
- 🎯 **Multi-System Support**: Odoo, SAP, Salesforce, and more
- ⚡ **High Performance**: Redis caching + Connection pooling
- 📝 **Audit Trail**: Complete logging of all operations
- 🧪 **Well Tested**: Comprehensive test coverage
- 🐳 **Docker Ready**: Full Docker and Docker Compose support
- 📊 **Auto Documentation**: Interactive API docs with Swagger/ReDoc

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
