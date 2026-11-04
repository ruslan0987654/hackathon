"""API inteqrasiya testləri (FastAPI TestClient). İşə salma: pytest -v
Qeyd: ilk işə salmada kiçik model dəsti öyrədilir (~30 san)."""
import os

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from tests.helpers import make_payload, model_dir  # noqa: E402

os.environ["API_KEY"] = "test-key"
os.environ["ADMIN_API_KEY"] = "admin-key"
os.environ["MODEL_DIR"] = str(model_dir())
os.environ["MAX_BATCH_SIZE"] = "3"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

H = {"X-API-Key": "test-key"}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _body(**kw):
    p = make_payload(**kw)
    for r in p["history"]:
        r["timestamp"] = r["timestamp"].isoformat()
    return p


def test_health_open(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["modelsLoaded"] is True


def test_auth_required(client):
    assert client.post("/predict/full-analysis", json=_body()).status_code == 401
    assert client.post("/predict/full-analysis", json=_body(), headers={"X-API-Key": "wrong"}).status_code == 401


def test_model_info(client):
    r = client.get("/model/info", headers=H)
    assert r.status_code == 200 and r.json()["dataBasis"] == "synthetic"


@pytest.mark.parametrize("path", ["production", "anomaly", "risk", "equipment", "full-analysis"])
def test_predict_endpoints(client, path):
    r = client.post(f"/predict/{path}", json=_body(), headers=H)
    assert r.status_code == 200, r.text
    assert r.json()["wellId"] == "TEST-1"


def test_full_analysis_fields(client):
    j = client.post("/predict/full-analysis", json=_body(), headers=H).json()
    for k in ("predictedProduction7d", "riskLevel", "anomalyScore", "recommendations", "dataQuality", "confidence"):
        assert k in j


def test_validation_errors(client):
    assert client.post("/predict/production", json={"wellId": "X", "history": []}, headers=H).status_code == 422
    bad = _body()
    bad["history"][0]["waterCut"] = 250
    assert client.post("/predict/production", json=bad, headers=H).status_code == 422


def test_batch_and_limit(client):
    ok = client.post("/predict/batch", json={"wells": [_body(), _body(well_idx=1)]}, headers=H)
    assert ok.status_code == 200 and ok.json()["succeeded"] == 2
    too_many = client.post("/predict/batch", json={"wells": [_body()] * 4}, headers=H)
    assert too_many.status_code == 422


def test_retrain_protected(client):
    assert client.post("/model/retrain", json={}, headers=H).status_code == 401
    assert client.post("/model/retrain", json={}).status_code == 401


def test_request_size_limit(client):
    r = client.post("/predict/production", content=b"x" * 6_000_000, headers={**H, "Content-Type": "application/json"})
    assert r.status_code == 413
