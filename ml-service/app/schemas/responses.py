"""Çıxış (response) sxemləri. Hesablanmayan nəticələr üçün saxta rəqəm yox, null + status qaytarılır."""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class _Resp(BaseModel):
    model_config = ConfigDict(extra="allow")


class _Header(_Resp):
    wellId: str
    analysisTimestamp: str
    modelVersion: str
    dataBasis: str


class HealthResponse(_Resp):
    status: str
    modelsLoaded: bool
    modelVersion: Optional[str] = None
    detail: Optional[str] = None


class ProductionResponse(_Header):
    status: Optional[str] = None
    statusMessage: Optional[str] = None
    currentProduction: Optional[float] = None
    baselineProduction7dAvg: Optional[float] = None
    predictedProduction7d: Optional[float] = None
    predictedProduction30d: Optional[float] = None
    predictedProduction90d: Optional[float] = None
    productionChangePct: Optional[float] = None
    predictionIntervals: Optional[Any] = None
    forecastDefinition: Optional[str] = None
    forecastVsActual: list[Any] = []
    confidence: Optional[Any] = None
    dataQuality: Optional[Any] = None
    warnings: list[str] = []


class AnomalyResponse(_Header):
    status: Optional[str] = None
    statusMessage: Optional[str] = None
    anomalyDetected: Optional[bool] = None
    anomalyScore: Optional[float] = None
    detectedBy: Optional[Any] = None
    detectedAnomalies: list[Any] = []
    scoreNote: Optional[str] = None
    dataQuality: Optional[Any] = None
    warnings: list[str] = []


class RiskResponse(_Header):
    status: Optional[str] = None
    statusMessage: Optional[str] = None
    riskLevel: Optional[str] = None
    riskScore: Optional[float] = None
    riskReasons: list[Any] = []
    classProbabilities: Optional[Any] = None
    scoreNote: Optional[str] = None
    dataQuality: Optional[Any] = None
    warnings: list[str] = []


class EquipmentResponse(_Header):
    status: Optional[str] = None
    statusMessage: Optional[str] = None
    equipmentFailureProbability: Optional[float] = None
    failureHorizonDays: Optional[int] = None
    maintenanceRisk: Optional[str] = None
    maintenanceRecommended: Optional[bool] = None
    decisionThreshold: Optional[float] = None
    estimatedDowntime: Optional[float] = None
    estimatedDowntimeUnit: Optional[str] = None
    failureFactors: list[Any] = []
    baseRateInTraining: Optional[float] = None
    probabilityNote: Optional[str] = None
    dataQuality: Optional[Any] = None
    warnings: list[str] = []


class FullAnalysisResponse(_Header):
    currentProduction: Optional[float] = None
    predictedProduction7d: Optional[float] = None
    predictedProduction30d: Optional[float] = None
    predictedProduction90d: Optional[float] = None
    productionChangePct: Optional[float] = None
    predictionIntervals: Optional[Any] = None
    forecastVsActual: list[Any] = []
    anomalyDetected: Optional[bool] = None
    anomalyScore: Optional[float] = None
    detectedAnomalies: list[Any] = []
    riskLevel: Optional[str] = None
    riskScore: Optional[float] = None
    riskReasons: list[Any] = []
    equipmentFailureProbability: Optional[float] = None
    maintenanceRisk: Optional[str] = None
    maintenanceRecommended: Optional[bool] = None
    failureFactors: list[Any] = []
    operationalEfficiency: Optional[float] = None
    efficiencyDetails: Optional[Any] = None
    estimatedDowntime: Optional[float] = None
    indicators: Optional[Any] = None
    recommendations: list[Any] = []
    dataQuality: Optional[Any] = None
    confidence: Optional[Any] = None
    componentStatus: Optional[Any] = None
    warnings: list[str] = []


class BatchItem(_Resp):
    wellId: str
    status: str
    result: Optional[FullAnalysisResponse] = None
    error: Optional[str] = None


class BatchResponse(_Resp):
    count: int
    succeeded: int
    failed: int
    results: list[BatchItem]


class RetrainResponse(_Resp):
    status: str
    message: str
