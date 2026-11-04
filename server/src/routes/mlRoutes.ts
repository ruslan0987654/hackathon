import { Router } from 'express';
import type { Pool } from 'pg';
import { MlController } from '../controllers/mlController';
import { mlClientFromEnv } from '../ml/mlClient';
import { MlAnalysisService } from '../ml/mlService';

/**
 * İstifadə (mövcud app.ts / server.ts daxilində):
 *
 *   import { buildMlRouter } from './routes/mlRoutes';
 *   app.use('/api/ml', yourAuthMiddleware, buildMlRouter(pool));
 *
 * `yourAuthMiddleware` — layihənizdəki mövcud autentifikasiya middleware-i (JWT və s.).
 * `express.json({ limit: '1mb' })` artıq qoşulmuş olmalıdır.
 */
export function buildMlRouter(pool: Pool): Router {
  const client = mlClientFromEnv();
  const controller = new MlController(new MlAnalysisService(pool, client), client);
  const router = Router();
  router.get('/health', controller.health);
  router.post('/wells/:wellId/analyze', controller.analyzeWell); // ?days=120&save=true
  router.post('/analyze-batch', controller.analyzeBatch); // body: { "wellIds": ["W-1", "W-2"] }
  router.get('/wells/:wellId/history', controller.history); // ?limit=30
  return router;
}
