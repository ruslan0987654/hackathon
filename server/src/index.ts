import cors from 'cors';
import dotenv from 'dotenv';
import express from 'express';
import { MlClient } from './ml/mlClient.js';

dotenv.config();

const app = express();
const port = Number(process.env.PORT ?? 3001);

app.use(cors({ origin: true, credentials: true }));
app.use(express.json({ limit: '1mb' }));

const mockWells = [
  { id: 'Q-1023', region: 'Abşeron', field: 'Neft Daşları', production: 286, pressure: 142, temperature: 68, status: 'Normal', change: 4.8, lastUpdated: '09:42' },
  { id: 'Q-0876', region: 'Bakı', field: 'Bibiheybət', production: 174, pressure: 118, temperature: 72, status: 'Diqqət', change: -12.4, lastUpdated: '09:38' },
  { id: 'Q-1154', region: 'Abşeron', field: 'Günəşli', production: 92, pressure: 86, temperature: 81, status: 'Riskli', change: -28.0, lastUpdated: '09:35' },
  { id: 'Q-0942', region: 'Şirvan', field: 'Kürsəngi', production: 312, pressure: 156, temperature: 64, status: 'Normal', change: 7.2, lastUpdated: '09:31' },
  { id: 'Q-1208', region: 'Abşeron', field: 'Çıraq', production: 241, pressure: 133, temperature: 69, status: 'Normal', change: 2.1, lastUpdated: '09:29' },
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

const alerts = [
  { id: 'AL-204', wellId: 'Q-1154', title: 'Hasilatda əhəmiyyətli azalma', description: 'Son 7 gündə hasilat 28% azalıb. Təzyiq göstəricisi də normadan aşağıdır.', severity: 'Yüksək', time: '12 dəq əvvəl', acknowledged: false },
  { id: 'AL-203', wellId: 'Q-0876', title: 'Aşağı təzyiq anomaliyası', description: 'Quyuda təzyiq son ölçmələrlə müqayisədə davamlı azalma göstərir.', severity: 'Yüksək', time: '38 dəq əvvəl', acknowledged: false },
];

const mlClient = process.env.ML_SERVICE_URL && process.env.ML_SERVICE_API_KEY
  ? new MlClient({
      baseUrl: process.env.ML_SERVICE_URL,
      apiKey: process.env.ML_SERVICE_API_KEY,
      timeoutMs: Number(process.env.ML_SERVICE_TIMEOUT_MS ?? 30000),
      retries: Number(process.env.ML_SERVICE_RETRIES ?? 1),
    })
  : null;

function buildDashboard() {
  const totalProduction = mockWells.reduce((sum, well) => sum + well.production, 0);
  return {
    source: mlClient ? 'live' : 'mock',
    summary: {
      totalProduction,
      analyzedWells: 124,
      productionGoal: 482.75,
      riskWells: 3,
      attentionWells: 9,
    },
    categoryShare,
    productionTrend,
    parameterTrend,
    alerts,
  };
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
  res.json({ wells: mockWells });
});

app.get('/api/dashboard', (_req, res) => {
  res.json(buildDashboard());
});

app.get('/api/analytics', (_req, res) => {
  res.json({ productionTrend, parameterTrend, categoryShare });
});

app.get('/api/alerts', (_req, res) => {
  res.json({ alerts });
});

app.post('/api/ml/wells/:wellId/analyze', async (req, res) => {
  const { wellId } = req.params;

  if (!mlClient) {
    return res.json({
      status: 'mock',
      wellId,
      message: 'ML service is not configured; returning fallback data.',
      data: buildDashboard(),
    });
  }

  try {
    const payload = {
      wellId,
      history: mockWells[0] ? [
        { timestamp: '2026-10-01T00:00:00Z', production: 280, pressure: 145, temperature: 70, waterCut: 8, pumpEfficiency: 92 },
        { timestamp: '2026-10-02T00:00:00Z', production: 274, pressure: 142, temperature: 71, waterCut: 9, pumpEfficiency: 91 },
        { timestamp: '2026-10-03T00:00:00Z', production: 268, pressure: 141, temperature: 72, waterCut: 10, pumpEfficiency: 88 },
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
