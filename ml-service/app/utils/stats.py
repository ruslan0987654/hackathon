"""Kiçik statistik köməkçi funksiyalar (yalnız numpy)."""
from __future__ import annotations

import numpy as np

NAN = float("nan")


def finite(a: np.ndarray) -> np.ndarray:
    a = np.asarray(a, dtype=float)
    return a[np.isfinite(a)]


def window(ts: np.ndarray, a: np.ndarray, t0: float, lo: float, hi: float) -> np.ndarray:
    """(t0-hi, t0-lo] günlük aralığındakı sonlu qiymətlər."""
    m = (ts > t0 - hi) & (ts <= t0 - lo)
    return finite(a[m])


def latest(ts: np.ndarray, a: np.ndarray, t0: float, max_age: float = 3.0) -> float:
    """Son `max_age` gün ərzindəki sonuncu sonlu qiymət; yoxdursa NaN."""
    m = (ts > t0 - max_age) & (ts <= t0) & np.isfinite(a)
    idx = np.flatnonzero(m)
    return float(a[idx[-1]]) if idx.size else NAN


def slope(ts: np.ndarray, a: np.ndarray, t0: float, days: float,
          min_pts: int = 5, min_span_ratio: float = 0.3) -> float:
    """Son `days` gün üzrə xətti reqressiya meyli (vahid/gün)."""
    m = (ts > t0 - days) & (ts <= t0) & np.isfinite(a)
    x, y = ts[m], a[m]
    if x.size < min_pts or (x.max() - x.min()) < days * min_span_ratio:
        return NAN
    xm = x.mean()
    den = float(((x - xm) ** 2).sum())
    if den <= 0:
        return NAN
    return float(((x - xm) * (y - y.mean())).sum() / den)


def robust_center_scale(values: np.ndarray, rel_floor: float = 0.03, abs_floor: float = 1e-6):
    """Median və MAD əsaslı davamlı miqyas (outlier-lərə həssas deyil)."""
    values = finite(values)
    med = float(np.median(values))
    mad = float(np.median(np.abs(values - med)))
    return med, max(1.4826 * mad, rel_floor * abs(med), abs_floor)
