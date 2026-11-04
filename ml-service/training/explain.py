"""Sadə və şəffaf izah mexanizmi: qlobal əhəmiyyət (permutation importance) x istiqamət (Spearman) x
quyunun cari kənarlaşması (robust z). Risk və nasazlıq səbəblərini göstərmək üçün istifadə olunur."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance


def fit_explainer(model, train_df, val_df, features, target_col, scoring, seed=42, score_col=None):
    """target_col: istiqamət (Spearman) üçün; score_col: permutation importance-ın həqiqi etiketi."""
    score_col = score_col or target_col
    X_tr = train_df[features]
    center, scale, direction = {}, {}, {}
    ranks = X_tr.rank()
    tgt_rank = train_df[target_col].rank()
    for f in features:
        v = X_tr[f].dropna().to_numpy(float)
        if v.size < 20:
            center[f], scale[f], direction[f] = float("nan"), float("nan"), 0.0
            continue
        center[f] = float(np.median(v))
        s = float((np.quantile(v, 0.84) - np.quantile(v, 0.16)) / 2)
        scale[f] = s if s > 1e-9 else max(float(v.std()), 1e-6)
        c = ranks[f].corr(tgt_rank)  # Spearman = rank-lar üzrə Pearson
        direction[f] = float(np.sign(c)) if pd.notna(c) and abs(c) > 0.03 else 0.0
    imp = permutation_importance(model, val_df[features].to_numpy(float), val_df[score_col].to_numpy(),
                                 scoring=scoring, n_repeats=3, random_state=seed, n_jobs=-1)
    importance = {f: float(max(0.0, m)) for f, m in zip(features, imp.importances_mean)}
    total = sum(importance.values()) or 1.0
    importance = {f: v / total for f, v in importance.items()}
    return {"center": center, "scale": scale, "direction": direction, "importance": importance}
