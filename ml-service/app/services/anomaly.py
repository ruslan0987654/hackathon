"""Anomaliya aşkarlanması: IsolationForest balı + parametr səviyyəsində statistik atribusiya."""
from __future__ import annotations

import numpy as np

from app.preprocessing.features import ZSELF_FIELDS, self_deviation, vectorize
from app.utils.messages import label
from app.utils.stats import NAN

Z_LIST = 4.0      # siyahıya düşmə həddi (|z|)
Z_HIGH = 6.0      # yüksək ciddiyyət
Z_POP = 5.0       # populyasiya normasından kənarlaşma həddi


def run(feats: dict, art: dict, ts, cols) -> dict:
    X = vectorize(feats, art["features"])
    n_finite = int(np.isfinite(X).sum())
    if n_finite < 3:
        return {"status": "insufficient_data", "anomalyDetected": None, "anomalyScore": None,
                "detectedAnomalies": [], "statusMessage": "Anomaliya təhlili üçün kifayət qədər ölçmə yoxdur."}
    raw = float(-art["pipeline"].score_samples(X)[0])
    q50, q995, thr = art["rawScoreQ50"], art["rawScoreQ995"], art["rawScoreThreshold"]
    score = float(np.clip((raw - q50) / max(q995 - q50, 1e-9), 0.0, 1.0))
    model_flag = raw >= thr

    t0 = float(ts[-1])
    items = []
    for fld in ZSELF_FIELDS:
        cur, med, scale, z = self_deviation(ts, cols[fld], t0, fld)
        if np.isfinite(z) and abs(z) >= Z_LIST:
            items.append({"parameter": fld, "label": label(fld), "value": round(cur, 3),
                          "expectedValue": round(med, 3), "zScore": round(z, 2),
                          "direction": "high" if z > 0 else "low", "basis": "well_history",
                          "severity": "high" if abs(z) >= Z_HIGH else "medium"})
    listed = {i["parameter"] for i in items}
    for fld, st in art["population"].items():
        cur = feats.get(fld, NAN)
        if fld in listed or not np.isfinite(cur) or cur <= 0:
            continue
        z = (cur - st["median"]) / st["scale"]
        if abs(z) >= Z_POP:
            items.append({"parameter": fld, "label": label(fld), "value": round(cur, 3),
                          "expectedValue": round(st["median"], 3), "zScore": round(z, 2),
                          "direction": "high" if z > 0 else "low", "basis": "population",
                          "severity": "high" if abs(z) >= 2 * Z_POP else "medium"})
    items.sort(key=lambda i: -abs(i["zScore"]))
    strong = any(i["severity"] == "high" and i["basis"] == "well_history" for i in items)
    return {
        "status": "ok", "anomalyDetected": bool(model_flag or strong), "anomalyScore": round(score, 4),
        "detectedBy": {"isolationForest": bool(model_flag), "strongStatisticalDeviation": bool(strong)},
        "detectedAnomalies": items[:6],
        "scoreNote": "anomalyScore 0..1 aralığına normallaşdırılmış nisbi baldır (1 = təlim paylanmasının ən kənar 0.5%-i).",
    }
