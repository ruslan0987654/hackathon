"""Prosesdə modelləri saxlayan sadə registry (thread-safe)."""
from __future__ import annotations

import logging
from pathlib import Path
from threading import RLock

from app.models.bundle import ModelBundle, load_bundle

log = logging.getLogger(__name__)


class ModelNotReadyError(RuntimeError):
    """Model yüklənməyib -> HTTP 503."""


class ModelRegistry:
    def __init__(self) -> None:
        self._bundle: ModelBundle | None = None
        self.error: str | None = None
        self._lock = RLock()
        self.training: dict = {"status": "idle"}

    def load(self, model_dir: Path | str) -> bool:
        with self._lock:
            try:
                self._bundle = load_bundle(model_dir)
                self.error = None
                log.info("Modellər yükləndi: %s", self._bundle.version)
                return True
            except Exception as exc:  # noqa: BLE001 - servis işləməyə davam etməlidir (503 qaytaracaq)
                self._bundle, self.error = None, str(exc)
                log.error("Modellər yüklənmədi: %s", exc)
                return False

    @property
    def ready(self) -> bool:
        return self._bundle is not None

    def get(self) -> ModelBundle:
        b = self._bundle
        if b is None:
            raise ModelNotReadyError(self.error or "Modellər yüklənməyib")
        return b


registry = ModelRegistry()
