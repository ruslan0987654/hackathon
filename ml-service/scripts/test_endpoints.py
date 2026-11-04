"""İşləyən servisi bütün endpoint-lər üzrə yoxlayır. Əvvəlcə run.bat ilə servisi başladın.

İstifadə:  python scripts\\test_endpoints.py [http://127.0.0.1:8000]
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

root = Path(__file__).resolve().parents[1]
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"


def read_env() -> dict:
    env = {}
    f = root / ".env"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def shift_to_today(well: dict) -> dict:
    """Nümunənin son ölçməsini bugünə çəkir ki, 'köhnə məlumat' xəbərdarlığı çıxmasın."""
    last = max(datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00")) for r in well["history"])
    delta = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) - last
    for r in well["history"]:
        t = datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00")) + delta
        r["timestamp"] = t.strftime("%Y-%m-%dT00:00:00Z")
    return well


def load(name: str) -> dict:
    return json.loads((root / "samples" / name).read_text(encoding="utf-8"))


def main() -> int:
    env = read_env()
    h = {"X-API-Key": env.get("API_KEY", "")}
    full, degraded, minimal = (shift_to_today(load(n)) for n in ("sample_full.json", "sample_degraded_pump.json", "sample_minimal.json"))
    batch = load("sample_batch.json")
    batch["wells"] = [shift_to_today(w) for w in batch["wells"]]
    failures = 0

    def check(name, resp, expect=200):
        nonlocal failures
        ok = resp.status_code == expect
        failures += 0 if ok else 1
        print(f"[{'OK' if ok else 'XƏTA'}] {name}: HTTP {resp.status_code}")
        return resp

    with httpx.Client(base_url=BASE, timeout=60) as c:
        check("GET /health", c.get("/health"))
        check("GET /model/info", c.get("/model/info", headers=h))
        for p in ("production", "anomaly", "risk", "equipment"):
            check(f"POST /predict/{p}", c.post(f"/predict/{p}", json=full, headers=h))
        r = check("POST /predict/full-analysis (normal)", c.post("/predict/full-analysis", json=full, headers=h))
        if r.status_code == 200:
            j = r.json()
            print("   ", {k: j[k] for k in ("predictedProduction30d", "anomalyDetected", "riskLevel", "equipmentFailureProbability", "operationalEfficiency")})
        r = check("POST /predict/full-analysis (nasos pisləşib)", c.post("/predict/full-analysis", json=degraded, headers=h))
        if r.status_code == 200:
            j = r.json()
            print("   ", {k: j[k] for k in ("riskLevel", "equipmentFailureProbability", "maintenanceRecommended")})
        r = check("POST /predict/full-analysis (1 qeyd, az məlumat)", c.post("/predict/full-analysis", json=minimal, headers=h))
        if r.status_code == 200:
            print("    məlumat keyfiyyəti:", r.json()["dataQuality"]["level"], "| status:", r.json()["componentStatus"])
        check("POST /predict/batch", c.post("/predict/batch", json=batch, headers=h))
        check("Autentifikasiya yoxdur -> 401", c.post("/predict/production", json=full), 401)
        check("Yanlış sorğu -> 422", c.post("/predict/production", json={"wellId": "X", "history": []}, headers=h), 422)
        check("Retrain admin açarsız -> 401", c.post("/model/retrain", json={}, headers=h), 401)
    print("\nNƏTİCƏ:", "bütün yoxlamalar keçdi" if not failures else f"{failures} yoxlama uğursuz oldu")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
