"""Avadanlıq (nasos) nasazlığı ehtimalı və texniki xidmət ehtiyacı."""
from __future__ import annotations

import numpy as np

from app.preprocessing.features import EQUIPMENT_SENSOR_FIELDS, vectorize
from app.services.explain import top_reasons


def _platt(p: float, a: float, b: float) -> float:
    p = min(max(p, 1e-6), 1 - 1e-6)
    return float(1.0 / (1.0 + np.exp(-(a * np.log(p / (1 - p)) + b))))


def run(feats: dict, art: dict) -> dict:
    if not any(np.isfinite(feats.get(f, np.nan)) for f in EQUIPMENT_SENSOR_FIELDS):
        return {"status": "insufficient_sensor_data", "equipmentFailureProbability": None,
                "maintenanceRisk": None, "maintenanceRecommended": None, "estimatedDowntime": None,
                "failureFactors": [],
                "statusMessage": "Vibrasiya, avadanlıq temperaturu və nasos səmərəliliyi üzrə ölçmə yoxdur; "
                                 "nasazlıq ehtimalı hesablanmır."}
    X = vectorize(feats, art["features"])
    raw = float(art["model"].predict_proba(X)[0, 1])
    p = _platt(raw, art["calibration"]["a"], art["calibration"]["b"])
    thr = art["threshold"]
    level = "high" if p >= thr else ("medium" if p >= thr / 2 else "low")
    synthetic = art.get("labelsAreSynthetic", True)
    return {
        "status": "ok",
        "equipmentFailureProbability": round(p, 4),
        "failureHorizonDays": 30,
        "maintenanceRisk": level,
        "maintenanceRecommended": bool(p >= thr),
        "decisionThreshold": round(float(thr), 3),
        "estimatedDowntime": round(p * art["medianFailureDowntimeHours"], 1),
        "estimatedDowntimeUnit": "hours (növbəti 30 gün üçün gözlənilən qiymət = ehtimal x tipik nasazlıq dayanması)",
        "failureFactors": top_reasons(feats, art["explainer"]),
        "baseRateInTraining": round(art["baseRate"], 4),
        "probabilityNote": ("Ehtimal sintetik nasazlıq etiketləri ilə öyrədilmiş və Platt ilə kalibrə edilmişdir; "
                            "real avadanlıq statistikası ilə yenidən təsdiqlənməlidir." if synthetic else
                            "Ehtimal real etiketlərlə öyrədilmişdir."),
    }
