from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings
from app.models import Base


def _resolve_sqlite_database_url(database_url: str) -> str:
    prefix = "sqlite+aiosqlite:///"
    if not database_url.startswith(prefix):
        return database_url

    raw_path = database_url.removeprefix(prefix)
    db_path = Path(raw_path)
    if not db_path.is_absolute():
        db_path = get_settings().project_root / db_path

    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"{prefix}{db_path.as_posix()}"


def create_engine() -> AsyncEngine:
    settings = get_settings()
    database_url = _resolve_sqlite_database_url(settings.database_url)
    return create_async_engine(database_url, echo=False, future=True)


engine = create_engine()
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
