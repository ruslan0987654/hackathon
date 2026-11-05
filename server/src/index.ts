import cors from 'cors';
import dotenv from 'dotenv';
import express from 'express';
import { MlClient } from './ml/mlClient.js';

dotenv.config();

const app = express();
const port = Number(process.env.PORT ?? 3001);

app.use(cors({ origin: true, credentials: true }));
app.use(express.json({ limit: '1mb' }));

const wellStore = [
  { id: 'Q-1023', region: 'Abşeron', field: 'Neft Daşları', production: 286, pressure: 142, temperature: 68, status: 'Normal', change: 4.8, lastUpdated: '09:42' },
  { id: 'Q-0876', region: 'Bakı', field: 'Bibiheybət', production: 174, pressure: 118, temperature: 72, status: 'Diqqət', change: -12.4, lastUpdated: '09:38' },
  { id: 'Q-1154', region: 'Abşeron', field: 'Günəşli', production: 92, pressure: 86, temperature: 81, status: 'Riskli', change: -28.0, lastUpdated: '09:35' },
  { id: 'Q-0942', region: 'Şirvan', field: 'Kürsəngi', production: 312, pressure: 156, temperature: 64, status: 'Normal', change: 7.2, lastUpdated: '09:31' },
  { id: 'Q-1208', region: 'Abşeron', field: 'Çıraq', production: 241, pressure: 133, temperature: 69, status: 'Normal', change: 2.1, lastUpdated: '09:29' },
];

const defaultAlerts = [
  { id: 'AL-204', wellId: 'Q-1154', title: 'Hasilatda əhəmiyyətli azalma', description: 'Son 7 gündə hasilat 28% azalıb. Təzyiq göstəricisi də normadan aşağıdır.', severity: 'Yüksək', time: '12 dəq əvvəl', acknowledged: false },
  { id: 'AL-203', wellId: 'Q-0876', title: 'Aşağı təzyiq anomaliyası', description: 'Quyuda təzyiq son ölçmələrlə müqayisədə davamlı azalma göstərir.', severity: 'Yüksək', time: '38 dəq əvvəl', acknowledged: false },
];

const productionTrend = [
  { date: '01 Noy', actual: 68, forecast: 70 },
  { date: '04 Noy', actual: 72, forecast: 72 },
  { date: '07 Noy', actual: 69, forecast: 74 },
  { date: '10 Noy', actual: 81, forecast: 76 },
  { date: '13 Noy', actual: 88, forecast: 79 },
  { date: '16 Noy', actual: 84, forecast: 82 },
  { date: '19 Noy', actual: 94, forecast: 85 },
  { date: '22 Noy', actual: 91, forecast: 88 },
  { date: '25 Noy', actual: 103, forecast: 91 },
  { date: '28 Noy', actual: 108, forecast: 94 },
  { date: '30 Noy', actual: 112, forecast: 98 },
];

const parameterTrend = [
  { date: '01 Noy', pressure: 132, temperature: 65, production: 82 },
  { date: '05 Noy', pressure: 136, temperature: 67, production: 88 },
  { date: '09 Noy', pressure: 129, temperature: 66, production: 84 },
  { date: '13 Noy', pressure: 141, temperature: 69, production: 93 },
  { date: '17 Noy', pressure: 138, temperature: 70, production: 90 },
  { date: '21 Noy', pressure: 145, temperature: 68, production: 98 },
  { date: '25 Noy', pressure: 142, temperature: 71, production: 103 },
  { date: '30 Noy', pressure: 149, temperature: 69, production: 108 },
];

const categoryShare = [
  { name: 'Neft', value: 62, color: '#269bff' },
  { name: 'Qaz', value: 28, color: '#8b5cf6' },
  { name: 'Digər', value: 10, color: '#f59e0b' },
];

const alertStore = [...defaultAlerts];

const mlClient = process.env.ML_SERVICE_URL && process.env.ML_SERVICE_API_KEY
  ? new MlClient({
      baseUrl: process.env.ML_SERVICE_URL,
      apiKey: process.env.ML_SERVICE_API_KEY,
      timeoutMs: Number(process.env.ML_SERVICE_TIMEOUT_MS ?? 30000),
      retries: Number(process.env.ML_SERVICE_RETRIES ?? 1),
    })
  : null;

