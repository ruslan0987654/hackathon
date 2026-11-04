import { useEffect, useMemo, useState } from "react";
import { Search, SlidersHorizontal, Download } from "lucide-react";
import PageTitle from "../components/PageTitle";
import Panel from "../components/Panel";
import StatusBadge from "../components/StatusBadge";
import { fetchWells } from "../lib/api";
import type { Well, WellStatus } from "../types";

export default function Wells({ searchQuery, onSearchChange }: { searchQuery: string; onSearchChange: (value: string) => void }) {
  const [status, setStatus] = useState("Hamısı");
  const [wells, setWells] = useState<Well[]>([]);
  const [selectedWell, setSelectedWell] = useState<Well | null>(null);

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

  return (
    <>
      <PageTitle title="Quyular" description="Monitorinqdə olan quyuların siyahısı və cari texniki göstəriciləri." action={<button className="primary-button" onClick={() => window.alert("Demo versiyada ixrac nümunəsi.")}><Download size={16} /> İxrac et</button>} />
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
        <Panel title={`Seçilmiş quyu: ${selectedWell.id}`} subtitle={`${selectedWell.field} · ${selectedWell.region}`}>
          <div className="selected-well-grid">
            <div><span>Gündəlik hasilat</span><strong>{selectedWell.production} <small>bbl/gün</small></strong></div>
            <div><span>Təzyiq</span><strong>{selectedWell.pressure} <small>bar</small></strong></div>
            <div><span>Temperatur</span><strong>{selectedWell.temperature} <small>°C</small></strong></div>
            <div><span>Son dəyişiklik</span><strong className={selectedWell.change >= 0 ? "text-green" : "text-red"}>{selectedWell.change > 0 ? "+" : ""}{selectedWell.change}%</strong></div>
          </div>
        </Panel>
      )}
    </>
  );
}