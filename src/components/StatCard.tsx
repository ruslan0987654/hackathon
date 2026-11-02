import type { LucideIcon } from "lucide-react";

interface StatCardProps {
  label: string;
  value: string;
  unit?: string;
  change: string;
  direction?: "up" | "down" | "neutral";
  icon: LucideIcon;
  color: "blue" | "green" | "purple" | "orange";
  note?: string;
}

export default function StatCard({ label, value, unit, change, direction = "up", icon: Icon, color, note = "öncəki dövrlə müqayisədə" }: StatCardProps) {
  return (
    <article className={`stat-card stat-${color}`}>
      <div className="stat-card-top">
        <div className="stat-icon"><Icon size={21} /></div>
        <span className={`trend trend-${direction}`}>{direction === "up" ? "↗" : direction === "down" ? "↘" : "—"} {change}</span>
      </div>
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}<small>{unit}</small></div>
      <div className="stat-note">{note}</div>
      <div className="stat-sparkline"><span /><span /><span /><span /><span /><span /><span /><span /></div>
    </article>
  );
}