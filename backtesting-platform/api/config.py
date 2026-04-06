from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BTP_", env_file=".env")

    db_url: str = f"sqlite:///{Path(__file__).resolve().parent.parent / 'db' / 'backtesting.db'}"
    price_cache_dir: Path = Path(__file__).resolve().parent.parent / "data" / "cache"
    cors_origins: list[str] = ["http://localhost:5173"]
    log_level: str = "INFO"


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
