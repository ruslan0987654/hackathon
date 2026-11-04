"""Test köməkçiləri: kiçik model dəsti öyrədir (bir dəfə) və sintetik quyudan sorğu yaradır."""
from __future__ import annotations

import tempfile
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path

import numpy as np

from app.models.bundle import load_bundle
from app.preprocessing.synthetic import simulate_wells


@lru_cache(maxsize=1)
def model_dir() -> Path:
    from training.train_all import run_training
    d = Path(tempfile.mkdtemp(prefix="socar_ml_test_"))
    run_training(out_dir=d, n_wells=90, n_days=800, seed=11, step=5, save_dataset=False, log=lambda *_: None)
    return d


@lru_cache(maxsize=1)
def bundle():
    return load_bundle(model_dir())


@lru_cache(maxsize=1)
def wells():
    return simulate_wells(6, 800, 2024)


def make_payload(well_idx: int = 0, day: int = 600, history_days: int = 120, end: datetime | None = None,
                 well_id: str = "TEST-1") -> dict:
    w = wells()[well_idx]
    end = end or datetime(2026, 11, 1)
    pidx = np.flatnonzero(w["present"])
    sl = pidx[(pidx <= day) & (pidx > day - history_days)]
    recs = []
    for d in sl:
        r = {"timestamp": end + timedelta(days=int(d - day))}
        for k, v in w["cols"].items():
            if k == "pumpFault":
                r["pumpStatus"] = None if np.isnan(v[d]) else ("fault" if v[d] == 1 else "running")
            else:
                r[k] = None if np.isnan(v[d]) else float(v[d])
        recs.append(r)
    return {"wellId": well_id, "wellType": w["static_info"]["wellType"], "depth": w["static_info"]["depth"],
            "productionTarget": float(w["plan"][day]), "history": recs}
