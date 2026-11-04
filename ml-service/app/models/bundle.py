"""Öyrədilmiş artefaktların (joblib) yüklənməsi. Pydantic/FastAPI-dan asılı deyil."""
from __future__ import annotations

import json
from pathlib import Path

import joblib

ARTIFACTS = ("production", "anomaly", "risk", "equipment")


class ModelBundle:
    def __init__(self, production: dict, anomaly: dict, risk: dict, equipment: dict, metadata: dict):
        self.production, self.anomaly, self.risk, self.equipment = production, anomaly, risk, equipment
        self.metadata = metadata

    @property
    def version(self) -> str:
        return self.metadata.get("modelVersion", "unknown")

    @property
    def data_basis(self) -> str:
        return self.metadata.get("dataBasis", "unknown")


def load_bundle(model_dir: Path | str) -> ModelBundle:
    d = Path(model_dir)
    missing = [n for n in (*(f"{a}.joblib" for a in ARTIFACTS), "metadata.json") if not (d / n).exists()]
    if missing:
        raise FileNotFoundError(
            f"Model faylları tapılmadı: {', '.join(missing)} ({d}). Əvvəlcə 'python -m training.train_all' icra edin.")
    # DİQQƏT: joblib/pickle yalnız ETİBARLI mənbədən (öz öyrətdiyiniz fayllar) yüklənməlidir.
    arts = {a: joblib.load(d / f"{a}.joblib") for a in ARTIFACTS}
    meta = json.loads((d / "metadata.json").read_text(encoding="utf-8"))
    return ModelBundle(metadata=meta, **arts)
