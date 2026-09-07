import { COLORS } from '../theme.js';

export function KpiRow({ items }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12 }}>
      {items.map((k) => (
        <div key={k.label} className="card">
          <div style={{ color: COLORS.muted, fontSize: 12, textTransform: 'uppercase', letterSpacing: '.04em' }}>
            {k.label}
          </div>
          <div className="tabular" style={{ fontSize: 26, fontWeight: 700, marginTop: 6, color: k.color || COLORS.text }}>
            {k.value}
          </div>
          {k.sub && <div style={{ color: COLORS.muted, fontSize: 12, marginTop: 4 }}>{k.sub}</div>}
        </div>
      ))}
    </div>
  );
}
