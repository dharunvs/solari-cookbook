"""Minimal PostgreSQL readiness boundary."""

from __future__ import annotations

from functools import lru_cache

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from noxyn_api.config import load_settings, sqlalchemy_database_url


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    """Create one process-local connection pool."""
    settings = load_settings()
    return create_async_engine(
        sqlalchemy_database_url(settings.database_url),
        pool_pre_ping=True,
    )


async def database_is_ready() -> bool:
    """Return whether PostgreSQL accepts a trivial query."""
    try:
        async with get_engine().connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception:
        return False
    return True


@lru_cache(maxsize=1)
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the process-local async session boundary."""
    return async_sessionmaker(get_engine(), expire_on_commit=False)
