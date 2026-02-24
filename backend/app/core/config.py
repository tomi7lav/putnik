from __future__ import annotations


from functools import lru_cache
from typing import Literal, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    app_name: str = "Putnik API"
    environment: Literal["dev", "staging", "prod"] = "dev"
    api_v1_str: str = "/api/v1"

    secret_key: str
    access_token_expire_minutes: int = 60

    database_url: str
    database_sync_url: Optional[str] = None

    whatsapp_verify_token: str
    whatsapp_app_secret: str

    def resolved_sync_database_url(self) -> str:
        if self.database_sync_url:
            return self.database_sync_url
        return self.database_url.replace("postgresql+asyncpg", "postgresql+psycopg")


@lru_cache
def get_settings() -> Settings:
    return Settings()
