from functools import lru_cache
from pathlib import Path
from typing import Literal
from uuid import UUID

from pydantic import Field, HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[3] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(repr=False)
    frontend_origin: HttpUrl
    app_env: Literal["development", "test", "production"] = "development"
    demo_registry_organization_id: UUID | None = None

    @field_validator("database_url")
    @classmethod
    def require_psycopg(cls, value: str) -> str:
        if make_url(value).drivername != "postgresql+psycopg":
            raise ValueError("DATABASE_URL must use postgresql+psycopg")
        return value

    @field_validator("frontend_origin")
    @classmethod
    def require_origin(cls, value: HttpUrl) -> HttpUrl:
        if value.path not in (None, "/") or value.query or value.fragment or value.username or value.password:
            raise ValueError("FRONTEND_ORIGIN must be an HTTP(S) origin without a path or credentials")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
