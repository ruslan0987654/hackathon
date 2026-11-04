"""Təlim cədvəlinin qurulması (sintetik quyulardan).

Bölgü (sızmanın qarşısını almaq üçün həm QUYU, həm də ZAMAN üzrə ayrılır):
  train : təlim quyuları, gün [14 .. 0.40*D]
  val   : validasiya quyuları (təlimdə YOX), train_end+90 .. +0.09*D   (90 gün boşluq = ən uzun proqnoz ufqu)
  test  : test quyuları (təlimdə YOX), val_end+90 .. D-91
Hədəf pəncərələri (t, t+90] heç vaxt növbəti bölgünün feature pəncərəsi ilə kəsişmir.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from app.preprocessing.features import FEATURE_NAMES, compute_features
from app.preprocessing.synthetic import HORIZONS, simulate_wells
from app.utils.stats import NAN

MIN_DAY = 14
MAX_HORIZON = max(HORIZONS)


def split_ranges(n_days: int) -> dict[str, tuple[int, int]]:
    if n_days < 500:
        raise ValueError("n_days ən azı 500 olmalıdır (zaman bölgüsü üçün)")
    train_end = int(0.40 * n_days)
    val_start = train_end + MAX_HORIZON
    val_end = val_start + int(0.09 * n_days)
    test_start = val_end + MAX_HORIZON
    test_end = n_days - MAX_HORIZON - 1
    return {"train": (MIN_DAY, train_end), "val": (val_start, val_end), "test": (test_start, test_end)}


def build_dataset(n_wells: int = 280, n_days: int = 1000, seed: int = 42, step: int = 4):
    wells = simulate_wells(n_wells, n_days, seed)
    rng = np.random.default_rng(seed + 1)
    ranges = split_ranges(n_days)

    ids = rng.permutation(n_wells)
    n_val, n_test = max(1, int(0.15 * n_wells)), max(1, int(0.18 * n_wells))
    well_split = {}
    for j, i in enumerate(ids):
        well_split[int(i)] = "test" if j < n_test else ("val" if j < n_test + n_val else "train")

    rows = []
    for wi, w in enumerate(wells):
        split = well_split[wi]
        lo, hi = ranges[split]
        pidx = np.flatnonzero(w["present"])
        start = lo + int(rng.integers(0, step))
        for day in range(start, hi + 1, step):
            if not w["present"][day]:
                continue
            sl = pidx[: np.searchsorted(pidx, day, side="right")]
            ts = sl.astype(float)
            cols = {k: v[sl] for k, v in w["cols"].items()}
            static = {
                "depth": w["static_info"]["depth"],
                "well_age_days": w["static_info"]["age0"] + day,
                "well_type_code": {"oil": 0.0, "gas": 1.0, "oil_gas": 2.0}[w["static_info"]["wellType"]],
                "production_target": float(w["plan"][day]),
                "days_since_maintenance": float(w["since_maint"][day]),
                "days_since_inspection": float(w["since_insp"][day]),
            }
            f = compute_features(ts, cols, static)
            base = f["production_7d_avg"] if np.isfinite(f["production_7d_avg"]) else f["production"]
            row = {"wellId": w["wellId"], "day": day, "split": split, **f, "base": base}
            for hz in HORIZONS:
                y = float(w["y_abs"][hz][day])
                row[f"y_abs_{hz}"] = y
                row[f"y_ratio_{hz}"] = y / base if np.isfinite(base) and base > 1.0 else NAN
            row["fail30"] = int(w["fail30"][day])
            row["risk_latent"] = float(w["risk_latent"][day])
            row["is_anomaly"] = int(w["anomaly"][day] > 0)
            rows.append(row)

    df = pd.DataFrame(rows)
    # risk etiketləri: təlim hissəsinin persentilləri ilə (60% aşağı, 28% orta, 12% yüksək)
    tr = df.loc[df.split == "train", "risk_latent"]
    q60, q88 = float(tr.quantile(0.60)), float(tr.quantile(0.88))
    df["risk_label"] = np.where(df.risk_latent >= q88, 2, np.where(df.risk_latent >= q60, 1, 0))
    all_fail_hours = [x for w in wells for x in w["failure_downtime"]]
    meta = {
        "nWells": n_wells, "nDays": n_days, "seed": seed, "sampleStepDays": step,
        "splitRanges": ranges, "rows": {s: int((df.split == s).sum()) for s in ("train", "val", "test")},
        "wellsPerSplit": {s: sum(1 for v in well_split.values() if v == s) for s in ("train", "val", "test")},
        "riskLabelThresholds": {"mediumFrom": q60, "highFrom": q88},
        "failureEvents": len(all_fail_hours),
        "medianFailureDowntimeHours": float(np.median(all_fail_hours)) if all_fail_hours else 48.0,
        "failure30dBaseRate": float(df.loc[df.split == "train", "fail30"].mean()),
        "anomalyRate": float(df.loc[df.split == "train", "is_anomaly"].mean()),
        "isSynthetic": True,
    }
    return df, meta
