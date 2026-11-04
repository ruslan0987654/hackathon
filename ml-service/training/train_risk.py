"""Əməliyyat riski: low / medium / high (3 sinifli HistGradientBoostingClassifier).

DİQQƏT: etiketlər SİNTETİKDİR (gizli dəyişənlərin persentil kəsiklərindən). Ona görə çıxış
"riskScore" (nisbi model balı) kimi təqdim olunur, kalibrə edilmiş ehtimal kimi YOX.
"""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score, roc_auc_score

from app.preprocessing.features import FEATURE_NAMES
from training.explain import fit_explainer

CLASSES = ["low", "medium", "high"]


def _eval(model, part):
    X, y = part[FEATURE_NAMES].to_numpy(float), part.risk_label.to_numpy()
    pred, proba = model.predict(X), model.predict_proba(X)
    return {
        "accuracy": float(accuracy_score(y, pred)),
        "balancedAccuracy": float(balanced_accuracy_score(y, pred)),
        "macroF1": float(f1_score(y, pred, average="macro")),
        "ROC_AUC_ovr_macro": float(roc_auc_score(y, proba, multi_class="ovr", average="macro")),
        "meanAbsoluteClassError": float(np.mean(np.abs(pred - y))),
        "confusionMatrix(rows=true, cols=pred; low,medium,high)": confusion_matrix(y, pred, labels=[0, 1, 2]).tolist(),
        "n": int(len(y)),
    }


def train_risk(df, seed: int = 42, log=print):
    tr, va, te = (df[df.split == s] for s in ("train", "val", "test"))
    model = HistGradientBoostingClassifier(max_iter=120, learning_rate=0.05, max_leaf_nodes=6,
                                           min_samples_leaf=200, l2_regularization=10.0,
                                           random_state=seed)
    model.fit(tr[FEATURE_NAMES].to_numpy(float), tr.risk_label.to_numpy())
    metrics = {s: _eval(model, p) for s, p in (("train", tr), ("val", va), ("test", te))}
    explainer = fit_explainer(model, tr, va, FEATURE_NAMES, "risk_latent", "f1_macro", seed, score_col="risk_label")
    log(f"  [risk] test macroF1={metrics['test']['macroF1']:.3f} acc={metrics['test']['accuracy']:.3f} "
        f"(train macroF1={metrics['train']['macroF1']:.3f})")
    artifact = {"features": list(FEATURE_NAMES), "model": model, "classes": CLASSES, "explainer": explainer,
                "labelsAreSynthetic": True}
    return artifact, metrics
