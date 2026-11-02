import { ArrowUpRight, BellRing } from "lucide-react";
import { alerts } from "../data/mockData";
import Panel from "./Panel";

export default function AlertsPreview({ onViewAll }: { onViewAll: () => void }) {
  return (
    <Panel title="Son xəbərdarlıqlar" subtitle="Diqqət tələb edən son dəyişikliklər" action={<button className="text-button" onClick={onViewAll}>Hamısına bax <ArrowUpRight size={14} /></button>}>
      <div className="alert-preview-list">
        {alerts.slice(0, 3).map((alert) => (
          <div className="alert-preview-item" key={alert.id}>
            <div className={`alert-symbol alert-${alert.severity === "Yüksək" ? "high" : alert.severity === "Orta" ? "medium" : "low"}`}><BellRing size={15} /></div>
            <div className="alert-preview-copy"><strong>{alert.title}</strong><span>{alert.wellId} · {alert.time}</span></div>
            <span className={`severity severity-${alert.severity === "Yüksək" ? "high" : alert.severity === "Orta" ? "medium" : "low"}`}>{alert.severity}</span>
          </div>
        ))}
      </div>
    </Panel>
  );
}