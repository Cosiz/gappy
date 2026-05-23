from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "Project Gappy"
    API_V1_STR: str = "/api/v1"
    PORT: int = 8080
    
    # Use SQLite for prototype (easy local testing)
    DATABASE_URL: str = "sqlite:///./gappy.db"
    
    # Redis (for Celery later)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # LiteLLM default model
    LITELLM_MODEL: str = "gpt-4o-mini"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()