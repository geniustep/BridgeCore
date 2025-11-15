"""
Database session management with connection pooling
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings

# Create async engine with optimized connection pool
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,

    # Connection Pool Settings
    pool_size=settings.DB_POOL_SIZE,              # Permanent connections
    max_overflow=settings.DB_MAX_OVERFLOW,        # Additional connections when needed
    pool_timeout=30,                               # Wait time to get a connection
    pool_recycle=3600,                             # Recycle connections every hour
    pool_pre_ping=True,                            # Check connection validity before use

    # Performance
    future=True,
    connect_args={
        "server_settings": {
            "jit": "off"  # Disable JIT in PostgreSQL for simple queries
        }
    }
)

# Session Factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_db() -> AsyncSession:
    """
    Dependency to get database session

    Usage:
        @router.get("/example")
        async def example(db: AsyncSession = Depends(get_db)):
            # Use db here
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database (create tables)"""
    from app.db.base import Base
    # Import all models to register them with SQLAlchemy
    from app.models.user import User
    from app.models.system import System
    from app.models.audit_log import AuditLog
    from app.models.field_mapping import FieldMapping

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections"""
    await engine.dispose()
