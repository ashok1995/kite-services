"""
Database Module
===============

Database initialization and connection management.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from core.logging_config import get_logger
from config.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()

# Create declarative base for ORM models
Base = declarative_base()

# Create async engine
engine = create_async_engine(
    settings.database.url,
    echo=settings.database.echo,
    future=True,
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_database():
    """Initialize database - create tables."""
    logger.info("Initializing database...")
    
    try:
        # Ensure database directory exists
        import os
        from pathlib import Path
        
        # Extract database path from URL
        db_url = settings.database.url
        if "sqlite" in db_url:
            # Parse SQLite URL: sqlite+aiosqlite:////app/data/db.db
            if "///" in db_url:
                # Absolute path
                db_path = db_url.split("///")[-1]
            elif "//" in db_url:
                # Relative path
                db_path = db_url.split("//")[-1]
            else:
                db_path = db_url.split("://")[-1]
            
            # Get directory
            db_dir = os.path.dirname(db_path)
            if db_dir:
                Path(db_dir).mkdir(parents=True, exist_ok=True)
                os.chmod(db_dir, 0o777)
                logger.info(f"✅ Database directory ensured: {db_dir}")
        
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

