from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "Project Gappy"
    API_V1_STR: str = "/api/v1"
    PORT: int = 8080

    # Database
    # Examples:
    #   SQLite (local dev):   sqlite:///./gappy.db
    #   PostgreSQL + PGVector: postgresql://user:password@host:5432/gappy
    DATABASE_URL: str = "sqlite:///./gappy.db"

    # Redis (required for Celery)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def celery_broker(self) -> str:
        return self.CELERY_BROKER_URL or self.REDIS_URL

    @property
    def celery_backend(self) -> str:
        return self.CELERY_RESULT_BACKEND or self.REDIS_URL

    @property
    def is_postgres(self) -> bool:
        return self.DATABASE_URL.startswith("postgresql")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
