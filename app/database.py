"""
Database Setup for ThoughtCaptcha Backend.

This module configures the SQLAlchemy engine and session management
for asynchronous interaction with the PostgreSQL database.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import get_settings

settings = get_settings()

DATABASE_URL = settings.DATABASE_URL

# Create the SQLAlchemy async engine
# connect_args is useful for specific driver options, like SSL modes if needed later.
# pool_pre_ping checks connections before use, helping prevent errors with stale connections.
# echo=True can be useful for debugging SQL locally, but should be False in production.
engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    # echo=True # Uncomment for local SQL logging
)

# Create a configured "Session" class
# expire_on_commit=False prevents attributes from being expired after commit,
# which is often useful in async contexts with FastAPI dependencies.
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)

# Base class for declarative models
Base = declarative_base()

async def get_db() -> AsyncSession:
    """
    FastAPI dependency that yields an async database session.

    Manages the session lifecycle per request, ensuring it's closed properly.
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

async def init_db():
    """
    Initialize the database (create tables).
    This is a simple approach for demos. For production, use Alembic migrations.
    """
    async with engine.begin() as conn:
        # In a real app, avoid dropping tables like this
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all) 