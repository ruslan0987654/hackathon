import type { WellStatus } from "../types";

export default function StatusBadge({ status }: { status: WellStatus }) {
  return <span className={`status-badge status-${status === "Normal" ? "normal" : status === "Diqqət" ? "watch" : "risk"}`}><i />{status}</span>;
}