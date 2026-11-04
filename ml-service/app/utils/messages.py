"""Azərbaycan dilində mətn şablonları və parametr adları (bütün istifadəçiyə göstərilən mətnlər burada)."""
from __future__ import annotations

PARAM_LABELS = {
    "production": "hasilat", "pressure": "təzyiq", "temperature": "temperatur",
    "bottomHolePressure": "dib təzyiqi", "wellheadPressure": "ağız təzyiqi",
    "casingPressure": "kəmər təzyiqi", "tubingPressure": "boru təzyiqi", "waterCut": "su payı",
    "gasOilRatio": "qaz-neft nisbəti", "flowRate": "axın sürəti", "vibration": "vibrasiya",
    "equipmentTemperature": "avadanlıq temperaturu", "pumpEfficiency": "nasos səmərəliliyi",
    "pumpRuntime": "nasosun iş müddəti", "depth": "dərinlik", "well_age_days": "quyunun istismar yaşı",
    "well_type_code": "quyu tipi", "production_target": "hasilat hədəfi",
    "days_since_maintenance": "son texniki xidmətdən keçən gün",
    "days_since_inspection": "son baxışdan keçən gün",
    "production_7d_avg": "7 günlük orta hasilat", "production_30d_avg": "30 günlük orta hasilat",
    "production_90d_avg": "90 günlük orta hasilat", "production_7d_change_pct": "7 günlük hasilat dəyişimi",
    "production_30d_change_pct": "30 günlük hasilat dəyişimi",
    "production_decline_rate": "hasilatın azalma sürəti", "production_volatility_30d": "hasilatın dalğalanması",
    "target_attainment_30d": "hədəfə çatma", "pressure_change_rate": "təzyiqin dəyişmə sürəti",
    "waterCut_trend": "su payı trendi", "gasOilRatio_slope30": "qaz-neft nisbəti trendi",
    "vibration_slope30": "vibrasiya trendi", "equipmentTemperature_slope30": "avadanlıq temperatur trendi",
    "pumpEfficiency_slope30": "nasos səmərəliliyi trendi", "downtime_7d_hours": "7 günlük dayanma",
    "downtime_30d_hours": "30 günlük dayanma", "pump_fault_frac_7d": "son 7 gündə nasos nasazlıqları",
    "pump_fault_frac_30d": "son 30 gündə nasos nasazlıqları",
    **{f"zself_{k}": f"{v} (öz tarixçəsindən kənarlaşma)" for k, v in {
        "production": "hasilat", "pressure": "təzyiq", "temperature": "temperatur",
        "bottomHolePressure": "dib təzyiqi", "wellheadPressure": "ağız təzyiqi", "vibration": "vibrasiya",
        "equipmentTemperature": "avadanlıq temperaturu", "pumpEfficiency": "nasos səmərəliliyi",
        "waterCut": "su payı"}.items()},
}


def label(name: str) -> str:
    return PARAM_LABELS.get(name, name)


def direction_az(z: float) -> str:
    return "yüksəkdir" if z > 0 else "aşağıdır"
