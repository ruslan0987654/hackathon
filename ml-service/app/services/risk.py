"""Əməliyyat riski: low / medium / high."""
from __future__ import annotations

import numpy as np

from app.preprocessing.features import vectorize
from app.services.explain import top_reasons


def run(feats: dict, art: dict) -> dict:
    X = vectorize(feats, art["features"])
    if int(np.isfinite(X).sum()) < 5:
        return {"status": "insufficient_data", "riskLevel": None, "riskScore": None, "riskReasons": [],
                "statusMessage": "Risk qiymətləndirməsi üçün kifayət qədər göstərici yoxdur."}
    proba = art["model"].predict_proba(X)[0]
    classes = list(art["model"].classes_)
    p = {art["classes"][int(c)]: float(proba[i]) for i, c in enumerate(classes)}
    score = 0.5 * p.get("medium", 0.0) + 1.0 * p.get("high", 0.0)
    level = max(p, key=p.get)
    res = {
        "status": "ok", "riskLevel": level, "riskScore": round(score, 4),
        "riskReasons": top_reasons(feats, art["explainer"]),
        "scoreNote": ("riskScore 0..1 nisbi model balıdır (0.5*P(medium)+P(high)). Etiketlər sintetik olduğundan "
                      "bu, kalibrə olunmuş ehtimal DEYİL." if art.get("labelsAreSynthetic", True) else
                      "riskScore 0..1 model balıdır."),
    }
    if not art.get("labelsAreSynthetic", True):  # yalnız real etiketlənmiş data ilə öyrədilibsə ehtimal göstərilir
        res["classProbabilities"] = {k: round(v, 4) for k, v in p.items()}
    return res
