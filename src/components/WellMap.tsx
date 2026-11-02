import Panel from "./Panel";

const dots = [
  ["17%", "25%", "normal"], ["32%", "42%", "watch"], ["48%", "24%", "normal"],
  ["58%", "55%", "risk"], ["71%", "36%", "normal"], ["78%", "69%", "normal"],
  ["39%", "72%", "risk"], ["23%", "65%", "normal"], ["64%", "18%", "watch"],
  ["86%", "48%", "watch"], ["51%", "82%", "normal"], ["12%", "49%", "normal"],
];

export default function WellMap() {
  return (
    <Panel title="Quyuların yerləşməsi" subtitle="Şərti region xəritəsi" action={<button className="text-button">Xəritəyə bax ↗</button>}>
      <div className="map-visual">
        <svg className="map-outline" viewBox="0 0 420 260" role="img" aria-label="Şərti quyu xəritəsi">
          <path d="M62 57 L102 36 L132 49 L158 30 L190 45 L218 31 L244 53 L278 45 L306 70 L343 81 L360 112 L341 139 L352 166 L322 184 L299 219 L269 209 L241 229 L214 205 L183 218 L158 190 L127 192 L111 165 L79 155 L91 127 L64 104 Z" fill="#142c4a" stroke="#2b5c8d" strokeWidth="2" />
          <path d="M95 78 L142 95 L177 73 L212 104 L253 86 L294 111 L323 143 M113 154 L159 131 L197 158 L244 137 L282 174" fill="none" stroke="#23486e" strokeWidth="1.5" strokeDasharray="4 5" />
        </svg>
        {dots.map(([left, top, type], i) => <span key={i} className={`map-dot map-dot-${type}`} style={{ left, top }} />)}
      </div>
      <div className="map-legend">
        <span><i className="dot-normal" /> Normal <b>112</b></span>
        <span><i className="dot-watch" /> Diqqət <b>9</b></span>
        <span><i className="dot-risk" /> Riskli <b>3</b></span>
      </div>
      <p className="map-disclaimer">Xəritə vizual maketdir, real koordinatları göstərmir.</p>
    </Panel>
  );
}