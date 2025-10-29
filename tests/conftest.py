import asyncio
import os
import sys
from collections.abc import AsyncGenerator
from enum import StrEnum
from pathlib import Path

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool, StaticPool

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.app import app
from src.core.database import get_db_session
from src.wallet.models import Base, Wallet


class DatabaseBackend(StrEnum):
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"


async def _check_postgres_connection(url: str) -> bool:
    engine = create_async_engine(url, echo=False, poolclass=NullPool)
    try:
        async with asyncio.timeout(5):
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
        return True

    except Exception:
        return False
        
    finally:
        await engine.dispose()


def detect_backend() -> DatabaseBackend:
    required = ("DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME")
    if all(os.getenv(name) for name in required):
        url = build_database_url(DatabaseBackend.POSTGRESQL)
        if asyncio.run(_check_postgres_connection(url)):
            return DatabaseBackend.POSTGRESQL
    return DatabaseBackend.SQLITE


def build_database_url(backend: DatabaseBackend) -> str:
    match backend:
        case DatabaseBackend.POSTGRESQL:
            return (
                "postgresql+asyncpg://"
                f"{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
                f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}"
                f"/{os.getenv('DB_NAME')}"
            )
        case DatabaseBackend.SQLITE:
            return "sqlite+aiosqlite:///:memory:"


def create_engine(backend: DatabaseBackend, url: str) -> AsyncEngine:
    match backend:
        case DatabaseBackend.POSTGRESQL:
            return create_async_engine(url, echo=False, poolclass=NullPool, pool_pre_ping=True)
        case DatabaseBackend.SQLITE:
            return create_async_engine(
                url,
                echo=False,
                poolclass=StaticPool,
                connect_args={"check_same_thread": False},
            )


def bootstrap_engine() -> tuple[DatabaseBackend, AsyncEngine, async_sessionmaker[AsyncSession]]:
    backend = detect_backend()
    engine = create_engine(backend, build_database_url(backend))
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    return backend, engine, session_factory


BACKEND, TEST_ENGINE, SESSION_FACTORY = bootstrap_engine()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TEST_ENGINE.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with SESSION_FACTORY() as session:
        try:
            yield session
        finally:
            await session.close()

    async with TEST_ENGINE.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        async with SESSION_FACTORY() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http_client:
        yield http_client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def wallet(db_session: AsyncSession) -> Wallet:
    wallet_obj = Wallet(balance=1000)
    db_session.add(wallet_obj)
    await db_session.commit()
    await db_session.refresh(wallet_obj)
    return wallet_obj


@pytest_asyncio.fixture
async def empty_wallet(db_session: AsyncSession) -> Wallet:
    wallet_obj = Wallet(balance=0)
    db_session.add(wallet_obj)
    await db_session.commit()
    await db_session.refresh(wallet_obj)
    return wallet_obj
