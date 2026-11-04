-- ML analiz nəticələrinin tarixçəsi (PostgreSQL)
-- İcra: psql -U <istifadəçi> -d <baza> -f sql/001_ml_analysis_results.sql
CREATE TABLE IF NOT EXISTS ml_analysis_results (
    id                              BIGSERIAL PRIMARY KEY,
    well_id                         TEXT        NOT NULL,
    analyzed_at                     TIMESTAMPTZ NOT NULL,
    model_version                   TEXT        NOT NULL,
    data_basis                      TEXT        NOT NULL,            -- 'synthetic' | 'real'
    current_production              NUMERIC,
    predicted_production_7d         NUMERIC,
    predicted_production_30d        NUMERIC,
    predicted_production_90d        NUMERIC,
    production_change_pct            NUMERIC,
    anomaly_detected                BOOLEAN,
    anomaly_score                   NUMERIC,
    risk_level                      TEXT CHECK (risk_level IN ('low', 'medium', 'high')),
    risk_score                      NUMERIC,
    equipment_failure_probability   NUMERIC,
    operational_efficiency          NUMERIC,
    estimated_downtime_hours        NUMERIC,
    confidence_score                NUMERIC,
    data_quality_level              TEXT,
    full_result                     JSONB       NOT NULL,            -- tam cavab (tövsiyələr, səbəblər, interval və s.)
    created_at                      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ml_results_well_time ON ml_analysis_results (well_id, analyzed_at DESC);
CREATE INDEX IF NOT EXISTS idx_ml_results_risk ON ml_analysis_results (risk_level, analyzed_at DESC);
