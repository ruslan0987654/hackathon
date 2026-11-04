"""SİNTETİK quyu məlumatı generatoru.

DİQQƏT: Bu məlumat YALNIZ development, test və inteqrasiya üçündür. Real SOCAR məlumatı DEYİL.
Fiziki proseslər sadələşdirilmişdir (Arps hiperbolik azalma, təzyiqin eksponensial düşməsi, su payının
sigmoid artımı, nasosun gizli "sağlamlıq" dəyişəninin tədricən pisləşməsi, təsadüfi anomaliyalar).
Bu məlumat əsasında öyrədilmiş modelin real istehsalatda dəqiqliyinə zəmanət verilmir.

Vahidlər (şərti): hasilat t/gün, təzyiq bar, temperatur °C, su payı %, vibrasiya mm/s, nasos səmərəliliyi %.
"""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np

from app.preprocessing.features import SERIES_FIELDS
from app.utils.stats import NAN

START_DATE = date(2023, 1, 1)
WELL_TYPES = ["oil", "gas", "oil_gas"]
FIELD_NAMES = ["Sintetik Sahə A", "Sintetik Sahə B", "Sintetik Sahə C", "Sintetik Sahə D"]
REGIONS = ["Region-1", "Region-2", "Region-3"]
HORIZONS = (7, 30, 90)


def _events_since(events: list[int], n: int) -> np.ndarray:
    """Hər gün üçün "ən son hadisədən keçən gün sayı"."""
    ev = np.array(sorted(events))
    idx = np.searchsorted(ev, np.arange(n), side="right") - 1
    return (np.arange(n) - ev[idx]).astype(float)


