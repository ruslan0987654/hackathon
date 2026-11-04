"""samples/ qovluğuna test JSON-ları yaradır (SİNTETİK quyular, son ölçmə = bugün)."""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from app.preprocessing.synthetic import simulate_wells  # noqa: E402


def payload(w, day, history_days, end, well_id, degrade=False):
    pidx = np.flatnonzero(w["present"])
    sl = pidx[(pidx <= day) & (pidx > day - history_days)]
    recs = []
    for d in sl:
        r = {"timestamp": (end + timedelta(days=int(d - day))).strftime("%Y-%m-%dT00:00:00Z")}
        for k, v in w["cols"].items():
            if k == "pumpFault":
                r["pumpStatus"] = None if np.isnan(v[d]) else ("fault" if v[d] == 1 else "running")
            else:
                r[k] = None if np.isnan(v[d]) else round(float(v[d]), 3)
        recs.append(r)
    if degrade:  # son 20 gündə nasos sensorlarının pisləşməsi (nümunə ssenari)
        for i, r in enumerate(recs[-20:]):
            f = (i + 1) / 20
            r["vibration"], r["equipmentTemperature"], r["pumpEfficiency"] = round(2 + 6 * f, 3), round(60 + 30 * f, 3), round(85 - 30 * f, 3)
    si = w["static_info"]
    return {"wellId": well_id, "wellName": si["wellName"], "fieldName": si["fieldName"], "region": si["region"],
            "wellType": si["wellType"], "wellStatus": "producing", "latitude": round(si["latitude"], 5),
            "longitude": round(si["longitude"], 5), "depth": round(si["depth"], 1),
            "drillingDate": "2019-03-15", "operationStartDate": "2019-06-01", "maintenanceDate": "2026-08-20",
            "lastInspectionDate": "2026-10-05", "productionTarget": round(float(w["plan"][day]), 3), "history": recs}


def main():
    end = datetime.now(timezone.utc).replace(tzinfo=None).replace(hour=0, minute=0, second=0, microsecond=0)
    ws = simulate_wells(4, 800, 777)
    out = root / "samples"
    out.mkdir(exist_ok=True)
    full = payload(ws[0], 600, 120, end, "SYN-DEMO-001")
    minimal = {"wellId": "SYN-DEMO-MIN", "history": [{"timestamp": end.strftime("%Y-%m-%dT00:00:00Z"), "production": 120.5, "pressure": 180.0}]}
    degraded = payload(ws[1], 600, 120, end, "SYN-DEMO-002-DEGRADED-PUMP", degrade=True)
    batch = {"wells": [full, degraded, payload(ws[2], 650, 90, end, "SYN-DEMO-003")]}
    for name, obj in (("sample_full.json", full), ("sample_minimal.json", minimal),
                      ("sample_degraded_pump.json", degraded), ("sample_batch.json", batch)):
        (out / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
        print("yaradıldı:", out / name)


if __name__ == "__main__":
    main()
