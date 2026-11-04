import type { Request, Response } from 'express';
import { MlServiceError, MlClient } from '../ml/mlClient.js';
import { MlAnalysisService, WellNotFoundError } from '../ml/mlService.js';

function sendError(res: Response, err: unknown): void {
  if (err instanceof WellNotFoundError) {
    res.status(404).json({ error: err.message });
  } else if (err instanceof MlServiceError) {
    if (err.status === 0 || err.status === 503) {
      res.status(503).json({ error: 'ML servisi müvəqqəti əlçatan deyil', detail: err.message });
    } else if (err.status === 422) {
      res.status(422).json({ error: 'ML servisi sorğunu rədd etdi', detail: err.detail });
    } else {
      console.error('[ML] gözlənilməz cavab:', err.status, err.detail);
      res.status(502).json({ error: 'ML servisi ilə əlaqə xətası' });
    }
  } else {
    console.error('[ML] xəta:', err);
    const message = err instanceof Error ? err.message : 'Daxili xəta';
    res.status(500).json({ error: message });
  }
}

export class MlController {
  constructor(
    private readonly service: MlAnalysisService,
    private readonly client: MlClient,
  ) {}

  health = async (_req: Request, res: Response) => {
    try {
      res.json(await this.client.health());
    } catch (e) {
      sendError(res, e);
    }
  };

  analyzeWell = async (req: Request, res: Response) => {
    try {
      const wellId = Array.isArray(req.params.wellId) ? req.params.wellId[0] : req.params.wellId;
      if (!wellId) {
        res.status(400).json({ error: 'Well id is required' });
        return;
      }
      const days = Math.min(Math.max(Number(req.query.days ?? 120) || 120, 7), 730);
      const save = req.query.save !== 'false';
      res.json(await this.service.analyzeWell(wellId, { days, save }));
    } catch (e) {
      sendError(res, e);
    }
  };

  analyzeBatch = async (req: Request, res: Response) => {
    try {
      const ids: unknown = req.body?.wellIds;
      if (!Array.isArray(ids) || ids.length === 0 || ids.length > 50 || !ids.every((x) => typeof x === 'string')) {
        res.status(400).json({ error: 'wellIds: 1-50 uzunluqlu string massivi olmalıdır' });
        return;
      }
      res.json(await this.service.analyzeMany(ids as string[], { save: req.query.save !== 'false' }));
    } catch (e) {
      sendError(res, e);
    }
  };

  history = async (req: Request, res: Response) => {
    try {
      const wellId = Array.isArray(req.params.wellId) ? req.params.wellId[0] : req.params.wellId;
      if (!wellId) {
        res.status(400).json({ error: 'Well id is required' });
        return;
      }
      res.json(await this.service.history(wellId, Number(req.query.limit ?? 30)));
    } catch (e) {
      sendError(res, e);
    }
  };
}
