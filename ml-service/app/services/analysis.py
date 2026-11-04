"""Orkestrator: sorğunu hazırlayır, komponentləri icra edir, vahid cavabı yığır.

Hər komponent ayrıca try/except ilə qorunur: biri uğursuz olarsa digərləri işləməyə davam edir və
uğursuz komponent üçün SAXTA rəqəm deyil, null + status qaytarılır.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import numpy as np

from app.models.bundle import ModelBundle
from app.preprocessing.features import (apply_provided_aggregates, build_series, compute_features,
                                        static_from_payload)
from app.services import anomaly, efficiency, equipment, forecast, quality as qsvc, recommendations, risk
from app.utils.serialize import clean

log = logging.getLogger(__name__)


@dataclass
class Prepared:
    payload: dict
    ts: np.ndarray
    cols: dict
    first_dt: datetime
    last_dt: datetime
    n_records: int
    feats: dict
    quality: dict
    base_conf: float


def prepare(payload: dict[str, Any], now: datetime | None = None) -> Prepared:
    ts, cols, first_dt, last_dt, n = build_series(payload)
    static = static_from_payload(payload, last_dt)
    feats = compute_features(ts, cols, static)
    used = apply_provided_aggregates(feats, payload)
    q = qsvc.assess(ts, cols, last_dt, n, payload, used, now)
    return Prepared(payload, ts, cols, first_dt, last_dt, n, feats, q, qsvc.base_confidence(q))


def _safe(name: str, fn, *args):
    try:
        return fn(*args)
    except Exception as exc:  # noqa: BLE001 - komponent səviyyəsində izolyasiya
        log.exception("Komponent xətası: %s", name)
        return {"status": "error", "statusMessage": f"{name} hesablanarkən daxili xəta: {type(exc).__name__}"}


def _conf(score: float, basis: str) -> dict:
    return {"score": round(float(np.clip(score, 0, 1)), 2), "level": qsvc.confidence_level(score), "basis": basis}


def header(prep: Prepared, bundle: ModelBundle) -> dict:
    return {
        "wellId": prep.payload["wellId"],
        "analysisTimestamp": datetime.now(timezone.utc).isoformat(),
        "modelVersion": bundle.version,
        "dataBasis": bundle.data_basis,
    }


def run_production(prep: Prepared, bundle: ModelBundle) -> dict:
    res = _safe("production", forecast.run, prep.feats, bundle.production, prep.ts, prep.cols, prep.payload,
                prep.first_dt, prep.last_dt, prep.quality)
    score = prep.base_conf
    iv = (res.get("predictionIntervals") or {}).get("30d")
    if iv and res.get("predictedProduction30d"):
        rel = (iv["upper"] - iv["lower"]) / max(res["predictedProduction30d"], 1e-9)
        score = prep.base_conf / (1.0 + rel)
    res["confidence"] = _conf(score, "Məlumat tamlığı x tarixçə uzunluğu / (1 + 30 günlük interval eni). Evristikdir, statistik ehtimal deyil.")
    return res


def run_anomaly(prep: Prepared, bundle: ModelBundle) -> dict:
    return _safe("anomaly", anomaly.run, prep.feats, bundle.anomaly, prep.ts, prep.cols)


def run_risk(prep: Prepared, bundle: ModelBundle) -> dict:
    return _safe("risk", risk.run, prep.feats, bundle.risk)


def run_equipment(prep: Prepared, bundle: ModelBundle) -> dict:
    return _safe("equipment", equipment.run, prep.feats, bundle.equipment)


def run_efficiency(prep: Prepared) -> dict:
    return _safe("efficiency", efficiency.run, prep.ts, prep.cols, prep.payload)


def _indicators(f: dict) -> dict:
    keys = {
        "productionDeclineRate": "production_decline_rate", "pressureChangeRate": "pressure_change_rate",
        "waterCutTrend": "waterCut_trend", "production7dAvg": "production_7d_avg",
        "production30dAvg": "production_30d_avg", "production90dAvg": "production_90d_avg",
        "production7dChangePct": "production_7d_change_pct", "production30dChangePct": "production_30d_change_pct",
        "targetAttainment30d": "target_attainment_30d",
    }
    out = {k: (None if not np.isfinite(f.get(v, np.nan)) else round(float(f[v]), 4)) for k, v in keys.items()}
    out["units"] = {"productionDeclineRate": "% / gün (müsbət = azalma)", "pressureChangeRate": "% / gün",
                    "waterCutTrend": "faiz bəndi / gün"}
    return out


def full_analysis(prep: Prepared, bundle: ModelBundle) -> dict:
    prod = run_production(prep, bundle)
    an = run_anomaly(prep, bundle)
    rk = run_risk(prep, bundle)
    eq = run_equipment(prep, bundle)
    ef = run_efficiency(prep)
    recs = _safe("recommendations", lambda: recommendations.build(
        {"production": prod, "anomaly": an, "risk": rk, "equipment": eq, "efficiency": ef},
        prep.feats, prep.quality, prep.base_conf))
    if isinstance(recs, dict):  # xəta qaytarıbsa
        recs = []
    warnings = list(prep.quality["warnings"])
    if bundle.data_basis == "synthetic":
        warnings.append("Modellər sintetik məlumatla öyrədilib; nəticələr yalnız inteqrasiya/test məqsədlidir və "
                        "mühəndis təsdiqi olmadan əməliyyat qərarı üçün istifadə edilməməlidir.")
    out = {
        **header(prep, bundle),
        "currentProduction": prod.get("currentProduction"),
        "predictedProduction7d": prod.get("predictedProduction7d"),
        "predictedProduction30d": prod.get("predictedProduction30d"),
        "predictedProduction90d": prod.get("predictedProduction90d"),
        "productionChangePct": prod.get("productionChangePct"),
        "predictionIntervals": prod.get("predictionIntervals"),
        "forecastVsActual": prod.get("forecastVsActual", []),
        "anomalyDetected": an.get("anomalyDetected"),
        "anomalyScore": an.get("anomalyScore"),
        "detectedAnomalies": an.get("detectedAnomalies", []),
        "riskLevel": rk.get("riskLevel"),
        "riskScore": rk.get("riskScore"),
        "riskReasons": rk.get("riskReasons", []),
        "equipmentFailureProbability": eq.get("equipmentFailureProbability"),
        "maintenanceRisk": eq.get("maintenanceRisk"),
        "maintenanceRecommended": eq.get("maintenanceRecommended"),
        "failureFactors": eq.get("failureFactors", []),
        "operationalEfficiency": ef.get("operationalEfficiency"),
        "efficiencyDetails": ef.get("efficiencyDetails"),
        "estimatedDowntime": eq.get("estimatedDowntime"),
        "indicators": _indicators(prep.feats),
        "recommendations": recs,
        "dataQuality": prep.quality,
        "confidence": _conf(prep.base_conf, "Məlumat tamlığı x tarixçə uzunluğu (evristik; statistik ehtimal deyil)."),
        "componentStatus": {"production": prod.get("status"), "anomaly": an.get("status"), "risk": rk.get("status"),
                            "equipment": eq.get("status"), "efficiency": ef.get("status")},
        "warnings": warnings,
    }
    return clean(out)
