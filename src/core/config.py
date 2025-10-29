import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )
    
    app_name: str
    app_version: str
    debug: bool
    
    # База данных
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str
    
    # Логирование
    log_level: str
    
    # Пул подключений к БД (для прод окружения)
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30  # seconds
    pool_recycle: int = 1800  # seconds
    pool_pre_ping: bool = True
    
    @property
    def database_url(self) -> str:
        """Получить URL базы данных."""
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


# Глобальный экземпляр настроек
settings = Settings()
