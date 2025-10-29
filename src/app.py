import structlog
from fastapi import FastAPI

from src.core.config import settings
from src.core.logging import configure_logging
from src.api.v1.wallets import router as wallets_router

logger = structlog.get_logger()


def create_app() -> FastAPI:
    # Конфигурация логирования
    configure_logging(settings)

    # Создание приложения FastAPI
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug
    )
    
    # Healthcheck endpoint
    @app.get("/ping", summary="Healthcheck", tags=["health"])
    async def healthcheck() -> dict[str, str]:
        return {"status": "OK", "message": "Pong"}

    # Подключение роутеров
    app.include_router(wallets_router, prefix="/api/v1")

    return app


# Создание экземпляра приложения
app = create_app()