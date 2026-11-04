"""Giriş (request) sxemləri. Bütün ölçmə sahələri ixtiyaridir; çatışmayan dəyərlər NaN kimi emal olunur və UYDURULMUR."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


def _num(ge: float | None = 0, le: float | None = None, desc: str = "") -> Any:
    return Field(default=None, ge=ge, le=le, allow_inf_nan=False, description=desc)


class TimeRecord(BaseModel):
    """Bir ölçmə anı (adətən gündəlik). Quyunun "cari" vəziyyəti ən son timestamp-ə malik qeyddir."""
    model_config = ConfigDict(extra="ignore")

    timestamp: datetime = Field(description="ISO 8601, məs. 2026-10-31T00:00:00Z")
    production: Optional[float] = _num(0, 1e7, "Ümumi mayə hasilatı, t/gün")
    oilProduction: Optional[float] = _num(0, 1e7, "Neft hasilatı")
    gasProduction: Optional[float] = _num(0, 1e10, "Qaz hasilatı")
    waterProduction: Optional[float] = _num(0, 1e7, "Su hasilatı")
    pressure: Optional[float] = _num(0, 3000, "Təzyiq, bar")
    temperature: Optional[float] = _num(-60, 600, "Quyu/yataq temperaturu, °C")
    bottomHolePressure: Optional[float] = _num(0, 3000, "Dib təzyiqi, bar")
    wellheadPressure: Optional[float] = _num(0, 3000, "Ağız təzyiqi, bar")
    casingPressure: Optional[float] = _num(0, 3000, "Kəmər təzyiqi, bar")
    tubingPressure: Optional[float] = _num(0, 3000, "Boru təzyiqi, bar")
    waterCut: Optional[float] = _num(0, 100, "Su payı, % (0-100)")
    gasOilRatio: Optional[float] = _num(0, 1e7, "Qaz-neft nisbəti")
    flowRate: Optional[float] = _num(0, 1e7, "Axın sürəti")
    vibration: Optional[float] = _num(0, 1000, "Vibrasiya, mm/s")
    equipmentTemperature: Optional[float] = _num(-60, 600, "Avadanlıq temperaturu, °C")
    pumpEfficiency: Optional[float] = _num(0, 100, "Nasos səmərəliliyi, % (0-100)")
    pumpRuntime: Optional[float] = _num(0, 24, "Nasosun həmin gün işlədiyi saat (0-24)")
    pumpStatus: Optional[str] = Field(default=None, max_length=32, description="running | stopped | fault ...")
    operatingHours: Optional[float] = _num(0, 24, "Həmin gün əməliyyat saatları (0-24)")
    downtimeHours: Optional[float] = _num(0, 24, "Həmin gün dayanma saatları (0-24)")


class WellInput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    wellId: str = Field(min_length=1, max_length=100)
    wellName: Optional[str] = Field(default=None, max_length=200)
    fieldName: Optional[str] = Field(default=None, max_length=200)
    region: Optional[str] = Field(default=None, max_length=200)
    wellType: Optional[str] = Field(default=None, max_length=50, description="oil | gas | oil_gas | gas_condensate")
    wellStatus: Optional[str] = Field(default=None, max_length=50)
    latitude: Optional[float] = Field(default=None, ge=-90, le=90, allow_inf_nan=False)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180, allow_inf_nan=False)
    depth: Optional[float] = _num(0, 20000, "Dərinlik, m")
    drillingDate: Optional[date] = None
    operationStartDate: Optional[date] = None
    maintenanceDate: Optional[date] = Field(default=None, description="Son texniki xidmət tarixi")
    lastInspectionDate: Optional[date] = None
    productionTarget: Optional[float] = _num(0, 1e7, "Gündəlik hasilat hədəfi (production ilə eyni vahid)")
    # Tarixçədən hesablana bilmədikdə ehtiyat kimi istifadə olunan hazır göstəricilər (ixtiyari):
    production7dAvg: Optional[float] = _num(0, 1e7)
    production30dAvg: Optional[float] = _num(0, 1e7)
    production90dAvg: Optional[float] = _num(0, 1e7)
    production7dChangePct: Optional[float] = Field(default=None, ge=-100, le=10000, allow_inf_nan=False)
    production30dChangePct: Optional[float] = Field(default=None, ge=-100, le=10000, allow_inf_nan=False)
    history: list[TimeRecord] = Field(min_length=1, max_length=2000,
                                      description="Zaman sırası: ən azı 1, tövsiyə olunan ≥ 90 günlük gündəlik qeyd")


class BatchRequest(BaseModel):
    wells: list[WellInput] = Field(min_length=1, max_length=1000)


class RetrainRequest(BaseModel):
    nWells: int = Field(default=200, ge=40, le=1000, description="Sintetik quyu sayı")
    nDays: int = Field(default=1000, ge=500, le=2000)
    seed: int = Field(default=42, ge=0, le=2**31 - 1)
