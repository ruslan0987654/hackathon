import { useState } from "react";
import { BellRing, Check, CheckCheck } from "lucide-react";
import PageTitle from "../components/PageTitle";
import Panel from "../components/Panel";
import { alerts as initialAlerts } from "../data/mockData";
import type { AlertItem } from "../types";

export default function Alerts({ searchQuery, onSearchChange }: { searchQuery: string; onSearchChange: (value: string) => void }) {
  const [items, setItems] = useState<AlertItem[]>(initialAlerts);
  const [filter, setFilter] = useState("Hamısı");
  const normalizedQuery = searchQuery.trim().toLowerCase();

  const visible = items.filter((item) => {
    const haystack = [item.id, item.wellId, item.title, item.description, item.severity].join(" ").toLowerCase();
    const matchesQuery = !normalizedQuery || haystack.includes(normalizedQuery);
    const matchesFilter = filter === "Hamısı" || (filter === "Oxunmamış" ? !item.acknowledged : item.severity === filter);
    return matchesQuery && matchesFilter;
  });

  const acknowledge = (id: string) => setItems((current) => current.map((item) => item.id === id ? { ...item, acknowledged: true } : item));
  return (
    <>
      <PageTitle title="Xəbərdarlıqlar" description="Quyularda qeydə alınan qeyri-adi dəyişikliklər və tövsiyələr." action={<button className="secondary-button" onClick={() => setItems((current) => current.map((item) => ({ ...item, acknowledged: true })))}><CheckCheck size={16}/> Hamısını oxunmuş et</button>} />
      <div className="alert-summary"><div><span>Ümumi bildiriş</span><strong>{items.length}</strong></div><div><span>Oxunmamış</span><strong className="text-red">{items.filter((a) => !a.acknowledged).length}</strong></div><div><span>Yüksək prioritet</span><strong className="text-orange">{items.filter((a) => a.severity === "Yüksək").length}</strong></div></div>
      <Panel title="Bildiriş mərkəzi" subtitle={normalizedQuery ? `Axtarış nəticələri: “${searchQuery}”` : "Son sistem xəbərdarlıqları"}>
        <div className="table-toolbar">
          <label className="table-search"><BellRing size={16} /><input value={searchQuery} onChange={(e) => onSearchChange(e.target.value)} placeholder="Bildiriş, quyu ID və ya risk axtar..." /></label>
          <div className="filter-bar alert-filters">{["Hamısı", "Oxunmamış", "Yüksək", "Orta", "Aşağı"].map((item) => <button key={item} className={`filter-chip ${filter === item ? "active" : ""}`} onClick={() => setFilter(item)}>{item}</button>)}</div>
        </div>
        <div className="alerts-list">{visible.map((item) => <article className={`alert-card ${item.acknowledged ? "acknowledged" : ""}`} key={item.id}><div className={`alert-symbol alert-${item.severity === "Yüksək" ? "high" : item.severity === "Orta" ? "medium" : "low"}`}><BellRing size={17}/></div><div className="alert-content"><div className="alert-title-line"><strong>{item.title}</strong><span className={`severity severity-${item.severity === "Yüksək" ? "high" : item.severity === "Orta" ? "medium" : "low"}`}>{item.severity}</span></div><p>{item.description}</p><div className="alert-meta"><span>{item.id}</span><span>Quyu: {item.wellId}</span><span>{item.time}</span></div></div><button className="ack-button" disabled={item.acknowledged} onClick={() => acknowledge(item.id)}>{item.acknowledged ? <><Check size={14}/> Oxunub</> : "Oxundu et"}</button></article>)}</div>
        {visible.length === 0 && <div className="empty-state">Bu filtr üzrə bildiriş yoxdur.</div>}
      </Panel>
    </>
  );
}