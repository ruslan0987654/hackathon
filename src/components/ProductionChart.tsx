import { useState } from "react";
import { Area, AreaChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { productionTrend } from "../data/mockData";
import Panel from "./Panel";

export default function ProductionChart() {
  const [mode, setMode] = useState("Günlük");
  return (
    <Panel title="Hasilatın zaman üzrə dəyişməsi" subtitle="Ümumi hasilat və model proqnozu" action={
      <div className="segmented-control">{["Günlük", "Həftəlik", "Aylıq"].map((item) => <button key={item} className={mode === item ? "selected" : ""} onClick={() => setMode(item)}>{item}</button>)}</div>
    }>
      <div className="chart-legend"><span><i className="legend-blue" /> Faktiki hasilat</span><span><i className="legend-dashed" /> Model proqnozu</span></div>
      <div className="chart-area">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={productionTrend} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
            <defs>
              <linearGradient id="actualFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#269bff" stopOpacity={0.28} /><stop offset="100%" stopColor="#269bff" stopOpacity={0.01} /></linearGradient>
              <linearGradient id="forecastFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.12} /><stop offset="100%" stopColor="#8b5cf6" stopOpacity={0} /></linearGradient>
            </defs>
            <CartesianGrid stroke="#1d2c45" strokeDasharray="3 5" vertical={false} />
            <XAxis dataKey="date" tick={{ fill: "#8291aa", fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: "#8291aa", fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ background: "#101d33", border: "1px solid #263956", borderRadius: 10, color: "#eaf1ff" }} />
            <Legend wrapperStyle={{ display: "none" }} />
            <Area type="monotone" dataKey="actual" name="Faktiki hasilat" stroke="#269bff" strokeWidth={2.5} fill="url(#actualFill)" />
            <Area type="monotone" dataKey="forecast" name="Proqnoz" stroke="#9a78ff" strokeWidth={2} strokeDasharray="6 5" fill="url(#forecastFill)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <div className="chart-footnote"><span className="tiny-live-dot" /> Nümunəvi göstəricilər · Ölçü vahidi: min barrel/gün</div>
    </Panel>
  );
}