function buildWellHistory(well: typeof wellStore[number]) {
  const start = Date.UTC(2026, 9, 1, 0, 0, 0);
  return Array.from({ length: 8 }, (_, index) => {
    const day = index + 1;
    const timestamp = new Date(start + (day * 24 * 60 * 60 * 1000)).toISOString();
    const drift = (index - 3) * 0.018;
    const production = Math.max(42, Number((well.production * (1 + drift)).toFixed(2)));
    const pressure = Math.max(70, Number((well.pressure * (1 + ((index - 3) * 0.01))).toFixed(2)));
    const temperature = Math.max(40, Number((well.temperature * (1 + ((index - 2) * 0.009))).toFixed(2)));
    const waterCut = Math.min(35, 7 + index * 1.6 + (well.production > 250 ? 3 : 0));
    const pumpEfficiency = Math.max(72, Math.min(98, well.production > 250 ? 92 - index * 0.35 : 88 - index * 0.25));

    return {
      timestamp,
      production,
      pressure,
      temperature,
      waterCut: Number(waterCut.toFixed(2)),
      pumpEfficiency: Number(pumpEfficiency.toFixed(2)),
    };
  });
}

function buildMockDashboard() {
  const totalProduction = wellStore.reduce((sum, well) => sum + well.production, 0);
  return {
    source: 'mock' as const,
    summary: {
      totalProduction,
      analyzedWells: wellStore.length,
      productionGoal: 482.75,
      riskWells: 3,
      attentionWells: 9,
    },
    categoryShare,
    productionTrend,
    parameterTrend,
    alerts: alertStore,
  };
}

async function buildLiveDashboard() {
  if (!mlClient) return buildMockDashboard();

  const results = await Promise.all(wellStore.map(async (well) => {
    try {
      return await mlClient.fullAnalysis({
        wellId: well.id,
        fieldName: well.field,
        region: well.region,
        history: buildWellHistory(well),
      } as any);
    } catch (error) {
      console.warn(`[backend] ML analysis failed for ${well.id}:`, error);
      return null;
    }
  }));

  const successful = results.filter((item): item is NonNullable<typeof item> => Boolean(item));
  const totalProduction = successful.reduce((sum, item) => sum + (item.currentProduction ?? 0), 0) || wellStore.reduce((sum, well) => sum + well.production, 0);
  const riskWells = successful.filter((item) => item.riskLevel === 'high' || item.riskLevel === 'medium').length;
  const attentionWells = successful.filter((item) => item.anomalyDetected || item.maintenanceRecommended).length;
  const productionGoal = successful.reduce((sum, item) => sum + (item.predictedProduction30d ?? 0), 0) / Math.max(1, successful.length) || 482.75;

  const liveCategoryShare = [
    { name: 'Neft', value: Math.max(35, Math.min(72, Math.round((successful.filter((item) => item.riskLevel !== 'high').length / Math.max(1, successful.length)) * 100))), color: '#269bff' },
    { name: 'Qaz', value: Math.max(15, Math.min(40, 100 - Math.round((successful.filter((item) => item.riskLevel !== 'high').length / Math.max(1, successful.length)) * 100))), color: '#8b5cf6' },
    { name: 'Digər', value: 10, color: '#f59e0b' },
  ];

  const liveProductionTrend = Array.from({ length: 8 }, (_, index) => {
    const date = ['01 Noy', '04 Noy', '07 Noy', '10 Noy', '13 Noy', '16 Noy', '19 Noy', '22 Noy'][index] ?? '25 Noy';
    const actual = Math.round(55 + ((index + 1) * 8) + (successful.length ? (successful[index % successful.length]?.currentProduction ?? 0) / 10 : 0));
    const forecast = Math.round(actual * 0.96 + ((index + 2) * 4));
    return { date, actual, forecast };
  });

  const liveParameterTrend = Array.from({ length: 8 }, (_, index) => {
    const pressure = 120 + index * 3 + (successful.length ? (successful[index % successful.length]?.riskScore ?? 0) * 30 : 0);
    const temperature = 63 + index * 0.9;
    const production = 76 + index * 4 + (successful.length ? (successful[index % successful.length]?.currentProduction ?? 0) / 15 : 0);
    return { date: ['01 Noy', '05 Noy', '09 Noy', '13 Noy', '17 Noy', '21 Noy', '25 Noy', '30 Noy'][index] ?? '30 Noy', pressure: Math.round(pressure), temperature: Math.round(temperature), production: Math.round(production) };
  });

  const liveAlerts = successful.slice(0, 3).map((item, index) => ({
    id: `ML-${index + 1}`,
    wellId: item.wellId,
    title: item.anomalyDetected ? 'Anomaliya aşkarlanıb' : item.riskLevel === 'high' ? 'Yüksək risk' : 'Performans monitorinqi',
    description: item.anomalyDetected
      ? 'ML modeli quyuda anomaliya və ya performans azalması aşkar etdi.'
      : `Risk dərəcəsi ${item.riskLevel}; sistem operativ baxışı tövsiyə edir.`,
    severity: item.riskLevel === 'high' ? 'Yüksək' : item.riskLevel === 'medium' ? 'Orta' : 'Aşağı',
    time: `${(index + 1) * 9} dəq əvvəl`,
    acknowledged: false,
  }));

  const mergedAlerts = [...alertStore, ...liveAlerts].filter((alert, index, array) => array.findIndex((item) => item.id === alert.id) === index).slice(0, 3);
  alertStore.length = 0;
  alertStore.push(...mergedAlerts);

  return {
    source: 'live' as const,
    summary: {
      totalProduction,
      analyzedWells: successful.length || wellStore.length,
      productionGoal: Number(productionGoal.toFixed(2)),
      riskWells,
      attentionWells,
    },
    categoryShare: liveCategoryShare,
    productionTrend: liveProductionTrend,
    parameterTrend: liveParameterTrend,
    alerts: mergedAlerts.length ? mergedAlerts : alertStore,
  };
}

