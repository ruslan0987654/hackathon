"""Müstəqil qiymətləndirmə və sızma (data leakage) yoxlamaları.

    python -m training.evaluate

1) Yeni seed ilə TAMAMİLƏ yeni sintetik quyular yaradılır və saxlanmış modellər onların test hissəsində yoxlanılır.
2) Etiket qarışdırma testi: etiketlər təsadüfi qarışdırılıb model öyrədilərsə ROC-AUC ≈ 0.5 olmalıdır
   (əks halda pipeline-da gizli sızma var).
3) Struktur yoxlamaları: bölgülər arasında ən uzun ufuq qədər boşluq, quyuların kəsişməməsi.
"""
from __future__ import annotations

import json

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

from app.core.paths import DEFAULT_MODEL_DIR
from app.models.bundle import load_bundle
from app.preprocessing.features import FEATURE_NAMES
from training.data import build_dataset
from training.train_equipment import apply_platt
from training.train_production import _ratio_preds


def main(model_dir=DEFAULT_MODEL_DIR, n_wells: int = 120, seed: int = 9999) -> dict:
    b = load_bundle(model_dir)
    df, meta = build_dataset(n_wells, b.metadata["dataset"]["nDays"], seed, 4)
    te = df[df.split == "test"]
    report: dict = {"newSeed": seed, "testRows": int(len(te)), "dataBasis": "synthetic"}

    prod = {}
    art = b.production
    for h in art["horizons"]:
        part = te[te.base.notna() & (te.base > 1) & te[f"y_abs_{h}"].notna()]
        _, mid, _ = _ratio_preds(art["models"][h], part[FEATURE_NAMES].to_numpy(float))
        truth, base = part[f"y_abs_{h}"].to_numpy(float), part.base.to_numpy(float)
        mae, mae0 = float(np.mean(np.abs(truth - mid * base))), float(np.mean(np.abs(truth - base)))
        prod[f"{h}d"] = {"MAE": mae, "persistenceMAE": mae0, "improvement": 1 - mae / mae0,
                         "RMSE": float(np.sqrt(np.mean((truth - mid * base) ** 2)))}
    report["production"] = prod

    eq = b.equipment
    p = apply_platt(eq["model"].predict_proba(te[FEATURE_NAMES].to_numpy(float))[:, 1], **eq["calibration"])
    report["equipment_ROC_AUC"] = float(roc_auc_score(te.fail30, p))

    tr = df[df.split == "train"]
    rng = np.random.default_rng(0)
    shuffled = HistGradientBoostingClassifier(max_iter=100, max_leaf_nodes=4, min_samples_leaf=250,
                                              l2_regularization=10.0, random_state=0)
    shuffled.fit(tr[FEATURE_NAMES].to_numpy(float), rng.permutation(tr.fail30.to_numpy()))
    auc_shuf = float(roc_auc_score(te.fail30, shuffled.predict_proba(te[FEATURE_NAMES].to_numpy(float))[:, 1]))
    report["labelShuffleAUC (≈0.5 gözlənilir)"] = auc_shuf
    report["leakageSuspected"] = bool(auc_shuf > 0.58)

    r = meta["splitRanges"]
    report["structure"] = {
        "gapTrainToVal_days": r["val"][0] - r["train"][1], "gapValToTest_days": r["test"][0] - r["val"][1],
        "wellsPerSplit": meta["wellsPerSplit"],
        "noOverlappingTargetWindows": bool(r["val"][0] - r["train"][1] >= 90 and r["test"][0] - r["val"][1] >= 90),
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return report


if __name__ == "__main__":
    main()
