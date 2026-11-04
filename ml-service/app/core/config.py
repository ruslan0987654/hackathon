"""Konfiqurasiya: .env faylından və ya mühit dəyişənlərindən oxunur."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.paths import BASE_DIR, DEFAULT_DATASET_DIR, DEFAULT_MODEL_DIR


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(BASE_DIR / ".env"), extra="ignore", protected_namespaces=())

    app_name: str = "SOCAR Smart Analytics ML Service"
    # Express -> ML servis autentifikasiyası (X-API-Key başlığı)
    api_key: str = ""
    # /model/retrain üçün ayrıca admin açarı (X-Admin-Key başlığı). Boşdursa retrain söndürülür.
    admin_api_key: str = ""
    model_dir: Path = DEFAULT_MODEL_DIR
    dataset_dir: Path = DEFAULT_DATASET_DIR
    max_request_bytes: int = 5_000_000
    max_batch_size: int = 100
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
