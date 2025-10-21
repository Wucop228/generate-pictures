import os
from pathlib import Path
import sys

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
GENERATED_PICTURES_DIR = BASE_DIR / "generated_pictures"
MAX_WORKERS = 3
TASK_TTL = 3600
MODEL_NAME = "dreamshaper-8"


class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    SECRET_KEY: str
    ALGORITHM: str
    REDIS_URL: str

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env")
    )


settings = Settings()

def get_url_db():
    return (f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@"
            f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")

def get_auth_data():
    return {"secret_key": settings.SECRET_KEY, "algorithm": settings.ALGORITHM}