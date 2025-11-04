import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

BASE_DIR = Path(__file__).resolve().parent.parent.parent
GENERATED_PICTURES_DIR = BASE_DIR / "generated_pictures"
TASK_TTL = 3600
MODEL_NAME = "dreamshaper-8"


class Settings(BaseSettings):
    DATABASE_URL: str | None = Field(default=None)

    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    SECRET_KEY: str
    ALGORITHM: str

    REDIS_URL: str

    S3_KEY_ID: str
    S3_SECRET_KEY: str
    S3_BUCKET_NAME: str

    FORCE_DEVICE: str = "cpu"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env"),
        extra="ignore"
    )

    def async_db_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


settings = Settings()

def get_url_db() -> str:
    return settings.async_db_url()


def get_sync_url_db() -> str:
    url = settings.DATABASE_URL
    if url:
        if url.startswith("sqlite+aiosqlite:"):
            return url.replace("sqlite+aiosqlite", "sqlite", 1)
        if url.startswith("postgresql+asyncpg:"):
            return url.replace("postgresql+asyncpg", "postgresql", 1)
        return url
    return (
        f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}"
        f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    )

def get_auth_data():
    return {"secret_key": settings.SECRET_KEY, "algorithm": settings.ALGORITHM}