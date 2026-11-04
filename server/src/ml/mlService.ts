import type { Pool } from 'pg';
import { MlClient } from './mlClient.js';
import type { MlFullAnalysis, MlTimeRecord, MlWellRequest } from './mlTypes.js';

/**
 * Express servis qatı: PostgreSQL-dən quyu məlumatını oxuyur -> ML servisinə göndərir -> nəticəni saxlayır.
 *
 * ⚠️ AŞAĞIDAKI SQL SORĞULARINDA CƏDVƏL/SÜTUN ADLARINI ÖZ BAZANIZA UYĞUN DƏYİŞİN
 *    (burada nümunə kimi `wells` və `well_measurements` cədvəlləri fərz edilib).
 *    Yalnız `loadWell` içindəki SELECT-lər və `toRecord` xəritələməsi dəyişməlidir.
 */

const num = (v: unknown): number | null => {
  if (v === null || v === undefined || v === '') return null;
  const n = Number(v); // pg NUMERIC dəyərləri string gəlir
  return Number.isFinite(n) ? n : null;
};
const iso = (v: unknown): string | null => (v instanceof Date ? v.toISOString() : v ? String(v) : null);
const day = (v: unknown): string | null => {
  const s = iso(v);
  return s ? s.slice(0, 10) : null;
};
const str = (v: unknown): string | null => (v === null || v === undefined ? null : String(v));

type Row = Record<string, unknown>;

function toRecord(r: Row): MlTimeRecord {
  return {
    timestamp: iso(r.ts) as string,
    production: num(r.production),
    oilProduction: num(r.oil_production),
    gasProduction: num(r.gas_production),
    waterProduction: num(r.water_production),
    pressure: num(r.pressure),
    temperature: num(r.temperature),
    bottomHolePressure: num(r.bottom_hole_pressure),
    wellheadPressure: num(r.wellhead_pressure),
    casingPressure: num(r.casing_pressure),
    tubingPressure: num(r.tubing_pressure),
    waterCut: num(r.water_cut),
    gasOilRatio: num(r.gas_oil_ratio),
    flowRate: num(r.flow_rate),
    vibration: num(r.vibration),
    equipmentTemperature: num(r.equipment_temperature),
    pumpEfficiency: num(r.pump_efficiency),
    pumpRuntime: num(r.pump_runtime),
    pumpStatus: str(r.pump_status),
    operatingHours: num(r.operating_hours),
    downtimeHours: num(r.downtime_hours),
  };
}

export class WellNotFoundError extends Error {
  constructor(wellId: string) {
    super(`Quyu tapılmadı: ${wellId}`);
    this.name = 'WellNotFoundError';
  }
}

export class MlAnalysisService {
  constructor(
    private readonly pool: Pool,
    private readonly client: MlClient,
  ) {}

  /** Quyunun statik məlumatını və son `days` günün ölçmələrini ML sorğusuna çevirir. */
  async loadWell(wellId: string, days = 120): Promise<MlWellRequest> {
    const w = await this.pool.query(
      `SELECT id, name, field_name, region, well_type, status, latitude, longitude, depth,
              drilling_date, operation_start_date, last_maintenance_date, last_inspection_date, production_target
         FROM wells WHERE id = $1`,
      [wellId],
    );
    if (w.rowCount === 0) throw new WellNotFoundError(wellId);
    const m = await this.pool.query(
      `SELECT ts, production, oil_production, gas_production, water_production, pressure, temperature,
              bottom_hole_pressure, wellhead_pressure, casing_pressure, tubing_pressure, water_cut,
              gas_oil_ratio, flow_rate, vibration, equipment_temperature, pump_efficiency, pump_runtime,
              pump_status, operating_hours, downtime_hours
         FROM well_measurements
        WHERE well_id = $1 AND ts >= now() - make_interval(days => $2::int)
        ORDER BY ts ASC`,
      [wellId, days],
    );
    const r = w.rows[0] as Row;
    return {
      wellId: String(r.id),
      wellName: str(r.name),
      fieldName: str(r.field_name),
      region: str(r.region),
      wellType: str(r.well_type),
      wellStatus: str(r.status),
      latitude: num(r.latitude),
      longitude: num(r.longitude),
      depth: num(r.depth),
      drillingDate: day(r.drilling_date),
      operationStartDate: day(r.operation_start_date),
      maintenanceDate: day(r.last_maintenance_date),
      lastInspectionDate: day(r.last_inspection_date),
      productionTarget: num(r.production_target),
      history: (m.rows as Row[]).map(toRecord),
    };
  }

  async analyzeWell(wellId: string, opts: { days?: number; save?: boolean } = {}): Promise<MlFullAnalysis> {
    const well = await this.loadWell(wellId, opts.days ?? 120);
    if (well.history.length === 0) {
      throw new Error(`Quyu ${wellId} üçün son ${opts.days ?? 120} gündə ölçmə yoxdur`);
    }
    const result = await this.client.fullAnalysis(well);
    if (opts.save !== false) await this.saveResult(result);
    return result;
  }

  async saveResult(r: MlFullAnalysis): Promise<void> {
    await this.pool.query(
      `INSERT INTO ml_analysis_results
         (well_id, analyzed_at, model_version, data_basis, current_production, predicted_production_7d,
          predicted_production_30d, predicted_production_90d, production_change_pct, anomaly_detected,
          anomaly_score, risk_level, risk_score, equipment_failure_probability, operational_efficiency,
          estimated_downtime_hours, confidence_score, data_quality_level, full_result)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19)`,
      [
        r.wellId, r.analysisTimestamp, r.modelVersion, r.dataBasis, r.currentProduction,
        r.predictedProduction7d, r.predictedProduction30d, r.predictedProduction90d, r.productionChangePct,
        r.anomalyDetected, r.anomalyScore, r.riskLevel, r.riskScore, r.equipmentFailureProbability,
        r.operationalEfficiency, r.estimatedDowntime, r.confidence?.score ?? null, r.dataQuality?.level ?? null,
        JSON.stringify(r),
      ],
    );
  }

  /** Bir neçə quyunu ardıcıl analiz edir; bir quyunun xətası digərlərini dayandırmır. */
  async analyzeMany(wellIds: string[], opts: { days?: number; save?: boolean } = {}) {
    const results: Array<{ wellId: string; status: 'ok' | 'error'; result?: MlFullAnalysis; error?: string }> = [];
    for (const id of wellIds) {
      try {
        results.push({ wellId: id, status: 'ok', result: await this.analyzeWell(id, opts) });
      } catch (e) {
        results.push({ wellId: id, status: 'error', error: (e as Error).message });
      }
    }
    return results;
  }

  async history(wellId: string, limit = 30) {
    const q = await this.pool.query(
      `SELECT id, analyzed_at, model_version, risk_level, risk_score, anomaly_detected, anomaly_score,
              equipment_failure_probability, operational_efficiency, predicted_production_30d, full_result
         FROM ml_analysis_results WHERE well_id = $1 ORDER BY analyzed_at DESC LIMIT $2`,
      [wellId, Math.min(Math.max(limit, 1), 365)],
    );
    return q.rows;
  }
}
