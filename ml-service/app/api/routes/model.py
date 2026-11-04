"""Model məlumatı və (qorunan) yenidən öyrətmə."""
from __future__ import annotations

import logging
import shutil
import threading
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.api.dependencies import get_bundle, require_admin_key, require_api_key
from app.core.config import Settings, get_settings
from app.models.bundle import ModelBundle
from app.models.registry import registry
from app.schemas.responses import RetrainResponse
from app.schemas.well import RetrainRequest
from app.utils.serialize import clean

log = logging.getLogger(__name__)
router = APIRouter(prefix="/model", tags=["model"])
_retrain_lock = threading.Lock()


def _summary(metrics: dict) -> dict:
    """Metrikaların qısa xülasəsi (tam metrikalar metadata.json-dadır)."""
    out = {}
    prod = metrics["production"]["metrics"]
    out["production"] = {k: {m: v["test"][m] for m in ("MAE", "RMSE", "R2", "baselineMAE_persistence", "intervalCoverage80")}
                         for k, v in prod.items()}
    out["anomaly"] = {m: metrics["anomaly"]["metrics"]["test"][m] for m in ("ROC_AUC", "recallAtThreshold", "precisionAtThreshold")}
    out["risk"] = {m: metrics["risk"]["metrics"]["test"][m] for m in ("accuracy", "macroF1", "ROC_AUC_ovr_macro")}
    out["equipment"] = {m: metrics["equipment"]["metrics"]["test"][m] for m in ("ROC_AUC", "averagePrecision", "brierScore", "baseRate")}
    return out


@router.get("/info", dependencies=[Depends(require_api_key)])
def model_info(bundle: ModelBundle = Depends(get_bundle)):
    m = bundle.metadata
    return clean({
        "modelVersion": m["modelVersion"], "trainedAt": m["trainedAt"], "dataBasis": m["dataBasis"],
        "warning": m["warning"], "dataset": m["dataset"], "environment": m["environment"],
        "models": {k: {"type": v["type"], "features": v["features"]} for k, v in m["models"].items()},
        "testMetricsSummary": _summary(m["models"]),
        "training": registry.training,
    })


def _do_retrain(settings: Settings, req: RetrainRequest) -> None:
    from training.train_all import run_training  # gec import: servis başlanğıcını yükləməsin
    model_dir = Path(settings.model_dir)
    tmp = model_dir / "_retrain_tmp"
    try:
        registry.training = {"status": "running", "startedAt": datetime.now(timezone.utc).isoformat(), "request": req.model_dump()}
        shutil.rmtree(tmp, ignore_errors=True)
        run_training(out_dir=tmp, n_wells=req.nWells, n_days=req.nDays, seed=req.seed, save_dataset=False,
                     log=lambda s: log.info(s))
        for f in tmp.iterdir():  # yalnız təlim tam bitdikdən sonra köhnə modellərin üstünə yazılır
            shutil.copy2(f, model_dir / f.name)
        registry.load(model_dir)
        registry.training = {"status": "done", "finishedAt": datetime.now(timezone.utc).isoformat(),
                             "modelVersion": registry.get().version}
    except Exception as exc:  # noqa: BLE001
        log.exception("Retrain uğursuz oldu")
        registry.training = {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        _retrain_lock.release()


@router.post("/retrain", response_model=RetrainResponse, status_code=202, dependencies=[Depends(require_admin_key)])
def retrain(body: RetrainRequest, background: BackgroundTasks, settings: Settings = Depends(get_settings)):
    """Yalnız ADMIN açarı ilə. Sintetik məlumatla yenidən öyrədir (real məlumat üçün training/ skriptlərini uyğunlaşdırın)."""
    if not _retrain_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="Yenidən öyrətmə artıq davam edir.")
    registry.training = {"status": "queued"}
    background.add_task(_do_retrain, settings, body)
    return RetrainResponse(status="accepted", message="Yenidən öyrətmə arxa planda başladı. Vəziyyət: GET /model/info -> training.")
