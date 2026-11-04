import type { MlBatchResponse, MlFullAnalysis, MlHealth, MlWellRequest } from './mlTypes';

/** ML servisi ilə əlaqə xətası. `status` HTTP kodudur (şəbəkə/timeout xətasında 0). */
export class MlServiceError extends Error {
  public readonly status: number;
  public readonly detail?: unknown;

  constructor(message: string, status: number, detail?: unknown) {
    super(message);
    this.name = 'MlServiceError';
    this.status = status;
    this.detail = detail;
  }
}

export interface MlClientOptions {
  baseUrl: string;
  apiKey: string;
  timeoutMs?: number;
  retries?: number;
}

const RETRYABLE = [502, 503, 504];

/** Node 18+ daxili fetch istifadə edir (əlavə paket tələb olunmur). */
export class MlClient {
  private readonly baseUrl: string;
  private readonly apiKey: string;
  private readonly timeoutMs: number;
  private readonly retries: number;

  constructor(opts: MlClientOptions) {
    this.baseUrl = opts.baseUrl.replace(/\/+$/, '');
    this.apiKey = opts.apiKey;
    this.timeoutMs = opts.timeoutMs ?? 30000;
    this.retries = Math.max(0, opts.retries ?? 1);
  }

  health(): Promise<MlHealth> {
    return this.request<MlHealth>('GET', '/health', undefined, false);
  }

  fullAnalysis(well: MlWellRequest): Promise<MlFullAnalysis> {
    return this.request<MlFullAnalysis>('POST', '/predict/full-analysis', well);
  }

  batch(wells: MlWellRequest[]): Promise<MlBatchResponse> {
    return this.request<MlBatchResponse>('POST', '/predict/batch', { wells });
  }

  predict<T = unknown>(kind: 'production' | 'anomaly' | 'risk' | 'equipment', well: MlWellRequest): Promise<T> {
    return this.request<T>('POST', `/predict/${kind}`, well);
  }

  private async request<T>(method: 'GET' | 'POST', path: string, body?: unknown, auth = true): Promise<T> {
    let lastError: MlServiceError | undefined;
    for (let attempt = 0; attempt <= this.retries; attempt++) {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), this.timeoutMs);
      try {
        const res = await fetch(`${this.baseUrl}${path}`, {
          method,
          headers: { 'Content-Type': 'application/json', ...(auth ? { 'X-API-Key': this.apiKey } : {}) },
          body: body === undefined ? undefined : JSON.stringify(body),
          signal: controller.signal,
        });
        const text = await res.text();
        let json: unknown;
        try {
          json = text ? JSON.parse(text) : undefined;
        } catch {
          json = undefined; // JSON olmayan cavab
        }
        if (res.ok) return json as T;
        const detail = (json as { detail?: unknown } | undefined)?.detail ?? text;
        lastError = new MlServiceError(`ML servisi ${res.status} qaytardı`, res.status, detail);
        // Yalnız müvəqqəti xətalarda (502/503/504) təkrar cəhd edilir; 4xx xətaları təkrarlanmır.
        if (!RETRYABLE.includes(res.status)) throw lastError;
      } catch (err) {
        if (err instanceof MlServiceError) {
          if (!RETRYABLE.includes(err.status)) throw err;
          lastError = err;
        } else if ((err as Error).name === 'AbortError') {
          lastError = new MlServiceError(`ML servisi ${this.timeoutMs} ms ərzində cavab vermədi`, 0);
        } else {
          lastError = new MlServiceError(`ML servisinə qoşulmaq mümkün olmadı: ${(err as Error).message}`, 0);
        }
      } finally {
        clearTimeout(timer);
      }
      if (attempt < this.retries) await new Promise((r) => setTimeout(r, 500 * (attempt + 1)));
    }
    throw lastError ?? new MlServiceError('Naməlum ML xətası', 0);
  }
}

export function mlClientFromEnv(env: NodeJS.ProcessEnv = process.env): MlClient {
  const baseUrl = env.ML_SERVICE_URL;
  const apiKey = env.ML_SERVICE_API_KEY;
  if (!baseUrl || !apiKey) {
    throw new Error('ML_SERVICE_URL və ML_SERVICE_API_KEY .env faylında təyin edilməlidir.');
  }
  return new MlClient({
    baseUrl,
    apiKey,
    timeoutMs: Number(env.ML_SERVICE_TIMEOUT_MS ?? 30000),
    retries: Number(env.ML_SERVICE_RETRIES ?? 1),
  });
}
