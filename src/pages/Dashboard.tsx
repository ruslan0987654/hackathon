import { Activity, AlertTriangle, BarChart3, Droplets, Gauge, TrendingUp } from "lucide-react";
import PageTitle from "../components/PageTitle";
import StatCard from "../components/StatCard";
import ProductionChart from "../components/ProductionChart";
import WellMap from "../components/WellMap";
import AlertsPreview from "../components/AlertsPreview";
import Panel from "../components/Panel";
import { Pie, PieChart, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { categoryShare, wells } from "../data/mockData";

export default function Dashboard({ onNavigate }: { onNavigate: (page: "alerts" | "wells" | "analytics" | "insights" | "dashboard") => void }) {
  const totalProduction = wells.reduce((sum, well) => sum + well.production, 0);
  return (
    <>
      <PageTitle title="Ümumi göstəricilər" description="Quyuların hasilat, texniki vəziyyət və risk göstəricilərinin icmalı." action={<span className="demo-chip"><i /> DEMO MƏLUMATLAR</span>} />
      <div className="stats-grid">
        <StatCard label="Analiz edilən quyular" value="124" change="+2.5%" icon={Droplets} color="blue" />
        <StatCard label="Ümumi hasilat" value="482.75" unit="k bbl" change="+6.8%" icon={BarChart3} color="green" />
        <StatCard label="Araşdırılmalı quyular" value="9" change="-1.2%" direction="down" icon={Activity} color="purple" />
        <StatCard label="Riskli quyular" value="3" change="+0.0%" direction="neutral" icon={AlertTriangle} color="orange" />
      </div>
      <div className="dashboard-grid dashboard-grid-main">
        <ProductionChart />
        <WellMap />
      </div>
      <div className="dashboard-grid dashboard-grid-bottom">
        <Panel title="Hasilatın paylanması" subtitle="Nümunəvi məhsul bölgüsü">
          <div className="donut-layout">
            <div className="donut-wrap">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart><Pie data={categoryShare} dataKey="value" nameKey="name" innerRadius={62} outerRadius={86} paddingAngle={4} stroke="none">{categoryShare.map((item) => <Cell key={item.name} fill={item.color} />)}</Pie><Tooltip contentStyle={{ background: "#101d33", border: "1px solid #263956", borderRadius: 10 }} /></PieChart>
              </ResponsiveContainer>
              <div className="donut-center"><strong>482.75</strong><span>k bbl</span></div>
            </div>
            <div className="donut-legend">{categoryShare.map((item) => <div key={item.name}><span><i style={{ background: item.color }} />{item.name}</span><b>{item.value}%</b></div>)}</div>
          </div>
        </Panel>
        <Panel title="Əsas texniki göstəricilər" subtitle="Seçilmiş quyular üzrə orta göstərici">
          <div className="metric-list">
            <div className="metric-row"><div className="metric-icon metric-blue"><Gauge size={18} /></div><div className="metric-copy"><span>Orta təzyiq</span><strong>126.4 <small>bar</small></strong></div><span className="metric-change positive">+1.8%</span></div>
            <div className="metric-row"><div className="metric-icon metric-orange"><Activity size={18} /></div><div className="metric-copy"><span>Orta temperatur</span><strong>69.8 <small>°C</small></strong></div><span className="metric-change positive">+0.9%</span></div>
            <div className="metric-row"><div className="metric-icon metric-green"><TrendingUp size={18} /></div><div className="metric-copy"><span>İstismar əmsalı</span><strong>96.5 <small>%</small></strong></div><span className="metric-change positive">+2.1%</span></div>
          </div>
        </Panel>
        <AlertsPreview onViewAll={() => onNavigate("alerts")} />
      </div>
      <div className="bottom-note">Ümumi hasilat cəmi: <b>{totalProduction.toLocaleString("az-AZ")} barrel/gün</b> <span>·</span> Göstərilən bütün rəqəmlər demo məqsədlidir.</div>
    </>
  );
}