def simulate_well(idx: int, n_days: int, seed: int) -> dict:
    r = np.random.default_rng(seed)
    n = n_days
    d = np.arange(n)

    wtype = str(r.choice(WELL_TYPES, p=[0.5, 0.2, 0.3]))
    depth = float(r.uniform(1500, 6200))
    qi, b, di = float(r.uniform(40, 600)), float(r.uniform(0.2, 1.0)), float(r.uniform(0.0008, 0.004))
    age0 = int(r.integers(30, 1500))
    t_abs = age0 + d
    base = qi / (1 + b * di * t_abs) ** (1 / b)          # Arps hiperbolik azalma
    plan = base * 1.06                                    # istehsal planı (hədəf)
    p0, tau = float(r.uniform(120, 380)), float(r.uniform(900, 3000))
    pres = 45.0 + (p0 - 45.0) * np.exp(-t_abs / tau)
    depl = np.clip(1 - pres / p0, 0, 1)
    wc = 100 * r.uniform(0.5, 0.95) / (1 + np.exp(-(t_abs - r.uniform(500, 2500)) / r.uniform(200, 500)))
    gor = r.uniform(60, 300) * (1 + 0.0004 * t_abs)

    # ---- nasosun gizli sağlamlıq dəyişəni h (0=yeni, ~1=nasazlıq) ----
    h = float(r.uniform(0, 0.8))
    rate = 1.0 / float(r.uniform(150, 450))
    theta = float(r.normal(1.0, 0.12))
    preventive = r.random() < 0.7
    pm_interval = float(r.uniform(150, 400))
    next_pm = int(r.integers(30, 200))
    maint = [-int(r.integers(10, 300))]
    insp, k = [], -int(r.integers(5, 90))
    while k < n:
        insp.append(k)
        k += int(r.integers(80, 101))
    h_arr, down, fault = np.zeros(n), np.zeros(n), np.zeros(n)
    failure_days: list[int] = []
    failure_downtime: list[float] = []
    repair_left, repair_len = 0, 0
    for day in range(n):
        if repair_left > 0:
            repair_left -= 1
            down[day] = 24.0
            h_arr[day] = h
            continue
        h += max(0.0, rate * (1 + 0.4 * r.standard_normal()))
        if h >= theta or r.random() < 1 / 3000:
            failure_days.append(day)
            repair_len = int(r.integers(2, 9))
            failure_downtime.append(repair_len * 24.0)
            repair_left = repair_len
            down[day] = 24.0
            fault[day] = 1.0
            h = 0.05
            maint.append(day)
        elif preventive and day >= next_pm:
            maint.append(day)
            h *= 0.25
            next_pm = day + max(30, int(pm_interval * (1 + 0.2 * r.standard_normal())))
        h_arr[day] = h

    partial = (r.random(n) < 0.03) & (down == 0)
    down = np.where(partial, r.uniform(1, 6, n), down)
    repair_day = down >= 24.0

    # ---- müşahidə olunan siqnallar ----
    prod = base * (1 - 0.18 * h_arr ** 2) * (1 + r.normal(0, 0.03, n)) * (24 - down) / 24
    pump_eff = np.clip(88 - 25 * h_arr ** 1.5 + r.normal(0, 1.5, n), 20, 100)
    vib = 1.8 + 6.5 * h_arr ** 2 + np.abs(r.normal(0, 0.25, n))
    eq_temp = 55 + 28 * h_arr + 5 * np.sin(2 * np.pi * d / 365) + r.normal(0, 1.5, n)
    p_line = pres * (1 + r.normal(0, 0.01, n))
    bhp = pres * 0.92 * (1 + r.normal(0, 0.01, n))
    whp = pres * 0.45 * (1 + r.normal(0, 0.012, n))
    csg = whp * 1.15 * (1 + r.normal(0, 0.012, n))
    tub = whp * 0.90 * (1 + r.normal(0, 0.012, n))
    temp = 20 + depth * 0.03 + r.normal(0, 1.0, n)
    wcut = np.clip(wc + r.normal(0, 0.6, n), 0, 100)
    gor_obs = gor * (1 + r.normal(0, 0.04, n))

    # ---- təsadüfi anomaliya hadisələri (etiketlənmiş, yalnız qiymətləndirmə üçün) ----
    anom = np.zeros(n)
    for _ in range(int(r.poisson(n / 80))):
        s, dur, kind = int(r.integers(0, n)), int(r.integers(1, 5)), int(r.integers(0, 5))
        sl = slice(s, min(n, s + dur))
        anom[sl] = 1.0
        if kind == 0:
            p_line[sl] *= 0.6; bhp[sl] *= 0.6; whp[sl] *= 0.6; csg[sl] *= 0.6; tub[sl] *= 0.6
        elif kind == 1:
            eq_temp[sl] += 22
        elif kind == 2:
            prod[sl] *= 0.45
        elif kind == 3:
            vib[sl] += 5
        else:
            wcut[sl] = np.clip(wcut[sl] + 18, 0, 100)
    # nasos dayanıb (təmir) -> sensorlar sıfıra/ətraf mühitə yaxın
    pump_eff[repair_day] = 0.0
    vib[repair_day] = 0.0
    eq_temp[repair_day] = 25.0
    anom = np.maximum(anom, repair_day.astype(float))
    prod = np.clip(prod, 0, None)

    # ---- törəmə kəmiyyətlər ----
    oil = prod * (1 - wcut / 100)
    water = prod * wcut / 100
    gas = oil * gor_obs
    flow = prod / 0.85 / 24.0

    # ---- gizli risk dəyişəni (etiketlər üçün) ----
    anom_recent = np.convolve(anom, np.ones(14) / 14, mode="full")[:n]
    risk_latent = (0.45 * h_arr + 0.25 * depl + 0.12 * (1 - base / qi) + 0.10 * (wcut / 100)
                   + 0.08 * np.clip(anom_recent * 4, 0, 1) + r.normal(0, 0.04, n))

    # ---- etiketlər: gələcək nasazlıq və gələcək orta hasilat ----
    fail_ind = np.zeros(n)
    fail_ind[failure_days] = 1.0
    cf = np.cumsum(fail_ind)
    fail30 = np.zeros(n)
    hi = np.minimum(d + 30, n - 1)
    fail30[:] = (cf[hi] - cf[d]) > 0
    cs = np.cumsum(prod)
    y_abs = {}
    for hz in HORIZONS:
        arr = np.full(n, NAN)
        ok = d + hz < n
        arr[ok] = (cs[d[ok] + hz] - cs[d[ok]]) / hz
        y_abs[hz] = arr

    observed = {
        "production": prod, "oilProduction": oil, "gasProduction": gas, "waterProduction": water,
        "pressure": p_line, "temperature": temp, "bottomHolePressure": bhp, "wellheadPressure": whp,
        "casingPressure": csg, "tubingPressure": tub, "waterCut": wcut, "gasOilRatio": gor_obs,
        "flowRate": flow, "vibration": vib, "equipmentTemperature": eq_temp, "pumpEfficiency": pump_eff,
        "pumpRuntime": 24.0 - down, "operatingHours": 24.0 - down, "downtimeHours": down.copy(),
    }
    obs = {k: np.asarray(observed[k], dtype=float).copy() for k in SERIES_FIELDS}
    obs["pumpFault"] = fault.copy()

    # ---- çatışmayan məlumat: təsadüfi boşluqlar + bəzi quyularda tam sütun yoxluğu ----
    for k in list(obs):
        obs[k][r.random(n) < 0.03] = NAN
    drop_cols: list[str] = []
    if r.random() < 0.25:
        drop_cols += ["casingPressure", "tubingPressure"]
    if r.random() < 0.15:
        drop_cols += ["gasOilRatio", "gasProduction"]
    if r.random() < 0.12:
        drop_cols += ["vibration", "equipmentTemperature"]
    if r.random() < 0.10:
        drop_cols += ["pumpEfficiency"]
    for k in drop_cols:
        obs[k][:] = NAN
    present = r.random(n) > 0.02
    present[0] = True

    return {
        "wellId": f"SYN-{idx:04d}",
        "static_info": {
            "wellName": f"Sintetik quyu {idx}", "fieldName": FIELD_NAMES[idx % len(FIELD_NAMES)],
            "region": REGIONS[idx % len(REGIONS)], "wellType": wtype, "wellStatus": "producing",
            "latitude": float(r.uniform(39.5, 41.0)), "longitude": float(r.uniform(48.5, 50.5)),
            "depth": depth, "age0": age0,
        },
        "cols": obs, "present": present, "plan": plan,
        "since_maint": _events_since(maint, n), "since_insp": _events_since(insp, n),
        "maint_events": maint, "failure_days": failure_days, "failure_downtime": failure_downtime,
        "fail30": fail30, "y_abs": y_abs, "anomaly": anom, "risk_latent": risk_latent,
        "prod_true": prod, "n_days": n,
    }


def simulate_wells(n_wells: int, n_days: int, seed: int) -> list[dict]:
    root = np.random.default_rng(seed)
    seeds = root.integers(0, 2**31 - 1, size=n_wells)
    return [simulate_well(i, n_days, int(s)) for i, s in enumerate(seeds)]


def day_to_date(day: int) -> date:
    return START_DATE + timedelta(days=int(day))
