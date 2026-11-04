"""Hasilat proqnozu: hər ufuq (7/30/90 gün) üçün 3 kvantil modeli (q10, q50, q90).

Hədəf: növbəti h gün ərzində ORTA gündəlik hasilatın cari bazaya (7 günlük orta) nisbəti.
Median (q50) nöqtəvi proqnozdur. [q10, q90] intervalı validasiya hissəsində "conformalized quantile
regression" (CQR) ilə genişləndirilir ki, 80% əhatə hədəfinə yaxınlaşsın.
"""
from __future__ import annotations

import math

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from app.preprocessing.features import FEATURE_NAMES
from app.preprocessing.synthetic import HORIZONS

QUANTILES = (0.1, 0.5, 0.9)
TARGET_COVERAGE = 0.8


def _usable(df, split, h):
    m = (df.split == split) & df.base.notna() & (df.base > 1.0) & df[f"y_ratio_{h}"].notna()
    return df[m]


def _ratio_preds(models_h, X):
    preds = np.vstack([np.clip(models_h[q].predict(X), 0, 3) for q in QUANTILES])
    return np.sort(preds, axis=0)  # lo, mid, hi (kvantillərin kəsişməsinə qarşı)


def _metrics(y, p, base):
    return {
        "MAE": float(mean_absolute_error(y, p)),
        "RMSE": float(np.sqrt(mean_squared_error(y, p))),
        "R2": float(r2_score(y, p)),
        "baselineMAE_persistence": float(mean_absolute_error(y, base)),
        "baselineRMSE_persistence": float(np.sqrt(mean_squared_error(y, base))),
        "baselineR2_persistence": float(r2_score(y, base)),
        "n": int(len(y)),
    }


def train_production(df, seed: int = 42, log=print):
    models, pads, metrics = {}, {}, {}
    for h in HORIZONS:
        tr = _usable(df, "train", h)
        X, y = tr[FEATURE_NAMES].to_numpy(float), np.clip(tr[f"y_ratio_{h}"].to_numpy(float), 0, 3)
        models[h] = {}
        for q in QUANTILES:
            m = HistGradientBoostingRegressor(
                loss="quantile", quantile=q, max_iter=250, learning_rate=0.05, max_leaf_nodes=20,
                min_samples_leaf=40, l2_regularization=1.0, random_state=seed)
            models[h][q] = m.fit(X, y)

        # CQR kalibrasiyası (validasiya quyuları/dövrü)
        va = _usable(df, "val", h)
        lo, _, hi = _ratio_preds(models[h], va[FEATURE_NAMES].to_numpy(float))
        yv = np.clip(va[f"y_ratio_{h}"].to_numpy(float), 0, 3)
        scores = np.maximum(lo - yv, yv - hi)
        n = len(scores)
        k = min(n, math.ceil((n + 1) * TARGET_COVERAGE))
        pads[h] = float(np.sort(scores)[k - 1]) if n >= 20 else 0.0

        metrics[f"{h}d"] = {"intervalPadRatio": pads[h]}
        for split in ("train", "val", "test"):
            part = _usable(df, split, h)
            if part.empty:
                continue
            lo, mid, hi = _ratio_preds(models[h], part[FEATURE_NAMES].to_numpy(float))
            lo, hi = np.clip(lo - pads[h], 0, None), hi + pads[h]
            base = part.base.to_numpy(float)
            truth = part[f"y_abs_{h}"].to_numpy(float)
            mt = _metrics(truth, mid * base, base)
            mt["intervalCoverage80"] = float(np.mean((truth >= lo * base) & (truth <= hi * base)))
            mt["meanIntervalWidthRel"] = float(np.mean(hi - lo))
            mt["MAEimprovementVsPersistence"] = float(1 - mt["MAE"] / mt["baselineMAE_persistence"])
            metrics[f"{h}d"][split] = mt
        t = metrics[f"{h}d"]["test"]
        log(f"  [production {h}d] test MAE={t['MAE']:.2f} (persistence {t['baselineMAE_persistence']:.2f}) "
            f"R2={t['R2']:.3f} cov80={t['intervalCoverage80']:.2f}")
    artifact = {"features": list(FEATURE_NAMES), "horizons": list(HORIZONS), "quantiles": list(QUANTILES),
                "models": models, "intervalPad": pads, "intervalLevel": TARGET_COVERAGE}
    return artifact, metrics
