"""Feature mühəndisliyi.

Eyni funksiya həm təlim zamanı (sintetik data), həm də API-də (real sorğu) istifadə olunur.
Bu, training/serving fərqini (skew) aradan qaldırır.

Əsas qayda: `ts` massivinin SON elementi "indiki an"dır. Yalnız bu andan əvvəlki məlumatlar
istifadə olunur (gələcək məlumat sızması yoxdur). Çatışmayan dəyərlər NaN olaraq qalır,
uydurulmur; modellər NaN-ı özləri idarə edir.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

import numpy as np

from app.utils.stats import NAN, finite, latest, slope, window

SERIES_FIELDS = [
    "production", "oilProduction", "gasProduction", "waterProduction",
    "pressure", "temperature", "bottomHolePressure", "wellheadPressure",
    "casingPressure", "tubingPressure", "waterCut", "gasOilRatio", "flowRate",
    "vibration", "equipmentTemperature", "pumpEfficiency", "pumpRuntime",
    "operatingHours", "downtimeHours",
]
# pumpStatus mətn sahəsidir; rəqəmli "pumpFault" (1=nasazlıq, 0=normal/dayanıb, NaN=məlum deyil) kimi saxlanılır.
ALL_COLUMNS = SERIES_FIELDS + ["pumpFault"]

LEVEL_FIELDS = [
    "production", "pressure", "temperature", "bottomHolePressure", "wellheadPressure",
    "casingPressure", "tubingPressure", "waterCut", "gasOilRatio", "flowRate",
    "vibration", "equipmentTemperature", "pumpEfficiency", "pumpRuntime",
]
ZSELF_FIELDS = [
    "production", "pressure", "temperature", "bottomHolePressure", "wellheadPressure",
    "vibration", "equipmentTemperature", "pumpEfficiency", "waterCut",
]
# z-score hesablanarkən minimum mütləq miqyas (sensor səs-küyündən kiçik dəyişikliklər "anomaliya" olmasın)
ABS_FLOOR = {"waterCut": 1.0, "pumpEfficiency": 1.0, "vibration": 0.15,
             "equipmentTemperature": 1.0, "temperature": 0.5}

STATIC_FEATURES = ["depth", "well_age_days", "well_type_code", "production_target",
                   "days_since_maintenance", "days_since_inspection"]
PROD_FEATURES = ["production_7d_avg", "production_30d_avg", "production_90d_avg",
                 "production_7d_change_pct", "production_30d_change_pct",
                 "production_decline_rate", "production_volatility_30d", "target_attainment_30d"]
TREND_FEATURES = ["pressure_change_rate", "waterCut_trend", "gasOilRatio_slope30",
                  "vibration_slope30", "equipmentTemperature_slope30", "pumpEfficiency_slope30"]
OPS_FEATURES = ["downtime_7d_hours", "downtime_30d_hours", "pump_fault_frac_7d", "pump_fault_frac_30d"]
ZSELF_FEATURES = [f"zself_{f}" for f in ZSELF_FIELDS]

FEATURE_NAMES = (STATIC_FEATURES + LEVEL_FIELDS + PROD_FEATURES + TREND_FEATURES
                 + OPS_FEATURES + ZSELF_FEATURES)

ANOMALY_FEATURES = (["pressure", "temperature", "vibration", "equipmentTemperature",
                     "pumpEfficiency", "waterCut"] + ZSELF_FEATURES
                    + ["production_7d_change_pct", "production_volatility_30d"])

# Həftə/ay proqnozu üçün "əsas" göstəricilər (data keyfiyyəti qiymətləndirməsində)
CORE_FIELDS = ["production", "pressure", "temperature", "waterCut", "bottomHolePressure",
               "wellheadPressure", "vibration", "equipmentTemperature", "pumpEfficiency",
               "downtimeHours"]
EQUIPMENT_SENSOR_FIELDS = ["vibration", "equipmentTemperature", "pumpEfficiency"]

WELL_TYPE_CODES = {"oil": 0.0, "gas": 1.0, "oil_gas": 2.0, "gas_condensate": 3.0}
_FAULT_WORDS = {"fault", "failed", "failure", "error", "alarm", "trip"}
_OK_WORDS = {"running", "on", "active", "stopped", "off", "idle", "standby"}


def well_type_code(value: Any) -> float:
    if not value:
        return NAN
    key = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    return WELL_TYPE_CODES.get(key, NAN)


def self_deviation(ts: np.ndarray, a: np.ndarray, t0: float, field: str, min_prior: int = 8):
    """Son qiymətin quyunun ÖZ əvvəlki 30 günlük tarixçəsindən kənarlaşması.

    Qaytarır: (cari, median, miqyas, z). Kifayət qədər tarixçə yoxdursa z = NaN.
    """
    cur = latest(ts, a, t0)
    prior = window(ts, a, t0, 1.0, 31.0)
    if not np.isfinite(cur) or prior.size < min_prior:
        return cur, NAN, NAN, NAN
    med = float(np.median(prior))
    mad = float(np.median(np.abs(prior - med)))
    scale = max(1.4826 * mad, 0.03 * abs(med), ABS_FLOOR.get(field, 1e-6))
    return cur, med, scale, float((cur - med) / scale)


def _pct_change(a: np.ndarray, b: np.ndarray, min_pts: int) -> float:
    if a.size >= min_pts and b.size >= min_pts and b.mean() > 0:
        return float((a.mean() - b.mean()) / b.mean() * 100.0)
    return NAN


def compute_features(ts: np.ndarray, cols: dict[str, np.ndarray], static: dict[str, float]) -> dict[str, float]:
    """`ts` (gün, artan) və `cols` əsasında bütün feature-ləri hesablayır."""
    with np.errstate(all="ignore"):
        t0 = float(ts[-1])
        f: dict[str, float] = {}
        for k in STATIC_FEATURES:
            v = static.get(k, NAN)
            f[k] = float(v) if v is not None else NAN
        for k in LEVEL_FIELDS:
            f[k] = latest(ts, cols[k], t0)

        prod = cols["production"]
        w7, w7p = window(ts, prod, t0, 0, 7), window(ts, prod, t0, 7, 14)
        w30, w30p = window(ts, prod, t0, 0, 30), window(ts, prod, t0, 30, 60)
        w90 = window(ts, prod, t0, 0, 90)
        f["production_7d_avg"] = float(w7.mean()) if w7.size >= 1 else NAN
        f["production_30d_avg"] = float(w30.mean()) if w30.size >= 3 else NAN
        f["production_90d_avg"] = float(w90.mean()) if w90.size >= 10 else NAN
        f["production_7d_change_pct"] = _pct_change(w7, w7p, 1)
        f["production_30d_change_pct"] = _pct_change(w30, w30p, 10)

        logp = np.where(prod > 0, np.log(np.where(prod > 0, prod, 1.0)), np.nan)
        s = slope(ts, logp, t0, 90, min_pts=10)
        f["production_decline_rate"] = float(-100.0 * s) if np.isfinite(s) else NAN  # %/gün, müsbət = azalma
        f["production_volatility_30d"] = (float(w30.std() / w30.mean())
                                          if w30.size >= 8 and w30.mean() > 0 else NAN)
        tgt = f["production_target"]
        f["target_attainment_30d"] = (f["production_30d_avg"] / tgt
                                      if np.isfinite(tgt) and tgt > 0 and np.isfinite(f["production_30d_avg"]) else NAN)

        p30 = window(ts, cols["pressure"], t0, 0, 30)
        sp = slope(ts, cols["pressure"], t0, 30)
        f["pressure_change_rate"] = (float(sp / p30.mean() * 100.0)
                                     if np.isfinite(sp) and p30.size and p30.mean() > 0 else NAN)  # %/gün
        f["waterCut_trend"] = slope(ts, cols["waterCut"], t0, 30)  # faiz bəndi/gün
        g30 = window(ts, cols["gasOilRatio"], t0, 0, 30)
        sg = slope(ts, cols["gasOilRatio"], t0, 30)
        f["gasOilRatio_slope30"] = (float(sg / g30.mean() * 100.0)
                                    if np.isfinite(sg) and g30.size and g30.mean() > 0 else NAN)
        f["vibration_slope30"] = slope(ts, cols["vibration"], t0, 30)
        f["equipmentTemperature_slope30"] = slope(ts, cols["equipmentTemperature"], t0, 30)
        f["pumpEfficiency_slope30"] = slope(ts, cols["pumpEfficiency"], t0, 30)

        dt = cols["downtimeHours"]
        d7, d30 = window(ts, dt, t0, 0, 7), window(ts, dt, t0, 0, 30)
        f["downtime_7d_hours"] = float(d7.mean() * 7) if d7.size >= 3 else NAN
        f["downtime_30d_hours"] = float(d30.mean() * 30) if d30.size >= 8 else NAN
        pf = cols["pumpFault"]
        pf7, pf30 = window(ts, pf, t0, 0, 7), window(ts, pf, t0, 0, 30)
        f["pump_fault_frac_7d"] = float(pf7.mean()) if pf7.size >= 1 else NAN
        f["pump_fault_frac_30d"] = float(pf30.mean()) if pf30.size >= 3 else NAN

        for fld in ZSELF_FIELDS:
            f[f"zself_{fld}"] = self_deviation(ts, cols[fld], t0, fld)[3]
    return f


def vectorize(feats: dict[str, float], names: list[str]) -> np.ndarray:
    return np.array([[feats.get(n, NAN) for n in names]], dtype=float)


# --------------------------------------------------------------------------------------
# API sorğusu -> massivlər
# --------------------------------------------------------------------------------------
def _naive_utc(dt: datetime) -> datetime:
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _fault_value(status: Any) -> float:
    if status is None:
        return NAN
    s = str(status).strip().lower()
    if s in _FAULT_WORDS:
        return 1.0
    if s in _OK_WORDS:
        return 0.0
    return NAN


def build_series(payload: dict[str, Any]):
    """payload['history'] -> (ts_gün, cols, first_dt, last_dt, n_records). Tarixə görə sıralanır, təkrarlar atılır."""
    rows = payload.get("history") or []
    if not rows:
        raise ValueError("history boşdur")
    by_ts: dict[datetime, dict] = {}
    for r in rows:
        by_ts[_naive_utc(r["timestamp"])] = r  # eyni vaxt təkrarlanarsa sonuncu qalır
    stamps = sorted(by_ts)
    first_dt, last_dt = stamps[0], stamps[-1]
    ts = np.array([(s - first_dt).total_seconds() / 86400.0 for s in stamps], dtype=float)
    cols: dict[str, np.ndarray] = {}
    for k in SERIES_FIELDS:
        cols[k] = np.array([NAN if by_ts[s].get(k) is None else float(by_ts[s][k]) for s in stamps], dtype=float)
    cols["pumpFault"] = np.array([_fault_value(by_ts[s].get("pumpStatus")) for s in stamps], dtype=float)
    return ts, cols, first_dt, last_dt, len(stamps)


def _days_between(later: datetime, earlier: Any) -> float:
    if earlier is None:
        return NAN
    if isinstance(earlier, datetime):
        earlier = _naive_utc(earlier).date()
    elif isinstance(earlier, str):
        earlier = date.fromisoformat(earlier[:10])
    d = (later.date() - earlier).days
    return float(d) if d >= 0 else NAN


def static_from_payload(payload: dict[str, Any], as_of: datetime) -> dict[str, float]:
    start = payload.get("operationStartDate") or payload.get("drillingDate")
    depth = payload.get("depth")
    target = payload.get("productionTarget")
    return {
        "depth": float(depth) if depth is not None else NAN,
        "well_age_days": _days_between(as_of, start),
        "well_type_code": well_type_code(payload.get("wellType")),
        "production_target": float(target) if target is not None else NAN,
        "days_since_maintenance": _days_between(as_of, payload.get("maintenanceDate")),
        "days_since_inspection": _days_between(as_of, payload.get("lastInspectionDate")),
    }


def apply_provided_aggregates(feats: dict[str, float], payload: dict[str, Any]) -> list[str]:
    """Tarixçədən hesablana bilməyən göstəricilər üçün istifadəçinin göndərdiyi hazır dəyərlər (ehtiyat variant)."""
    mapping = {
        "production7dAvg": "production_7d_avg",
        "production30dAvg": "production_30d_avg",
        "production90dAvg": "production_90d_avg",
        "production7dChangePct": "production_7d_change_pct",
        "production30dChangePct": "production_30d_change_pct",
    }
    used = []
    for src, dst in mapping.items():
        v = payload.get(src)
        if v is not None and not np.isfinite(feats.get(dst, NAN)):
            feats[dst] = float(v)
            used.append(src)
    return used
