import { alerts, categoryShare, parameterTrend, productionTrend, wells } from "../data/mockData";

const API_BASE = (import.meta as ImportMeta & { env?: { VITE_API_URL?: string } }).env?.VITE_API_URL ?? "/api";

export type DashboardApiResponse = {
  source: "live" | "mock";
  summary: {
    totalProduction: number;
    analyzedWells: number;
    productionGoal: number;
    riskWells: number;
    attentionWells: number;
  };
  categoryShare: Array<{ name: string; value: number; color: string }>;
  productionTrend: Array<{ date: string; actual: number; forecast: number }>;
  parameterTrend: Array<{ date: string; pressure: number; temperature: number; production: number }>;
  alerts: Array<{ id: string; wellId: string; title: string; description: string; severity: "Yüksək" | "Orta" | "Aşağı"; time: string; acknowledged: boolean }>;
};

const fallbackDashboard: DashboardApiResponse = {
  source: "mock",
  summary: {
    totalProduction: wells.reduce((sum, well) => sum + well.production, 0),
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

async function fetchJson<T>(path: string, fallback: T): Promise<T> {
  try {
    const res = await fetch(`${API_BASE}${path}`);
    if (!res.ok) throw new Error(`Request failed: ${res.status}`);
    return (await res.json()) as T;
  } catch (error) {
    console.warn(`[api] Falling back to local data for ${path}:`, error);
    return fallback;
  }
}

export async function fetchDashboard(): Promise<DashboardApiResponse> {
  return fetchJson<DashboardApiResponse>("/dashboard", fallbackDashboard);
}

export async function fetchWells() {
  return fetchJson<{ wells: typeof wells }>("/wells", { wells });
}

export async function fetchAnalytics() {
  return fetchJson<{ productionTrend: typeof productionTrend; parameterTrend: typeof parameterTrend; categoryShare: typeof categoryShare }>("/analytics", { productionTrend, parameterTrend, categoryShare });
}

export async function fetchAlerts() {
  return fetchJson<{ alerts: typeof alerts }>("/alerts", { alerts });
}
export async function createWell(payload: Partial<{ id: string; region: string; field: string; production: number; pressure: number; temperature: number; status: string; change: number; lastUpdated: string }>) {
  const res = await fetch(`${API_BASE}/wells`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    throw new Error(`Failed to create well: ${res.status}`);
  }

  return res.json() as Promise<{ well: typeof wells[number]; created: boolean }>;
}

export async function acknowledgeAlert(alertId: string) {
  const res = await fetch(`${API_BASE}/alerts/${alertId}/acknowledge`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
  });

  if (!res.ok) {
    throw new Error(`Failed to acknowledge alert: ${res.status}`);
  }

  return res.json() as Promise<{ alertId: string; acknowledged: boolean }>;
}