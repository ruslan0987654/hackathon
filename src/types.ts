export type PageKey = "dashboard" | "wells" | "analytics" | "insights" | "alerts";

export type WellStatus = "Normal" | "Diqqət" | "Riskli";

export interface Well {
  id: string;
  region: string;
  field: string;
  production: number;
  pressure: number;
  temperature: number;
  status: WellStatus;
  change: number;
  lastUpdated: string;
}

export interface AlertItem {
  id: string;
  wellId: string;
  title: string;
  description: string;
  severity: "Yüksək" | "Orta" | "Aşağı";
  time: string;
  acknowledged: boolean;
}