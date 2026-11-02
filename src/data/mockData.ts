import type { AlertItem, Well } from "../types";

export const wells: Well[] = [
  { id: "Q-1023", region: "Abşeron", field: "Neft Daşları", production: 286, pressure: 142, temperature: 68, status: "Normal", change: 4.8, lastUpdated: "09:42" },
  { id: "Q-0876", region: "Bakı", field: "Bibiheybət", production: 174, pressure: 118, temperature: 72, status: "Diqqət", change: -12.4, lastUpdated: "09:38" },
  { id: "Q-1154", region: "Abşeron", field: "Günəşli", production: 92, pressure: 86, temperature: 81, status: "Riskli", change: -28.0, lastUpdated: "09:35" },
  { id: "Q-0942", region: "Şirvan", field: "Kürsəngi", production: 312, pressure: 156, temperature: 64, status: "Normal", change: 7.2, lastUpdated: "09:31" },
  { id: "Q-1208", region: "Abşeron", field: "Çıraq", production: 241, pressure: 133, temperature: 69, status: "Normal", change: 2.1, lastUpdated: "09:29" },
  { id: "Q-0761", region: "Bakı", field: "Bibiheybət", production: 108, pressure: 94, temperature: 77, status: "Diqqət", change: -9.6, lastUpdated: "09:24" },
  { id: "Q-1102", region: "Şirvan", field: "Mişovdağ", production: 198, pressure: 121, temperature: 70, status: "Normal", change: 3.5, lastUpdated: "09:20" },
  { id: "Q-0991", region: "Abşeron", field: "Neft Daşları", production: 74, pressure: 79, temperature: 83, status: "Riskli", change: -31.2, lastUpdated: "09:16" },
  { id: "Q-0834", region: "Şirvan", field: "Kürsəngi", production: 221, pressure: 139, temperature: 66, status: "Normal", change: 5.1, lastUpdated: "09:12" },
  { id: "Q-1055", region: "Bakı", field: "Bibiheybət", production: 153, pressure: 105, temperature: 75, status: "Diqqət", change: -6.8, lastUpdated: "09:08" },
];

export const productionTrend = [
  { date: "01 Noy", actual: 68, forecast: 70 },
  { date: "04 Noy", actual: 72, forecast: 72 },
  { date: "07 Noy", actual: 69, forecast: 74 },
  { date: "10 Noy", actual: 81, forecast: 76 },
  { date: "13 Noy", actual: 88, forecast: 79 },
  { date: "16 Noy", actual: 84, forecast: 82 },
  { date: "19 Noy", actual: 94, forecast: 85 },
  { date: "22 Noy", actual: 91, forecast: 88 },
  { date: "25 Noy", actual: 103, forecast: 91 },
  { date: "28 Noy", actual: 108, forecast: 94 },
  { date: "30 Noy", actual: 112, forecast: 98 },
];

export const parameterTrend = [
  { date: "01 Noy", pressure: 132, temperature: 65, production: 82 },
  { date: "05 Noy", pressure: 136, temperature: 67, production: 88 },
  { date: "09 Noy", pressure: 129, temperature: 66, production: 84 },
  { date: "13 Noy", pressure: 141, temperature: 69, production: 93 },
  { date: "17 Noy", pressure: 138, temperature: 70, production: 90 },
  { date: "21 Noy", pressure: 145, temperature: 68, production: 98 },
  { date: "25 Noy", pressure: 142, temperature: 71, production: 103 },
  { date: "30 Noy", pressure: 149, temperature: 69, production: 108 },
];

export const alerts: AlertItem[] = [
  { id: "AL-204", wellId: "Q-1154", title: "Hasilatda əhəmiyyətli azalma", description: "Son 7 gündə hasilat 28% azalıb. Təzyiq göstəricisi də normadan aşağıdır.", severity: "Yüksək", time: "12 dəq əvvəl", acknowledged: false },
  { id: "AL-203", wellId: "Q-0991", title: "Aşağı təzyiq anomaliyası", description: "Quyuda təzyiq son ölçmələrlə müqayisədə davamlı azalma göstərir.", severity: "Yüksək", time: "38 dəq əvvəl", acknowledged: false },
  { id: "AL-202", wellId: "Q-0876", title: "Hasilat trendində dəyişiklik", description: "Hasilat göstəricisi əvvəlki 30 günlük orta göstəricidən aşağıdır.", severity: "Orta", time: "1 saat əvvəl", acknowledged: false },
  { id: "AL-201", wellId: "Q-0761", title: "Temperatur artımı", description: "Temperatur 77 °C qeydə alınıb. Növbəti ölçmələrdə izlənilməsi tövsiyə olunur.", severity: "Aşağı", time: "3 saat əvvəl", acknowledged: true },
];

export const categoryShare = [
  { name: "Neft", value: 62, color: "#269bff" },
  { name: "Qaz", value: 28, color: "#8b5cf6" },
  { name: "Digər", value: 10, color: "#f59e0b" },
];