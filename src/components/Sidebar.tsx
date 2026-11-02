import { Activity, Bell, ChartNoAxesCombined, ClipboardList, Database, Gauge, House, Settings, Waves } from "lucide-react";
import type { PageKey } from "../types";

interface SidebarProps {
  activePage: PageKey;
  onNavigate: (page: PageKey) => void;
}

const navItems = [
  { id: "dashboard" as const, label: "Ümumi göstəricilər", icon: House },
  { id: "wells" as const, label: "Quyular", icon: Database },
  { id: "analytics" as const, label: "Analitika", icon: ChartNoAxesCombined },
  { id: "insights" as const, label: "Ağıllı analiz", icon: Activity },
  { id: "alerts" as const, label: "Xəbərdarlıqlar", icon: Bell },
];

export default function Sidebar({ activePage, onNavigate }: SidebarProps) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark"><Waves size={25} /></div>
        <div><strong>SOCAR</strong><span>SMART ANALYTICS</span></div>
      </div>

      <div className="nav-caption">İŞ MASASI</div>
      <nav className="nav-list">
        {navItems.map(({ id, label, icon: Icon }) => (
          <button key={id} className={`nav-link ${activePage === id ? "active" : ""}`} onClick={() => onNavigate(id)}>
            <Icon size={18} strokeWidth={1.8} />
            <span>{label}</span>
            {id === "alerts" && <i className="nav-count">3</i>}
          </button>
        ))}
      </nav>

      <div className="nav-caption secondary-caption">SİSTEM</div>
      <button className="nav-link" onClick={() => onNavigate("analytics")}><Gauge size={18} /><span>Parametrlər</span></button>
      <button className="nav-link" onClick={() => onNavigate("analytics")}><Settings size={18} /><span>Konfiqurasiya</span></button>

      <div className="sidebar-bottom">
        <div className="online-indicator"><span /> Demo məlumatlar aktivdir</div>
        <div className="sidebar-version">SOCAR Analytics <b>v1.0.0</b></div>
      </div>
    </aside>
  );
}