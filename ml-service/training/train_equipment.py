"""Avadanlıq (nasos) nasazlığı: növbəti 30 gündə nasazlıq ehtimalı (ikili HistGradientBoostingClassifier).

- Güclü regulyarizasiya (dayaz ağaclar, böyük min_samples_leaf): eyni quyudan gələn ardıcıl nümunələr
  çox oxşardır və model onları əzbərləməyə meyllidir.
- Ehtimallar validasiya hissəsində Platt miqyaslaması ilə kalibrə edilir.
- Eşik (maintenance tövsiyəsi) kalibrə olunmuş validasiya ehtimalları üzərində F1-i maksimallaşdıran dəyərdir.
- Nasazlıq/təmir tarixçəsi (days_since_maintenance, pump_fault_frac_*) feature kimi istifadə olunur.
"""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, brier_score_loss, f1_score, precision_score,
                             recall_score, roc_auc_score)

from app.preprocessing.features import FEATURE_NAMES
from training.explain import fit_explainer


def _logit(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def apply_platt(p, a, b):
    return 1.0 / (1.0 + np.exp(-(a * _logit(p) + b)))


def _calibration(y, p, bins=5):
    edges = np.quantile(p, np.linspace(0, 1, bins + 1))
    edges[-1] += 1e-9
    out = []
    for i in range(bins):
        m = (p >= edges[i]) & (p < edges[i + 1])
        if m.sum():
            out.append({"meanPredicted": float(p[m].mean()), "observedRate": float(y[m].mean()), "n": int(m.sum())})
    return out


def _eval(proba, y, thr):
    flag = proba >= thr
    return {
        "ROC_AUC": float(roc_auc_score(y, proba)),
        "averagePrecision": float(average_precision_score(y, proba)),
        "baseRate": float(y.mean()),
        "brierScore": float(brier_score_loss(y, proba)),
        "threshold": float(thr),
        "precisionAtThreshold": float(precision_score(y, flag, zero_division=0)),
        "recallAtThreshold": float(recall_score(y, flag, zero_division=0)),
        "f1AtThreshold": float(f1_score(y, flag, zero_division=0)),
        "calibrationBins": _calibration(y, proba),
        "n": int(len(y)),
    }


def train_equipment(df, median_downtime_hours: float, seed: int = 42, log=print):
    tr, va, te = (df[df.split == s] for s in ("train", "val", "test"))
    model = HistGradientBoostingClassifier(max_iter=100, learning_rate=0.05, max_leaf_nodes=4,
                                           min_samples_leaf=250, l2_regularization=10.0, random_state=seed)
    model.fit(tr[FEATURE_NAMES].to_numpy(float), tr.fail30.to_numpy())

    def raw(part):
        return model.predict_proba(part[FEATURE_NAMES].to_numpy(float))[:, 1]

    yv = va.fail30.to_numpy()
    a, b = 1.0, 0.0
    if yv.sum() >= 10 and (len(yv) - yv.sum()) >= 10:
        lr = LogisticRegression(C=1e6, max_iter=1000).fit(_logit(raw(va)).reshape(-1, 1), yv)
        a, b = float(lr.coef_[0][0]), float(lr.intercept_[0])
    pv = apply_platt(raw(va), a, b)
    grid = np.linspace(0.02, 0.6, 59)
    thr = float(grid[int(np.argmax([f1_score(yv, pv >= g, zero_division=0) for g in grid]))])
    metrics = {s: _eval(apply_platt(raw(p), a, b), p.fail30.to_numpy(), thr)
               for s, p in (("train", tr), ("val", va), ("test", te))}
    explainer = fit_explainer(model, tr, va, FEATURE_NAMES, "fail30", "roc_auc", seed)
    log(f"  [equipment] test ROC-AUC={metrics['test']['ROC_AUC']:.3f} AP={metrics['test']['averagePrecision']:.3f} "
        f"brier={metrics['test']['brierScore']:.3f} thr={thr:.2f} (train AUC={metrics['train']['ROC_AUC']:.3f})")
    artifact = {"features": list(FEATURE_NAMES), "model": model, "calibration": {"a": a, "b": b},
                "threshold": thr, "medianFailureDowntimeHours": float(median_downtime_hours),
                "baseRate": float(tr.fail30.mean()), "explainer": explainer, "labelsAreSynthetic": True}
    return artifact, metrics
