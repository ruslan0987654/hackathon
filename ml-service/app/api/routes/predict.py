"""Proqnoz endpoint-ləri."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_bundle, require_api_key
from app.core.config import Settings, get_settings
from app.models.bundle import ModelBundle
from app.schemas.responses import (AnomalyResponse, BatchResponse, EquipmentResponse, FullAnalysisResponse,
                                   ProductionResponse, RiskResponse)
from app.schemas.well import BatchRequest, WellInput
from app.services import analysis
from app.utils.serialize import clean

log = logging.getLogger(__name__)
router = APIRouter(prefix="/predict", tags=["predict"], dependencies=[Depends(require_api_key)])


def _prep(body: WellInput) -> analysis.Prepared:
    try:
        return analysis.prepare(body.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _wrap(prep: analysis.Prepared, bundle: ModelBundle, part: dict) -> dict:
    return clean({**analysis.header(prep, bundle), **part, "dataQuality": prep.quality,
                  "warnings": prep.quality["warnings"]})


@router.post("/production", response_model=ProductionResponse)
def predict_production(body: WellInput, bundle: ModelBundle = Depends(get_bundle)):
    prep = _prep(body)
    return _wrap(prep, bundle, analysis.run_production(prep, bundle))


@router.post("/anomaly", response_model=AnomalyResponse)
def predict_anomaly(body: WellInput, bundle: ModelBundle = Depends(get_bundle)):
    prep = _prep(body)
    return _wrap(prep, bundle, analysis.run_anomaly(prep, bundle))


@router.post("/risk", response_model=RiskResponse)
def predict_risk(body: WellInput, bundle: ModelBundle = Depends(get_bundle)):
    prep = _prep(body)
    return _wrap(prep, bundle, analysis.run_risk(prep, bundle))


@router.post("/equipment", response_model=EquipmentResponse)
def predict_equipment(body: WellInput, bundle: ModelBundle = Depends(get_bundle)):
    prep = _prep(body)
    return _wrap(prep, bundle, analysis.run_equipment(prep, bundle))


@router.post("/full-analysis", response_model=FullAnalysisResponse)
def predict_full(body: WellInput, bundle: ModelBundle = Depends(get_bundle)):
    return analysis.full_analysis(_prep(body), bundle)


@router.post("/batch", response_model=BatchResponse)
def predict_batch(body: BatchRequest, bundle: ModelBundle = Depends(get_bundle),
                  settings: Settings = Depends(get_settings)):
    if len(body.wells) > settings.max_batch_size:
        raise HTTPException(status_code=422, detail=f"Bir sorğuda ən çox {settings.max_batch_size} quyu göndərilə bilər.")
    results, ok = [], 0
    for well in body.wells:
        try:
            results.append({"wellId": well.wellId, "status": "ok",
                            "result": analysis.full_analysis(analysis.prepare(well.model_dump()), bundle)})
            ok += 1
        except Exception as exc:  # noqa: BLE001 - bir quyunun xətası digərlərinə təsir etməsin
            log.exception("Batch: %s", well.wellId)
            results.append({"wellId": well.wellId, "status": "error", "error": f"{type(exc).__name__}: {exc}"})
    return {"count": len(results), "succeeded": ok, "failed": len(results) - ok, "results": results}
