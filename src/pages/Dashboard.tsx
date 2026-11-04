import { Activity, AlertTriangle, BarChart3, Droplets, Gauge, TrendingUp } from "lucide-react";
import { useEffect, useState } from "react";
import PageTitle from "../components/PageTitle";
import StatCard from "../components/StatCard";
import ProductionChart from "../components/ProductionChart";
import WellMap from "../components/WellMap";
import AlertsPreview from "../components/AlertsPreview";
import Panel from "../components/Panel";
import { Pie, PieChart, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { fetchDashboard, type DashboardApiResponse } from "../lib/api";

export default function Dashboard({ searchQuery, onNavigate }: { searchQuery: string; onNavigate: (page: "alerts" | "wells" | "analytics" | "insights" | "dashboard") => void }) {
  const [dashboard, setDashboard] = useState<DashboardApiResponse>({
    source: "mock",
    summary: { totalProduction: 0, analyzedWells: 124, productionGoal: 482.75, riskWells: 3, attentionWells: 9 },
    categoryShare: [],
    productionTrend: [],
    parameterTrend: [],
    alerts: [],
  });

  useEffect(() => {
    void fetchDashboard().then(setDashboard);
  }, []);

  const normalizedQuery = searchQuery.trim().toLowerCase();
  const matchingAlerts = normalizedQuery ? dashboard.alerts.filter((alert) => [alert.title, alert.description, alert.wellId].join(" ").toLowerCase().includes(normalizedQuery)) : [];
  const totalProduction = dashboard.summary.totalProduction;
  const categoryShare = dashboard.categoryShare;

  return (
    <>
      <PageTitle title="Ümumi göstəricilər" description="Quyuların hasilat, texniki vəziyyət və risk göstəricilərinin icmalı." action={<span className="demo-chip"><i /> {dashboard.source === "live" ? "LIVE API" : "DEMO MƏLUMATLAR"}</span>} />
      {normalizedQuery && (
        <Panel title={`Axtarış nəticələri: “${searchQuery}”`} subtitle={`${matchingAlerts.length} uyğun bildiriş tapıldı`}>
          <div className="alerts-list">
            {matchingAlerts.length > 0 ? matchingAlerts.map((alert) => (
              <article className="alert-card" key={alert.id}>
                <div className="alert-content">
                  <div className="alert-title-line"><strong>{alert.title}</strong><span className={`severity severity-${alert.severity === "Yüksək" ? "high" : alert.severity === "Orta" ? "medium" : "low"}`}>{alert.severity}</span></div>
                  <p>{alert.description}</p>
                  <div className="alert-meta"><span>{alert.id}</span><span>Quyu: {alert.wellId}</span><span>{alert.time}</span></div>
                </div>
              </article>
            )) : <div className="empty-state">Bu axtarışa uyğun nəticə tapılmadı.</div>}
          </div>
        </Panel>
      )}
      <div className="stats-grid">
        <StatCard label="Analiz edilən quyular" value={String(dashboard.summary.analyzedWells)} change="+2.5%" icon={Droplets} color="blue" />
        <StatCard label="Ümumi hasilat" value={String(dashboard.summary.productionGoal)} unit="k bbl" change="+6.8%" icon={BarChart3} color="green" />
        <StatCard label="Araşdırılmalı quyular" value={String(dashboard.summary.attentionWells)} change="-1.2%" direction="down" icon={Activity} color="purple" />
        <StatCard label="Riskli quyular" value={String(dashboard.summary.riskWells)} change="+0.0%" direction="neutral" icon={AlertTriangle} color="orange" />
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
              <div className="donut-center"><strong>{dashboard.summary.productionGoal}</strong><span>k bbl</span></div>
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
      <div className="bottom-note">Ümumi hasilat cəmi: <b>{totalProduction.toLocaleString("az-AZ")} barrel/gün</b> <span>·</span> Göstərilən bütün rəqəmlər demo və live data ilə işlənə bilər.</div>
    </>
  );
}