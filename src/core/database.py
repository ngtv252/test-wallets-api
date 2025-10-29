from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.core.config import settings

# Создание async engine с настраиваемым пулом (в тестах переопределяется)
engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_size=settings.pool_size,
    max_overflow=settings.max_overflow,
    pool_timeout=settings.pool_timeout,
    pool_recycle=settings.pool_recycle,
    pool_pre_ping=settings.pool_pre_ping,
)

# Создание фабрики сессий
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Получить сессию базы данных."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
