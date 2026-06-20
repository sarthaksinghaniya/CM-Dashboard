"""
Database session configuration — production-grade.

Handles both SQLite (aiosqlite) and PostgreSQL (asyncpg) transparently.
SQLite does NOT support pool_size/max_overflow, so we conditionally set them.
"""
import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from app.core.config import settings

logger = logging.getLogger("cm_dashboard.db.session")

_is_sqlite = settings.SQLALCHEMY_DATABASE_URI.startswith("sqlite")

if _is_sqlite:
    # SQLite requires StaticPool + check_same_thread=False for async usage.
    # pool_size / max_overflow are NOT supported by SQLite drivers.
    engine = create_async_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        echo=False,
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    logger.info("[DB] Configured SQLite async engine with StaticPool.")
else:
    # PostgreSQL with full connection-pool tuning
    engine = create_async_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        echo=False,
        future=True,
        pool_size=20,
        max_overflow=10,
        pool_recycle=1800,
        pool_timeout=30,
        pool_pre_ping=True,
    )
    logger.info("[DB] Configured PostgreSQL async engine with connection pooling.")

# Async session factory — expire_on_commit=False avoids lazy-load surprises
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:  # type: ignore
    """FastAPI dependency that provides a scoped async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
