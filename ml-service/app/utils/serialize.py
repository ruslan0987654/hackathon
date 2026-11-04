"""Cavabları JSON-a təhlükəsiz çevirmək: numpy tipləri -> Python tipləri, NaN/Inf -> null."""
from __future__ import annotations

import math
from datetime import date, datetime
from typing import Any

import numpy as np


def clean(x: Any) -> Any:
    if isinstance(x, dict):
        return {str(k): clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [clean(v) for v in x]
    if isinstance(x, np.ndarray):
        return clean(x.tolist())
    if isinstance(x, (np.bool_, bool)):
        return bool(x)
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        v = float(x)
        return v if math.isfinite(v) else None
    if isinstance(x, (datetime, date)):
        return x.isoformat()
    return x
