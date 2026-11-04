"""Bütün modelləri öyrədir və artefaktları saxlayır.

İstifadə (layihə qovluğundan):
    python -m training.train_all
    python -m training.train_all --n-wells 120 --n-days 800
"""
from __future__ import annotations

import argparse
import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import sklearn

from app.core.paths import DEFAULT_DATASET_DIR, DEFAULT_MODEL_DIR
from training.data import build_dataset
from training.train_anomaly import train_anomaly
from training.train_equipment import train_equipment
from training.train_production import train_production
from training.train_risk import train_risk

MODEL_SERIES = "1.0.0"
SYNTHETIC_WARNING = (
    "Modellər SİNTETİK məlumat üzərində öyrədilib (real SOCAR məlumatı deyil). Metrikalar yalnız "
    "sintetik test hissəsinə aiddir və real istehsalatda dəqiqliyə zəmanət DEYİL."
)


def run_training(out_dir: Path | str = DEFAULT_MODEL_DIR, n_wells: int = 280, n_days: int = 1000,
                 seed: int = 42, step: int = 4, save_dataset: bool = True,
                 dataset_dir: Path | str = DEFAULT_DATASET_DIR, log=print) -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    log(f"Sintetik məlumat yaradılır: {n_wells} quyu x {n_days} gün ...")
    df, dmeta = build_dataset(n_wells, n_days, seed, step)
    log(f"  cədvəl: {df.shape[0]} sətir ({dmeta['rows']}), nasazlıq hadisələri: {dmeta['failureEvents']}")
    if save_dataset:
        ddir = Path(dataset_dir)
        ddir.mkdir(parents=True, exist_ok=True)
        df.to_csv(ddir / "synthetic_training_samples.csv.gz", index=False)

    log("Modellər öyrədilir ...")
    prod_art, prod_m = train_production(df, seed, log)
    anom_art, anom_m = train_anomaly(df, seed, log)
    risk_art, risk_m = train_risk(df, seed, log)
    eq_art, eq_m = train_equipment(df, dmeta["medianFailureDowntimeHours"], seed, log)

    trained_at = datetime.now(timezone.utc)
    version = f"{MODEL_SERIES}-synthetic-{trained_at:%Y%m%d}"
    for name, art in (("production", prod_art), ("anomaly", anom_art), ("risk", risk_art), ("equipment", eq_art)):
        joblib.dump(art, out / f"{name}.joblib", compress=3)
    metadata = {
        "modelVersion": version,
        "trainedAt": trained_at.isoformat(),
        "dataBasis": "synthetic",
        "warning": SYNTHETIC_WARNING,
        "dataset": dmeta,
        "environment": {"python": platform.python_version(), "scikitLearn": sklearn.__version__},
        "models": {
            "production": {"type": "HistGradientBoostingRegressor (quantile q10/q50/q90) x horizons 7/30/90",
                           "features": prod_art["features"], "metrics": prod_m},
            "anomaly": {"type": "IsolationForest + per-well robust z-score attribution",
                        "features": anom_art["features"], "metrics": anom_m},
            "risk": {"type": "HistGradientBoostingClassifier (3 classes; synthetic labels)",
                     "features": risk_art["features"], "metrics": risk_m},
            "equipment": {"type": "HistGradientBoostingClassifier (failure within 30 days; synthetic labels)",
                          "features": eq_art["features"], "metrics": eq_m},
        },
    }
    (out / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"Hazırdır: {version}  ({time.time() - t0:.0f} san). Artefaktlar: {out}")
    return metadata


def main() -> None:
    ap = argparse.ArgumentParser(description="SOCAR ML servisi: modelləri öyrət")
    ap.add_argument("--n-wells", type=int, default=280)
    ap.add_argument("--n-days", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--step", type=int, default=4, help="nümunələr arasındakı gün sayı")
    ap.add_argument("--out-dir", default=str(DEFAULT_MODEL_DIR))
    ap.add_argument("--no-save-dataset", action="store_true")
    a = ap.parse_args()
    run_training(a.out_dir, a.n_wells, a.n_days, a.seed, a.step, not a.no_save_dataset)


if __name__ == "__main__":
    main()
