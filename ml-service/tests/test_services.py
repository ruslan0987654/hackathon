"""Servis qatının testləri (FastAPI tələb etmir): feature-lər, modellər, cavab formatı, çatışmayan məlumat."""
import json
import math
from datetime import datetime

import numpy as np

from app.preprocessing.features import FEATURE_NAMES, build_series, compute_features, static_from_payload
from app.services import analysis
from tests.helpers import bundle, make_payload, wells

NOW = datetime(2026, 11, 2)

SPEC_KEYS = [
    "wellId", "analysisTimestamp", "modelVersion", "currentProduction", "predictedProduction7d",
    "predictedProduction30d", "predictedProduction90d", "productionChangePct", "anomalyDetected",
    "anomalyScore", "detectedAnomalies", "riskLevel", "riskScore", "riskReasons",
    "equipmentFailureProbability", "operationalEfficiency", "estimatedDowntime", "recommendations",
    "dataQuality", "confidence",
]


def test_full_analysis_has_all_spec_fields_and_is_json_safe():
    out = analysis.full_analysis(analysis.prepare(make_payload(), NOW), bundle())
    for k in SPEC_KEYS:
        assert k in out, k
    json.dumps(out, allow_nan=False)  # NaN/Inf olmamalıdır
    assert out["riskLevel"] in ("low", "medium", "high")
    assert 0 <= out["riskScore"] <= 1
    assert 0 <= out["equipmentFailureProbability"] <= 1
    assert out["recommendations"], "ən azı bir tövsiyə (və ya 'normal' mesajı) olmalıdır"
    assert all(r["requiresEngineerReview"] for r in out["recommendations"])


def test_serving_features_match_training_path():
    """Training/serving skew yoxdur: API yolu ilə hesablanan feature-lər birbaşa massivlərlə eynidir."""
    payload = make_payload(1, 500)
    ts, cols, first, last, _ = build_series(payload)
    direct = compute_features(ts, cols, static_from_payload(payload, last))
    via_api = analysis.prepare(payload, NOW).feats
    for k in FEATURE_NAMES:
        a, b = direct[k], via_api[k]
        assert (math.isnan(a) and math.isnan(b)) or math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9), k


def test_features_use_only_past_data():
    """Sonuncu qeydə qədər olan məlumat dəyişməyibsə, sonradan əlavə olunan qeydlər əvvəlki anın feature-lərini dəyişmir."""
    full = make_payload(2, 600, history_days=150)
    cut = dict(full, history=full["history"][:-20])
    f_cut = analysis.prepare(cut, NOW).feats
    ts, cols, first, last, _ = build_series(full)
    idx = ts <= ts[-21] + 1e-9
    f_trunc = compute_features(ts[idx], {k: v[idx] for k, v in cols.items()}, static_from_payload(cut, last))
    for k in ("production_7d_avg", "production_30d_avg", "pressure", "zself_production"):
        a, b = f_cut[k], f_trunc[k]
        assert (math.isnan(a) and math.isnan(b)) or math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-9), k


def test_single_record_with_missing_values_does_not_fabricate_numbers():
    payload = {"wellId": "MIN-1", "history": [{"timestamp": "2026-11-01T00:00:00", "production": None}]}
    payload["history"][0]["timestamp"] = datetime(2026, 11, 1)
    out = analysis.full_analysis(analysis.prepare(payload, NOW), bundle())
    json.dumps(out, allow_nan=False)
    assert out["predictedProduction30d"] is None
    assert out["equipmentFailureProbability"] is None
    assert out["operationalEfficiency"] is None
    assert out["dataQuality"]["level"] == "poor"
    assert out["componentStatus"]["production"] == "insufficient_data"


def test_partial_data_still_works():
    payload = make_payload(3, 450, history_days=40)
    for r in payload["history"]:
        for k in ("vibration", "equipmentTemperature", "pumpEfficiency", "gasOilRatio", "casingPressure"):
            r[k] = None
    out = analysis.full_analysis(analysis.prepare(payload, NOW), bundle())
    assert out["componentStatus"]["equipment"] == "insufficient_sensor_data"
    assert out["equipmentFailureProbability"] is None
    assert out["predictedProduction30d"] is not None


def test_injected_pressure_drop_is_detected():
    payload = make_payload(0, 600, history_days=90)
    last = payload["history"][-1]
    for k in ("pressure", "bottomHolePressure", "wellheadPressure", "casingPressure", "tubingPressure"):
        if last.get(k) is not None:
            last[k] = last[k] * 0.45
    out = analysis.full_analysis(analysis.prepare(payload, NOW), bundle())
    assert out["anomalyDetected"] is True
    assert any(a["parameter"] in ("pressure", "bottomHolePressure", "wellheadPressure") for a in out["detectedAnomalies"])


def test_forecast_beats_persistence_on_synthetic_test_split():
    m = bundle().metadata["models"]["production"]["metrics"]
    for h in ("7d", "30d", "90d"):
        t = m[h]["test"]
        assert t["MAE"] < t["baselineMAE_persistence"], h


def test_classifiers_have_signal_on_unseen_wells():
    m = bundle().metadata["models"]
    assert m["equipment"]["metrics"]["test"]["ROC_AUC"] > 0.70
    assert m["risk"]["metrics"]["test"]["macroF1"] > 0.60
    assert m["anomaly"]["metrics"]["test"]["ROC_AUC"] > 0.75


def test_overfitting_gap_is_bounded():
    m = bundle().metadata["models"]
    assert m["equipment"]["metrics"]["train"]["ROC_AUC"] - m["equipment"]["metrics"]["test"]["ROC_AUC"] < 0.20
    assert m["risk"]["metrics"]["train"]["macroF1"] - m["risk"]["metrics"]["test"]["macroF1"] < 0.20


def test_split_has_no_well_or_time_leakage():
    meta = bundle().metadata["dataset"]
    r = meta["splitRanges"]
    assert r["val"][0] - r["train"][1] >= 90 and r["test"][0] - r["val"][1] >= 90  # ən uzun ufuq qədər boşluq
    assert sum(meta["wellsPerSplit"].values()) == meta["nWells"]  # hər quyu yalnız bir bölgüdə


def test_failure_probability_higher_for_degraded_pump():
    """Nasos sensorları pisləşmiş quyu üçün ehtimal sağlam quyudan yüksək olmalıdır."""
    base = make_payload(4, 600, history_days=90)
    p_ok = analysis.full_analysis(analysis.prepare(base, NOW), bundle())["equipmentFailureProbability"]
    bad = make_payload(4, 600, history_days=90)
    for i, r in enumerate(bad["history"][-20:]):
        f = (i + 1) / 20
        r["vibration"] = 2.0 + 6.0 * f
        r["equipmentTemperature"] = 60 + 30 * f
        r["pumpEfficiency"] = 85 - 30 * f
    p_bad = analysis.full_analysis(analysis.prepare(bad, NOW), bundle())["equipmentFailureProbability"]
    assert p_bad is not None and p_ok is not None and p_bad > p_ok
