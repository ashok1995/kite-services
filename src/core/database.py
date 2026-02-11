"""
Database Module
===============

Database initialization and connection management.
"""

import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from config.settings import get_settings
from core.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Prefer DATABASE_URL from env (pydantic-settings may not pass to nested models in Docker)
_database_url = os.environ.get("DATABASE_URL") or settings.database.url

# Create declarative base for ORM models
Base = declarative_base()

# Create async engine
engine = create_async_engine(
    _database_url,
    echo=settings.database.echo,
    future=True,
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


def _get_sqlite_db_path(db_url: str) -> str:
    """Extract path from SQLite URL. Preserves relative paths (e.g. ./data/db.db)."""
    if "///" in db_url:
        path = db_url.split("///", 1)[-1]
    elif "//" in db_url:
        path = db_url.split("//", 1)[-1]
    else:
        path = db_url.split("://", 1)[-1]
    # Preserve relative paths (./data); only add / for bare relative (data/foo)
    if path.startswith("/") or path.startswith("."):
        return path
    return f"/{path}"


async def init_database():
    """Initialize database - create tables."""
    logger.info("Initializing database...")

    try:
        import os
        from pathlib import Path

        db_url = _database_url
        if "sqlite" in db_url:
            db_path = _get_sqlite_db_path(db_url)
            db_dir = os.path.dirname(db_path)
            if db_dir:
                # Resolve relative paths from cwd (e.g. ./data -> project/data)
                target = Path(db_dir).resolve()
                target.mkdir(parents=True, exist_ok=True)
                try:
                    os.chmod(str(target), 0o777)  # nosec B103 - dev-only writable db directory
                except OSError:
                    pass  # May fail in restricted envs
                logger.info(f"✅ Database directory ensured: {target}")

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}", exc_info=True)
        raise


async def close_database():
    """Close database connections."""
    logger.info("Closing database connections...")

    try:
        await engine.dispose()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"❌ Error closing database: {e}")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database sessions.

    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
