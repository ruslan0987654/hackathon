"""Anomaliya aşkarlanması: IsolationForest (nəzarətsiz) + quyunun öz tarixçəsinə görə z-score atribusiyası.

Təlim zamanı etiket İSTİFADƏ OLUNMUR. Sintetik etiketlər (injected anomaly) yalnız qiymətləndirmə üçündür.
"""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import Pipeline

from app.preprocessing.features import ANOMALY_FEATURES, EQUIPMENT_SENSOR_FIELDS
from app.utils.stats import robust_center_scale


def _raw_scores(pipe, X):
    return -pipe.score_samples(X)  # böyük = daha anomal


def train_anomaly(df, seed: int = 42, log=print):
    tr, va, te = (df[df.split == s] for s in ("train", "val", "test"))
    Xtr = tr[ANOMALY_FEATURES].to_numpy(float)
    pipe = Pipeline([
        ("impute", SimpleImputer(strategy="median", keep_empty_features=True)),
        ("iforest", IsolationForest(n_estimators=300, max_samples=512, contamination="auto",
                                    random_state=seed, n_jobs=-1)),
    ])
    pipe.fit(Xtr)
    raw_tr = _raw_scores(pipe, Xtr)
    q50, q97, q995 = (float(np.quantile(raw_tr, q)) for q in (0.50, 0.97, 0.995))

    population = {}
    for f in EQUIPMENT_SENSOR_FIELDS:
        vals = tr[f].dropna().to_numpy(float)
        # sıfır dəyərlər (nasos dayanıb) populyasiya normasını pozmasın
        vals = vals[vals > 0]
        med, scale = robust_center_scale(vals, rel_floor=0.03)
        population[f] = {"median": med, "scale": scale}

    metrics = {}
    for name, part in (("val", va), ("test", te)):
        raw = _raw_scores(pipe, part[ANOMALY_FEATURES].to_numpy(float))
        y = part.is_anomaly.to_numpy()
        flag = raw >= q97
        tp = int(((flag == 1) & (y == 1)).sum())
        metrics[name] = {
            "ROC_AUC": float(roc_auc_score(y, raw)),
            "averagePrecision": float(average_precision_score(y, raw)),
            "anomalyBaseRate": float(y.mean()),
            "recallAtThreshold": float(tp / max(1, y.sum())),
            "precisionAtThreshold": float(tp / max(1, flag.sum())),
            "falsePositiveRate": float(((flag == 1) & (y == 0)).sum() / max(1, (y == 0).sum())),
            "n": int(len(y)),
        }
    log(f"  [anomaly] test ROC-AUC={metrics['test']['ROC_AUC']:.3f} "
        f"recall={metrics['test']['recallAtThreshold']:.2f} precision={metrics['test']['precisionAtThreshold']:.2f}")
    artifact = {"features": list(ANOMALY_FEATURES), "pipeline": pipe,
                "rawScoreQ50": q50, "rawScoreThreshold": q97, "rawScoreQ995": q995,
                "population": population}
    return artifact, metrics
