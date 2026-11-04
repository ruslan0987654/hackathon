"""Məlumat keyfiyyətinin və etibarlılığın qiymətləndirilməsi (heç nə uydurulmur, yalnız mövcud olan ölçülür)."""
from __future__ import annotations

from datetime import datetime, timezone

import numpy as np

from app.preprocessing.features import CORE_FIELDS
from app.utils.stats import window

NON_PRODUCING = {"shut_in", "shutin", "inactive", "suspended", "abandoned", "closed", "idle", "dayanıb", "bağlı"}


def assess(ts, cols, last_dt, n_records, payload, used_provided: list[str], now: datetime | None = None) -> dict:
    t0 = float(ts[-1])
    n30 = int(((ts > t0 - 30) & (ts <= t0)).sum())
    n_eff = max(n30, 1)
    coverage, missing = {}, []
    for f in CORE_FIELDS:
        a = cols[f]
        cnt = int(np.isfinite(window(ts, a, t0, 0, 30)).sum()) if n30 else int(np.isfinite(a[-1:]).sum())
        coverage[f] = round(min(1.0, cnt / n_eff), 3)
        if cnt == 0:
            missing.append(f)
    completeness = float(np.mean(list(coverage.values())) * 100)
    history_days = float(ts[-1] - ts[0])

    warnings: list[str] = []
    if history_days < 30:
        warnings.append(f"Tarixçə qısadır ({history_days:.0f} gün). Trend göstəriciləri və proqnozlar etibarsız ola bilər.")
    if missing:
        warnings.append("Aşağıdakı göstəricilər üzrə son 30 gündə heç bir ölçmə yoxdur: " + ", ".join(missing) + ".")
    if payload.get("productionTarget") is None:
        warnings.append("productionTarget göndərilməyib: hədəfə çatma və səmərəlilik hesablaması məhdudlaşır.")
    status = str(payload.get("wellStatus") or "").strip().lower().replace("-", "_").replace(" ", "_")
    if status in NON_PRODUCING:
        warnings.append(f"Quyunun statusu '{payload.get('wellStatus')}'. Proqnoz normal istismar rejimini fərz edir.")
    now = now or datetime.now(timezone.utc).replace(tzinfo=None)
    age_days = (now - last_dt).total_seconds() / 86400.0
    if age_days > 3:
        warnings.append(f"Ən son ölçmə {age_days:.0f} gün əvvəlindir; nəticələr cari vəziyyəti əks etdirməyə bilər.")
    if used_provided:
        warnings.append("Tarixçədən hesablana bilməyən göstəricilər üçün göndərilmiş hazır dəyərlər istifadə olundu: "
                        + ", ".join(used_provided) + ".")

    level = "good" if completeness >= 80 and history_days >= 60 else (
        "fair" if completeness >= 50 and history_days >= 14 else "poor")
    return {
        "level": level, "completenessPct": round(completeness, 1), "fieldCoverage30d": coverage,
        "missingFields": missing, "recordCount": int(n_records), "recordsLast30d": n30,
        "historyDays": round(history_days, 1), "dataAgeDays": round(age_days, 1), "warnings": warnings,
    }


def base_confidence(quality: dict) -> float:
    """Evristik etibarlılıq balı (0..1) = məlumat tamlığı x tarixçə uzunluğu. Statistik ehtimal DEYİL."""
    comp = quality["completenessPct"] / 100.0
    hist = min(1.0, quality["historyDays"] / 60.0) ** 0.5
    return float(np.clip(comp * hist, 0.0, 1.0))


def confidence_level(score: float) -> str:
    return "high" if score >= 0.75 else ("medium" if score >= 0.45 else "low")
