"""Hasilat proqnozu və "proqnoz vs faktiki" geri-test."""
from __future__ import annotations

from datetime import timedelta

import numpy as np

from app.preprocessing.features import compute_features, static_from_payload, vectorize
from app.utils.stats import NAN

HORIZONS = (7, 30, 90)


def baseline_production(feats: dict) -> float:
    b = feats.get("production_7d_avg", NAN)
    if not np.isfinite(b):
        b = feats.get("production", NAN)
    return float(b) if np.isfinite(b) else NAN


def predict_horizons(feats: dict, art: dict) -> dict | None:
    """{h: {"lower","median","upper"}} (mütləq vahidlərlə, orta gündəlik hasilat) və ya None (baza yoxdur)."""
    base = baseline_production(feats)
    if not np.isfinite(base) or base <= 0:
        return None
    X = vectorize(feats, art["features"])
    out = {}
    for h in art["horizons"]:
        ms = art["models"][h]
        q = np.sort([float(np.clip(ms[qq].predict(X)[0], 0, 3)) for qq in art["quantiles"]])
        pad = art["intervalPad"][h]
        out[h] = {"lower": float(max(0.0, q[0] - pad) * base), "median": float(q[1] * base),
                  "upper": float((q[2] + pad) * base)}
    return out


def run(feats: dict, art: dict, ts, cols, payload, first_dt, last_dt, quality: dict) -> dict:
    preds = predict_horizons(feats, art)
    cur = feats.get("production", NAN)
    base = baseline_production(feats)
    res = {
        "currentProduction": float(cur) if np.isfinite(cur) else None,
        "baselineProduction7dAvg": float(base) if np.isfinite(base) else None,
        "status": "ok" if preds else "insufficient_data",
    }
    if not preds:
        res.update({f"predictedProduction{h}d": None for h in HORIZONS})
        res.update({"productionChangePct": None, "predictionIntervals": None, "forecastVsActual": [],
                    "statusMessage": "Proqnoz üçün son günlərdə müsbət hasilat ölçməsi tələb olunur."})
        return res
    for h in HORIZONS:
        res[f"predictedProduction{h}d"] = round(preds[h]["median"], 3)
    res["predictionIntervals"] = {
        f"{h}d": {"lower": round(preds[h]["lower"], 3), "upper": round(preds[h]["upper"], 3),
                  "level": art["intervalLevel"]} for h in HORIZONS}
    res["productionChangePct"] = round((preds[30]["median"] - base) / base * 100.0, 2)
    res["forecastDefinition"] = ("predictedProductionNd = növbəti N gün ərzində gözlənilən ORTA gündəlik hasilat; "
                                 "productionChangePct = 30 günlük proqnozun cari 7 günlük orta ilə müqayisəsi (%).")
    res["forecastVsActual"] = backtest(ts, cols, payload, first_dt, last_dt, art)
    return res


def backtest(ts, cols, payload, first_dt, last_dt, art, horizons=(7, 30)) -> list[dict]:
    """Keçmişdəki (t-h) anda verilə biləcək proqnozu həmin müddətdə baş vermiş FAKTİKİ hasilatla müqayisə edir."""
    out = []
    t_end = float(ts[-1])
    for h in horizons:
        t_cut = t_end - h
        idx = ts <= t_cut
        if idx.sum() < 10 or (ts[idx][-1] - ts[idx][0]) < 14 or ts[idx][-1] < t_cut - 3:
            continue
        cut_dt = first_dt + timedelta(days=float(ts[idx][-1]))
        f = compute_features(ts[idx], {k: v[idx] for k, v in cols.items()},
                             static_from_payload(payload, cut_dt))
        preds = predict_horizons(f, art)
        if not preds:
            continue
        seg = cols["production"][(ts > ts[idx][-1]) & (ts <= t_end)]
        seg = seg[np.isfinite(seg)]
        if seg.size < max(3, int(0.4 * h)):
            continue
        actual, pred = float(seg.mean()), preds[h]["median"]
        out.append({
            "horizonDays": h, "forecastMadeAt": cut_dt.isoformat(), "windowEnd": last_dt.isoformat(),
            "predictedAvgDailyProduction": round(pred, 3), "actualAvgDailyProduction": round(actual, 3),
            "errorPct": round((pred - actual) / actual * 100.0, 2) if actual > 0 else None,
            "withinInterval": bool(preds[h]["lower"] <= actual <= preds[h]["upper"]),
        })
    return out
