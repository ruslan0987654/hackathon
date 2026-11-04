"""Autentifikasiya və model asılılıqları."""
from __future__ import annotations

import hmac
from typing import Optional

from fastapi import Depends, Header, HTTPException

from app.core.config import Settings, get_settings
from app.models.bundle import ModelBundle
from app.models.registry import registry


def _same(provided: Optional[str], expected: str) -> bool:
    return bool(provided) and hmac.compare_digest(provided.encode("utf-8"), expected.encode("utf-8"))


def require_api_key(x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
                    settings: Settings = Depends(get_settings)) -> None:
    if not settings.api_key:
        raise HTTPException(status_code=503, detail="Servis konfiqurasiya olunmayıb: API_KEY təyin edilməyib (.env).")
    if not _same(x_api_key, settings.api_key):
        raise HTTPException(status_code=401, detail="Yanlış və ya çatışmayan X-API-Key.")


def require_admin_key(x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key"),
                      settings: Settings = Depends(get_settings)) -> None:
    if not settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Bu əməliyyat söndürülüb (ADMIN_API_KEY təyin edilməyib).")
    if not _same(x_admin_key, settings.admin_api_key):
        raise HTTPException(status_code=401, detail="Yanlış və ya çatışmayan X-Admin-Key.")


def get_bundle() -> ModelBundle:
    return registry.get()  # ModelNotReadyError -> main.py-də HTTP 503
