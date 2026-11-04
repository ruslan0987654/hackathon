"""Risk/nasazlıq səbəblərinin çıxarılması: qlobal əhəmiyyət x istiqamət x cari kənarlaşma."""
from __future__ import annotations

import numpy as np

from app.utils.messages import direction_az, label


def top_reasons(feats: dict, explainer: dict, top: int = 5, min_signed_z: float = 1.5) -> list[dict]:
    rows = []
    for f, imp in explainer["importance"].items():
        d = explainer["direction"].get(f, 0.0)
        v, c, s = feats.get(f, np.nan), explainer["center"].get(f, np.nan), explainer["scale"].get(f, np.nan)
        if d == 0 or imp <= 0 or not (np.isfinite(v) and np.isfinite(c) and np.isfinite(s)) or s <= 0:
            continue
        z = (v - c) / s
        signed = z * d  # müsbət = riski artıran istiqamətdə kənarlaşma
        if signed >= min_signed_z:
            rows.append((imp * min(signed, 6.0), f, v, c, z))
    rows.sort(reverse=True)
    out = []
    for contrib, f, v, c, z in rows[:top]:
        out.append({
            "feature": f, "label": label(f), "value": round(float(v), 3),
            "typicalValue": round(float(c), 3), "zScore": round(float(z), 2),
            "importanceWeight": round(float(explainer["importance"][f]), 3),
            "text": f"{label(f)} = {v:.2f} (tipik səviyyə ≈ {c:.2f}); tipik dəyərdən {direction_az(z)}",
        })
    return out
