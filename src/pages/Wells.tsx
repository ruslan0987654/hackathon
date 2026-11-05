import { useEffect, useMemo, useState } from "react";
import { Search, SlidersHorizontal, Download } from "lucide-react";
import PageTitle from "../components/PageTitle";
import Panel from "../components/Panel";
import StatusBadge from "../components/StatusBadge";
import { createWell, fetchWells } from "../lib/api";
import type { Well, WellStatus } from "../types";

export default function Wells({ searchQuery, onSearchChange }: { searchQuery: string; onSearchChange: (value: string) => void }) {
  const [status, setStatus] = useState("Hamısı");
  const [wells, setWells] = useState<Well[]>([]);
  const [selectedWell, setSelectedWell] = useState<Well | null>(null);
  const [analysis, setAnalysis] = useState<{ status: string; message: string; result?: any } | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  useEffect(() => {
    void fetchWells().then(({ wells: nextWells }) => {
      setWells(nextWells);
      setSelectedWell(nextWells[0] ?? null);
    });
  }, []);

  const normalizedQuery = searchQuery.trim().toLowerCase();

  const filtered = useMemo(
    () =>
      wells.filter((well) => {
        const haystack = [well.id, well.field, well.region, well.status].join(" ").toLowerCase();
        const matchesQuery = !normalizedQuery || haystack.includes(normalizedQuery);
        const matchesStatus = status === "Hamısı" || well.status === status;
        return matchesQuery && matchesStatus;
      }),
    [normalizedQuery, status, wells],
  );

  useEffect(() => {
    if (filtered.length > 0 && (!selectedWell || !filtered.some((well) => well.id === selectedWell.id))) {
      setSelectedWell(filtered[0]);
    }

    if (filtered.length === 0) {
      setSelectedWell(null);
    }
  }, [filtered, selectedWell]);

  const addNewWell = async () => {
    const nextId = `Q-${String(wells.length + 1000).padStart(4, '0')}`;
    const nextWell = {
      id: nextId,
      region: "Abşeron",
      field: "Yeni quyu sahəsi",
      production: 220 + Math.round(Math.random() * 120),
      pressure: 120 + Math.round(Math.random() * 40),
      temperature: 64 + Math.round(Math.random() * 18),
      status: "Normal",
      change: Number((Math.random() * 10 - 2).toFixed(1)),
      lastUpdated: new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' }),
    };

    const result = await createWell(nextWell);
    setWells((current) => {
      const existing = current.some((well) => well.id === result.well.id);
      return existing ? current : [...current, result.well];
    });
    setSelectedWell(result.well);
  };

  const analyzeSelectedWell = async () => {
    if (!selectedWell) return;

    setIsAnalyzing(true);
    setAnalysis(null);

    try {
      const res = await fetch(`/api/ml/wells/${selectedWell.id}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });

      const payload = await res.json();
      setAnalysis({
        status: payload?.status ?? 'unknown',
        message: payload?.message ?? 'Analiz tamamlandı.',
        result: payload?.result ?? payload?.data ?? null,
      });
    } catch (error) {
      setAnalysis({
        status: 'error',
        message: error instanceof Error ? error.message : 'ML analizi baş tutmadı.',
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <>
      <PageTitle title="Quyular" description="Monitorinqdə olan quyuların siyahısı və cari texniki göstəriciləri." action={<div style={{ display: 'flex', gap: 8 }}><button className="secondary-button" onClick={addNewWell}><Download size={16} /> Yeni quyu</button><button className="primary-button" onClick={analyzeSelectedWell} disabled={!selectedWell || isAnalyzing}>{isAnalyzing ? 'Analiz edilir…' : 'ML analizi'}</button><button className="primary-button" onClick={() => window.alert("Report export is available in the production workflow.")}><Download size={16} /> İxrac et</button></div>} />
      <div className="well-summary">
        <div><span>Ümumi quyu</span><strong>{wells.length || 124}</strong></div><div><span>Normal</span><strong className="text-green">{wells.filter((well) => well.status === "Normal").length || 112}</strong></div><div><span>Diqqət</span><strong className="text-orange">{wells.filter((well) => well.status === "Diqqət").length || 9}</strong></div><div><span>Riskli</span><strong className="text-red">{wells.filter((well) => well.status === "Riskli").length || 3}</strong></div>
      </div>
      <Panel title="Quyu reyestri" subtitle={`${filtered.length} quyu göstərilir`}>
        <div className="table-toolbar">
          <label className="table-search"><Search size={16} /><input value={searchQuery} onChange={(e) => onSearchChange(e.target.value)} placeholder="Quyu ID, yataq və ya region axtar..." /></label>
          <label className="filter-select"><SlidersHorizontal size={15} /><select value={status} onChange={(e) => setStatus(e.target.value)}><option>Hamısı</option><option>Normal</option><option>Diqqət</option><option>Riskli</option></select></label>
        </div>
        <div className="table-scroll">
          <table className="data-table">
            <thead><tr><th>QUYU ID</th><th>REGİON / YATAQ</th><th>HASİLAT <small>bbl/gün</small></th><th>TƏZYİQ <small>bar</small></th><th>TEMPERATUR <small>°C</small></th><th>DƏYİŞİM</th><th>STATUS</th><th></th></tr></thead>
            <tbody>{filtered.map((well) => <tr key={well.id} className={selectedWell?.id === well.id ? "row-selected" : ""} onClick={() => setSelectedWell(well)}><td><strong className="well-id">{well.id}</strong></td><td><strong>{well.field}</strong><span className="cell-sub">{well.region}</span></td><td>{well.production}</td><td>{well.pressure}</td><td>{well.temperature}</td><td className={well.change >= 0 ? "text-green" : "text-red"}>{well.change > 0 ? "+" : ""}{well.change}%</td><td><StatusBadge status={well.status as WellStatus} /></td><td><button className="row-view" onClick={(e) => { e.stopPropagation(); setSelectedWell(well); }}>Bax</button></td></tr>)}</tbody>
          </table>
          {filtered.length === 0 && <div className="empty-state">Axtarışa uyğun quyu tapılmadı.</div>}
        </div>
      </Panel>
      {selectedWell && (
        <>
          <Panel title={`Seçilmiş quyu: ${selectedWell.id}`} subtitle={`${selectedWell.field} · ${selectedWell.region}`}>
            <div className="selected-well-grid">
              <div><span>Gündəlik hasilat</span><strong>{selectedWell.production} <small>bbl/gün</small></strong></div>
              <div><span>Təzyiq</span><strong>{selectedWell.pressure} <small>bar</small></strong></div>
              <div><span>Temperatur</span><strong>{selectedWell.temperature} <small>°C</small></strong></div>
              <div><span>Son dəyişiklik</span><strong className={selectedWell.change >= 0 ? "text-green" : "text-red"}>{selectedWell.change > 0 ? "+" : ""}{selectedWell.change}%</strong></div>
            </div>
          </Panel>
          {analysis && (
            <Panel title={`ML nəticəsi: ${selectedWell.id}`} subtitle={analysis.message}>
              <div className="selected-well-grid">
                <div><span>Status</span><strong>{analysis.status}</strong></div>
                <div><span>Risk səviyyəsi</span><strong>{analysis.result?.riskLevel ?? '—'}</strong></div>
                <div><span>Risk xalı</span><strong>{analysis.result?.riskScore ?? '—'}</strong></div>
                <div><span>Anomaliya</span><strong>{analysis.result?.anomalyDetected ? 'Bəli' : 'Yox'}</strong></div>
              </div>
            </Panel>
          )}
        </>
      )}
    </>
  );
}