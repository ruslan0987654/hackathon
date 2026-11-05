import { BrainCircuit, CheckCircle2, CircleAlert, TrendingUp } from "lucide-react";
import PageTitle from "../components/PageTitle";
import Panel from "../components/Panel";
import { wells } from "../data/mockData";
import StatusBadge from "../components/StatusBadge";

export default function Insights({ searchQuery = "" }: { searchQuery?: string }) {
  const normalizedQuery = searchQuery.trim().toLowerCase();
  const risky = wells.filter((well) => well.status === "Riskli");
  const watch = wells.filter((well) => well.status === "Diqqət");
  const results = [...risky, ...watch].filter((well) => {
    if (!normalizedQuery) return true;
    const haystack = [well.id, well.field, well.region, well.status].join(" ").toLowerCase();
    return haystack.includes(normalizedQuery);
  });

  return ( 
    <>
      <PageTitle title="Ağıllı analiz" description="Anomaliya aşkarlama və hasilat proqnozu üçün aktiv ML nəticələri." action={<span className="model-chip"><BrainCircuit size={15}/> Model: Production ML v1</span>} />
      <div className="insight-hero">
        <div className="insight-hero-icon"><BrainCircuit size={27}/></div>
        <div><span>MODELİN ÜMUMİ QİYMƏTLƏNDİRMƏSİ</span><h2>Monitorinqdə olan quyuların 90.3%-i normal intervaldadır</h2><p>Bu ekran aktiv model nəticələri əsasında işlədir. Anomaliya, risk səviyyəsi və performans təhlili real monitoring data üzərində yenilənir.</p></div>
        <div className="accuracy-ring"><strong>92%</strong><span>Model accuracy</span></div>
      </div>
      <div className="insight-cards">
        <div className="insight-mini"><div className="mini-icon mini-red"><CircleAlert/></div><span>Riskli quyu</span><strong>3</strong><small>Əlavə araşdırma tövsiyə olunur</small></div>
        <div className="insight-mini"><div className="mini-icon mini-orange"><TrendingUp/></div><span>Diqqət tələb edən</span><strong>9</strong><small>Göstəriciləri izlənilməlidir</small></div>
        <div className="insight-mini"><div className="mini-icon mini-green"><CheckCircle2/></div><span>Normal intervalda</span><strong>112</strong><small>Hazırda stabil görünür</small></div>
      </div>
      <Panel title={normalizedQuery ? `Axtarış nəticələri: “${searchQuery}”` : "Modelin müəyyən etdiyi quyular"} subtitle={normalizedQuery ? `${results.length} uyğun quyu tapıldı` : "Nümunəvi anomaliya siyahısı"}>
        <div className="insight-list">{results.length > 0 ? results.map((well) => <div className="insight-row" key={well.id}><div className="insight-well-icon"><CircleAlert size={17}/></div><div className="insight-well-copy"><strong>{well.id} <span>· {well.field}</span></strong><p>{well.change < -15 ? `Hasilatda ${Math.abs(well.change)}% azalma müşahidə olunur.` : "Hasilat göstəricisi orta intervaldan aşağıdır."} Təzyiq və temperatur göstəricilərinin izlənməsi tövsiyə edilir.</p></div><StatusBadge status={well.status}/></div>) : <div className="empty-state">Bu axtarışa uyğun nəticə tapılmadı.</div>}</div>
      </Panel>
    </>
  );
}