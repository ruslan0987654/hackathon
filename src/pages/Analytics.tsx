import { useEffect, useState } from "react";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import PageTitle from "../components/PageTitle";
import Panel from "../components/Panel";
import { fetchAnalytics } from "../lib/api";

type AnalyticsData = {
  productionTrend: Array<{ date: string; actual: number; forecast: number }>;
  parameterTrend: Array<{ date: string; pressure: number; temperature: number; production: number }>;
  categoryShare: Array<{ name: string; value: number; color: string }>;
};

export default function Analytics({ searchQuery = "" }: { searchQuery?: string }) {
  const [parameter, setParameter] = useState("pressure");
  const [data, setData] = useState<AnalyticsData>({ productionTrend: [], parameterTrend: [], categoryShare: [] });

  useEffect(() => {
    void fetchAnalytics().then(setData);
  }, []);

  const normalizedQuery = searchQuery.trim().toLowerCase();
  const labels: Record<string, string> = { pressure: "Təzyiq", temperature: "Temperatur", production: "Hasilat" };
  const colors: Record<string, string> = { pressure: "#269bff", temperature: "#f59e0b", production: "#21c99a" };

  const filteredTrend = normalizedQuery
    ? data.parameterTrend.filter((point) => [point.date, String(point.pressure), String(point.temperature), String(point.production)].join(" ").toLowerCase().includes(normalizedQuery))
    : data.parameterTrend;

  return (
    <>
      <PageTitle title="Analitika" description="Hasilat və texniki parametrlərin zaman üzrə müqayisəli təhlili." />
      <div className="filter-bar"><span>Göstərici seçin</span>{Object.entries(labels).map(([key, label]) => <button key={key} className={`filter-chip ${parameter === key ? "active" : ""}`} onClick={() => setParameter(key)}>{label}</button>)}</div>
      <div className="analytics-grid">
        <Panel title={`${labels[parameter]} dinamikası`} subtitle={normalizedQuery ? `Axtarışa uyğun tarixlər: ${filteredTrend.length}` : "Son 30 gün üzrə nümunəvi göstəricilər"}>
          <div className="large-chart"><ResponsiveContainer width="100%" height="100%"><AreaChart data={filteredTrend}><defs><linearGradient id="paramFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={colors[parameter]} stopOpacity={0.3}/><stop offset="100%" stopColor={colors[parameter]} stopOpacity={0}/></linearGradient></defs><CartesianGrid stroke="#1d2c45" strokeDasharray="3 5" vertical={false}/><XAxis dataKey="date" tick={{ fill: "#8291aa", fontSize: 11 }} axisLine={false} tickLine={false}/><YAxis tick={{ fill: "#8291aa", fontSize: 11 }} axisLine={false} tickLine={false}/><Tooltip contentStyle={{ background: "#101d33", border: "1px solid #263956", borderRadius: 10 }}/><Area type="monotone" dataKey={parameter} name={labels[parameter]} stroke={colors[parameter]} strokeWidth={2.5} fill="url(#paramFill)"/></AreaChart></ResponsiveContainer></div>
        </Panel>
        <Panel title="Hasilat və proqnoz" subtitle="Faktiki və model nəticəsinin müqayisəsi">
          <div className="large-chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={data.productionTrend}><CartesianGrid stroke="#1d2c45" strokeDasharray="3 5" vertical={false}/><XAxis dataKey="date" tick={{ fill: "#8291aa", fontSize: 10 }} axisLine={false} tickLine={false}/><YAxis tick={{ fill: "#8291aa", fontSize: 11 }} axisLine={false} tickLine={false}/><Tooltip contentStyle={{ background: "#101d33", border: "1px solid #263956", borderRadius: 10 }}/><Legend/><Bar dataKey="actual" name="Faktiki" fill="#269bff" radius={[4,4,0,0]}/><Bar dataKey="forecast" name="Proqnoz" fill="#8b5cf6" radius={[4,4,0,0]}/></BarChart></ResponsiveContainer></div>
        </Panel>
      </div>
      <div className="info-banner"><span>i</span><div><strong>Analitik qeyd</strong><p>Qrafiklər demo məlumatlarla qurulub. Real layihədə bu göstəricilər Data Analyst-in hazırladığı API nəticələrindən gələcək.</p></div></div>
    </>
  );
}