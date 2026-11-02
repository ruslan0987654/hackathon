import { useState } from "react";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import PageTitle from "../components/PageTitle";
import Panel from "../components/Panel";
import { parameterTrend, productionTrend } from "../data/mockData";

export default function Analytics() {
  const [parameter, setParameter] = useState("pressure");
  const labels: Record<string, string> = { pressure: "Təzyiq", temperature: "Temperatur", production: "Hasilat" };
  const colors: Record<string, string> = { pressure: "#269bff", temperature: "#f59e0b", production: "#21c99a" };
  return (
    <>
      <PageTitle title="Analitika" description="Hasilat və texniki parametrlərin zaman üzrə müqayisəli təhlili." />
      <div className="filter-bar"><span>Göstərici seçin</span>{Object.entries(labels).map(([key, label]) => <button key={key} className={`filter-chip ${parameter === key ? "active" : ""}`} onClick={() => setParameter(key)}>{label}</button>)}</div>
      <div className="analytics-grid">
        <Panel title={`${labels[parameter]} dinamikası`} subtitle="Son 30 gün üzrə nümunəvi göstəricilər">
          <div className="large-chart"><ResponsiveContainer width="100%" height="100%"><AreaChart data={parameterTrend}><defs><linearGradient id="paramFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={colors[parameter]} stopOpacity={0.3}/><stop offset="100%" stopColor={colors[parameter]} stopOpacity={0}/></linearGradient></defs><CartesianGrid stroke="#1d2c45" strokeDasharray="3 5" vertical={false}/><XAxis dataKey="date" tick={{ fill: "#8291aa", fontSize: 11 }} axisLine={false} tickLine={false}/><YAxis tick={{ fill: "#8291aa", fontSize: 11 }} axisLine={false} tickLine={false}/><Tooltip contentStyle={{ background: "#101d33", border: "1px solid #263956", borderRadius: 10 }}/><Area type="monotone" dataKey={parameter} name={labels[parameter]} stroke={colors[parameter]} strokeWidth={2.5} fill="url(#paramFill)"/></AreaChart></ResponsiveContainer></div>
        </Panel>
        <Panel title="Hasilat və proqnoz" subtitle="Faktiki və model nəticəsinin müqayisəsi">
          <div className="large-chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={productionTrend}><CartesianGrid stroke="#1d2c45" strokeDasharray="3 5" vertical={false}/><XAxis dataKey="date" tick={{ fill: "#8291aa", fontSize: 10 }} axisLine={false} tickLine={false}/><YAxis tick={{ fill: "#8291aa", fontSize: 11 }} axisLine={false} tickLine={false}/><Tooltip contentStyle={{ background: "#101d33", border: "1px solid #263956", borderRadius: 10 }}/><Legend/><Bar dataKey="actual" name="Faktiki" fill="#269bff" radius={[4,4,0,0]}/><Bar dataKey="forecast" name="Proqnoz" fill="#8b5cf6" radius={[4,4,0,0]}/></BarChart></ResponsiveContainer></div>
        </Panel>
      </div>
      <div className="info-banner"><span>i</span><div><strong>Analitik qeyd</strong><p>Qrafiklər demo məlumatlarla qurulub. Real layihədə bu göstəricilər Data Analyst-in hazırladığı API nəticələrindən gələcək.</p></div></div>
    </>
  );
}