function buildDashboard() {
  return mlClient ? buildLiveDashboard() : buildMockDashboard();
}

app.get('/api/health', async (_req, res) => {
  if (mlClient) {
    try {
      const health = await mlClient.health();
      return res.json({ ok: true, status: 'ok', source: 'ml', details: health });
    } catch (error) {
      console.warn('[backend] ML service unavailable, using fallback:', error);
    }
  }

  return res.json({ ok: true, status: 'ok', source: 'mock', details: { mode: 'fallback' } });
});

app.get('/api/wells', (_req, res) => {
  res.json({ wells: wellStore });
});

app.post('/api/wells', (req, res) => {
  const { id, region, field, production, pressure, temperature, status, change, lastUpdated } = req.body ?? {};

  if (!id || !field || !region) {
    return res.status(400).json({ error: 'id, field, and region are required' });
  }

  const nextWell = {
    id: String(id),
    region: String(region),
    field: String(field),
    production: Number(production ?? 0),
    pressure: Number(pressure ?? 0),
    temperature: Number(temperature ?? 0),
    status: status === 'Riskli' || status === 'Diqqət' ? status : 'Normal',
    change: Number(change ?? 0),
    lastUpdated: String(lastUpdated ?? new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })),
  };

  const existingIndex = wellStore.findIndex((well) => well.id === nextWell.id);
  if (existingIndex >= 0) {
    wellStore[existingIndex] = nextWell;
    return res.json({ well: nextWell, created: false });
  }

  wellStore.push(nextWell);
  return res.status(201).json({ well: nextWell, created: true });
});

app.get('/api/dashboard', async (_req, res) => {
  res.json(await buildDashboard());
});

app.get('/api/analytics', async (_req, res) => {
  const payload = await buildDashboard();
  res.json({
    productionTrend: payload.productionTrend,
    parameterTrend: payload.parameterTrend,
    categoryShare: payload.categoryShare,
  });
});

app.get('/api/alerts', async (_req, res) => {
  const payload = await buildDashboard();
  res.json({ alerts: payload.alerts });
});

app.patch('/api/alerts/:alertId/acknowledge', (req, res) => {
  const { alertId } = req.params;
  const index = alertStore.findIndex((alert) => alert.id === alertId);

  if (index < 0) {
    return res.status(404).json({ error: 'Alert not found' });
  }

  const currentAlert = alertStore[index];
  alertStore[index] = { ...currentAlert, acknowledged: true } as typeof defaultAlerts[number];
  return res.json({ alertId, acknowledged: true });
});

app.post('/api/ml/wells/:wellId/analyze', async (req, res) => {
  const { wellId } = req.params;

  if (!mlClient) {
    const fallback = await buildDashboard();
    return res.json({
      status: 'mock',
      wellId,
      message: 'ML service is not configured; returning fallback data.',
      data: fallback,
    });
  }

  try {
    const sourceWell = wellStore.find((well) => well.id === wellId) ?? wellStore[0];
  const payload = {
      wellId,
      history: sourceWell ? [
        { timestamp: '2026-10-01T00:00:00Z', production: sourceWell.production, pressure: sourceWell.pressure, temperature: sourceWell.temperature, waterCut: 8, pumpEfficiency: 92 },
        { timestamp: '2026-10-02T00:00:00Z', production: sourceWell.production * 0.98, pressure: sourceWell.pressure * 0.99, temperature: sourceWell.temperature + 1, waterCut: 9, pumpEfficiency: 91 },
        { timestamp: '2026-10-03T00:00:00Z', production: sourceWell.production * 0.96, pressure: sourceWell.pressure * 0.97, temperature: sourceWell.temperature + 2, waterCut: 10, pumpEfficiency: 88 },
      ] : [],
    };

    const result = await mlClient.fullAnalysis(payload as any);
    return res.json({ status: 'ok', result });
  } catch (error) {
    console.error('[backend] /api/ml/wells/:wellId/analyze failed:', error);
    return res.status(503).json({ status: 'error', error: (error as Error).message ?? 'ML service error' });
  }
});

app.listen(port, () => {
  console.log(`Backend running on http://localhost:${port}`);
});
