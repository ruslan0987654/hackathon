/**
 * ML servisi ilə sorğu/cavab tipləri.
 * Sahələr ml-service README-dəki sxemə uyğundur. Bütün ölçmələr ixtiyaridir:
 * məlumat yoxdursa sahəni göndərməyin və ya null verin (uydurma dəyər YAZMAYIN).
 */

export interface MlTimeRecord {
  timestamp: string; // ISO 8601, məs. "2026-10-31T00:00:00Z"
  production?: number | null;
  oilProduction?: number | null;
  gasProduction?: number | null;
  waterProduction?: number | null;
  pressure?: number | null;
  temperature?: number | null;
  bottomHolePressure?: number | null;
  wellheadPressure?: number | null;
  casingPressure?: number | null;
  tubingPressure?: number | null;
  waterCut?: number | null; // % (0-100)
  gasOilRatio?: number | null;
  flowRate?: number | null;
  vibration?: number | null;
  equipmentTemperature?: number | null;
  pumpEfficiency?: number | null; // % (0-100)
  pumpRuntime?: number | null; // saat/gün (0-24)
  pumpStatus?: string | null; // running | stopped | fault
  operatingHours?: number | null; // 0-24
  downtimeHours?: number | null; // 0-24
}

export interface MlWellRequest {
  wellId: string;
  wellName?: string | null;
  fieldName?: string | null;
  region?: string | null;
  wellType?: string | null; // oil | gas | oil_gas | gas_condensate
  wellStatus?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  depth?: number | null;
  drillingDate?: string | null; // YYYY-MM-DD
  operationStartDate?: string | null;
  maintenanceDate?: string | null;
  lastInspectionDate?: string | null;
  productionTarget?: number | null;
  history: MlTimeRecord[]; // ən azı 1 qeyd; tövsiyə: ≥ 90 gün
}

export type RiskLevel = 'low' | 'medium' | 'high';
export type ComponentStatus = 'ok' | 'insufficient_data' | 'insufficient_sensor_data' | 'error';

export interface MlConfidence {
  score: number;
  level: 'low' | 'medium' | 'high';
  basis: string;
}

export interface MlDetectedAnomaly {
  parameter: string;
  label: string;
  value: number;
  expectedValue: number;
  zScore: number;
  direction: 'high' | 'low';
  basis: 'well_history' | 'population';
  severity: 'medium' | 'high';
}

export interface MlReason {
  feature: string;
  label: string;
  value: number;
  typicalValue: number;
  zScore: number;
  importanceWeight: number;
  text: string;
}

export interface MlRecommendation {
  id: string;
  category: string;
  priority: 'low' | 'medium' | 'high';
  text: string;
  reason: string;
  evidence: Record<string, unknown>;
  confidence: { score: number; level: 'low' | 'medium' | 'high' };
  requiresEngineerReview: true;
}

export interface MlDataQuality {
  level: 'good' | 'fair' | 'poor';
  completenessPct: number;
  missingFields: string[];
  recordCount: number;
  recordsLast30d: number;
  historyDays: number;
  dataAgeDays: number;
  warnings: string[];
}

/** /predict/full-analysis cavabı. null = hesablanmayıb (saxta rəqəm qaytarılmır). */
export interface MlFullAnalysis {
  wellId: string;
  analysisTimestamp: string;
  modelVersion: string;
  dataBasis: 'synthetic' | 'real' | string;
  currentProduction: number | null;
  predictedProduction7d: number | null;
  predictedProduction30d: number | null;
  predictedProduction90d: number | null;
  productionChangePct: number | null;
  predictionIntervals: Record<string, { lower: number; upper: number; level: number }> | null;
  forecastVsActual: Array<{
    horizonDays: number;
    forecastMadeAt: string;
    windowEnd: string;
    predictedAvgDailyProduction: number;
    actualAvgDailyProduction: number;
    errorPct: number | null;
    withinInterval: boolean;
  }>;
  anomalyDetected: boolean | null;
  anomalyScore: number | null;
  detectedAnomalies: MlDetectedAnomaly[];
  riskLevel: RiskLevel | null;
  riskScore: number | null;
  riskReasons: MlReason[];
  equipmentFailureProbability: number | null;
  maintenanceRisk: RiskLevel | null;
  maintenanceRecommended: boolean | null;
  failureFactors: MlReason[];
  operationalEfficiency: number | null;
  efficiencyDetails: Record<string, unknown> | null;
  estimatedDowntime: number | null; // saat, növbəti 30 gün
  indicators: Record<string, unknown>;
  recommendations: MlRecommendation[];
  dataQuality: MlDataQuality;
  confidence: MlConfidence;
  componentStatus: Record<'production' | 'anomaly' | 'risk' | 'equipment' | 'efficiency', ComponentStatus | null>;
  warnings: string[];
}

export interface MlBatchResponse {
  count: number;
  succeeded: number;
  failed: number;
  results: Array<{ wellId: string; status: 'ok' | 'error'; result?: MlFullAnalysis; error?: string }>;
}

export interface MlHealth {
  status: 'ok' | 'degraded';
  modelsLoaded: boolean;
  modelVersion?: string | null;
}
