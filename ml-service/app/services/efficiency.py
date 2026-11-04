"""Əməliyyat səmərəliliyi: izah oluna bilən KPI (ML modeli deyil, şəffaf formula).

Komponentlər (mövcud olanlar üzrə çəkilər yenidən normallaşdırılır):
  hədəfə çatma (50%) = orta hasilat / productionTarget (maks 100%)
  əlçatanlıq    (30%) = 1 - orta gündəlik dayanma saatı / 24     (və ya operatingHours / 24)
  nasos         (20%) = orta nasos səmərəliliyi / 100
Cari 30 gün əvvəlki 30 günlə müqayisə olunur.
"""
from __future__ import annotations

import numpy as np

from app.utils.stats import window

WEIGHTS = {"targetAttainment": 0.5, "availability": 0.3, "pumpEfficiency": 0.2}
LABELS = {"targetAttainment": "hədəfə çatma", "availability": "əlçatanlıq (az dayanma)",
          "pumpEfficiency": "nasos səmərəliliyi"}


def _components(ts, cols, t0, lo, hi, target) -> dict:
    comp = {}
    prod = window(ts, cols["production"], t0, lo, hi)
    if prod.size >= 3 and target and target > 0:
        comp["targetAttainment"] = float(min(prod.mean() / target, 1.0))
    dt = window(ts, cols["downtimeHours"], t0, lo, hi)
    op = window(ts, cols["operatingHours"], t0, lo, hi)
    if dt.size >= 3:
        comp["availability"] = float(np.clip(1 - dt.mean() / 24.0, 0, 1))
    elif op.size >= 3:
        comp["availability"] = float(np.clip(op.mean() / 24.0, 0, 1))
    pe = window(ts, cols["pumpEfficiency"], t0, lo, hi)
    pe = pe[pe > 0]
    if pe.size >= 3:
        comp["pumpEfficiency"] = float(np.clip(pe.mean() / 100.0, 0, 1))
    return comp


def _score(comp: dict):
    if not comp:
        return None
    w = {k: WEIGHTS[k] for k in comp}
    tot = sum(w.values())
    return float(sum(comp[k] * w[k] for k in comp) / tot * 100.0)


def run(ts, cols, payload) -> dict:
    t0 = float(ts[-1])
    target = payload.get("productionTarget")
    cur = _components(ts, cols, t0, 0, 30, target)
    prev = _components(ts, cols, t0, 30, 60, target)
    s_cur, s_prev = _score(cur), _score(prev)
    if s_cur is None:
        return {"status": "insufficient_data", "operationalEfficiency": None, "efficiencyDetails": None,
                "statusMessage": "Səmərəlilik üçün productionTarget, downtimeHours/operatingHours və ya pumpEfficiency lazımdır."}
    details = {
        "formula": "50% hədəfə çatma + 30% əlçatanlıq + 20% nasos səmərəliliyi (mövcud komponentlər üzrə normallaşdırılır)",
        "currentPeriodDays": 30,
        "currentComponentsPct": {k: round(v * 100, 1) for k, v in cur.items()},
        "previousComponentsPct": {k: round(v * 100, 1) for k, v in prev.items()},
        "previousEfficiency": round(s_prev, 1) if s_prev is not None else None,
        "changePoints": None, "explanation": "Əvvəlki 30 gün üçün kifayət qədər məlumat yoxdur; müqayisə aparılmadı.",
    }
    if s_prev is not None:
        # müqayisə yalnız hər iki dövrdə olan komponentlər üzrə (kompozisiya fərqi saxta dəyişiklik yaratmasın)
        common = [k for k in cur if k in prev]
        like_cur = _score({k: cur[k] for k in common}) if common else None
        like_prev = _score({k: prev[k] for k in common}) if common else None
        if like_cur is not None and like_prev is not None:
            delta = like_cur - like_prev
            details["changePoints"] = round(delta, 1)
            parts = sorted(((cur[k] - prev[k]) * 100, k) for k in common)
            drivers = [f"{LABELS[k]} ({d:+.1f} b.b.)" for d, k in parts if abs(d) >= 1.0]
            if abs(delta) < 1.0:
                details["explanation"] = "Səmərəlilik əvvəlki 30 günlə müqayisədə praktiki olaraq dəyişməyib."
            else:
                word = "artıb" if delta > 0 else "azalıb"
                tail = (" Əsas komponentlər: " + ", ".join(drivers) + ".") if drivers else ""
                details["explanation"] = f"Səmərəlilik əvvəlki 30 günlə müqayisədə {abs(delta):.1f} faiz bəndi {word}.{tail}"
    return {"status": "ok", "operationalEfficiency": round(s_cur, 1), "efficiencyDetails": details}
