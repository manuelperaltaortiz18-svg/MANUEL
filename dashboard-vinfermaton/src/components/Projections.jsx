import { useState } from 'react';
import { proyectar, trayectoria } from '../lib/projections.js';
import { ProjectionChart } from './Charts.jsx';
import { COLORS, eur } from '../theme.js';

const TIPOS = ['AVISPAS', 'MOSQUITOS', 'MOSCAS', 'ANTIPOLILLAS', 'INSECT', 'REPELENTE', 'OTROS'];

export function Projections({ rows, desde }) {
  const [hasta, setHasta] = useState('2026-09-30');
  // Vendimia: el pico real de avispas es septiembre, no julio-agosto.
  const [mult, setMult] = useState({ AVISPAS: 1.4, MOSQUITOS: 0.5 });

  const p = proyectar(rows, { desde, hasta, multiplicadores: mult });
  const data = trayectoria(rows, { desde, hasta, multiplicadores: mult });

  return (
    <div style={{ display: 'grid', gap: 16 }}>
      <div className="card">
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <label style={{ display: 'grid', gap: 4 }}>
            <span style={{ fontSize: 12, color: COLORS.muted }}>Fecha objetivo</span>
            <input
              type="date" value={hasta} onChange={(e) => setHasta(e.target.value)}
              style={{ background: COLORS.bg, color: COLORS.text, border: `1px solid ${COLORS.border}`, borderRadius: 6, padding: '6px 8px' }}
            />
          </label>
          {TIPOS.map((t) => (
            <label key={t} style={{ display: 'grid', gap: 4 }}>
              <span style={{ fontSize: 12, color: COLORS.muted }}>{t} ×</span>
              <input
                type="number" step="0.1" min="0" value={mult[t] ?? 1}
                onChange={(e) => setMult((m) => ({ ...m, [t]: Number(e.target.value) }))}
                style={{ width: 70, background: COLORS.bg, color: COLORS.text, border: `1px solid ${COLORS.border}`, borderRadius: 6, padding: '6px 8px' }}
              />
            </label>
          ))}
        </div>
        <div style={{ marginTop: 12, color: COLORS.muted, fontSize: 13 }}>
          Base {eur(p.base)} · {p.semanas} semanas hasta {hasta} ·
          {' '}Lineal <b style={{ color: COLORS.text }}>{eur(p.escenarios.lineal)}</b> ·
          {' '}Bueno <b style={{ color: COLORS.text }}>{eur(p.escenarios.bueno)}</b> ·
          {' '}Muy bueno <b style={{ color: COLORS.text }}>{eur(p.escenarios.muyBueno)}</b>
        </div>
        <div style={{ marginTop: 8, color: COLORS.orange, fontSize: 12 }}>
          ⚠ La proyección parte de la velocidad del último periodo cargado. Si esa
          velocidad es un mínimo estacional, los tres escenarios lo son también.
        </div>
      </div>
      <div className="card"><ProjectionChart data={data} /></div>
    </div>
  );
}
