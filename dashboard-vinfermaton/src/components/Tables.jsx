import { useMemo, useState } from 'react';
import { COLORS, MARCA_LINE, bbColor, eur, num } from '../theme.js';

function useSort(rows, inicial) {
  const [sort, setSort] = useState(inicial);
  const sorted = useMemo(() => {
    const { key, dir } = sort;
    return [...rows].sort((a, b) => {
      const va = a[key], vb = b[key];
      if (va == null && vb == null) return 0;
      if (va == null) return 1;
      if (vb == null) return -1;
      const cmp = typeof va === 'string' ? va.localeCompare(vb) : va - vb;
      return dir === 'asc' ? cmp : -cmp;
    });
  }, [rows, sort]);
  const toggle = (key) =>
    setSort((s) => (s.key === key ? { key, dir: s.dir === 'asc' ? 'desc' : 'asc' } : { key, dir: 'desc' }));
  return { sorted, sort, toggle };
}

function Th({ label, k, sort, toggle }) {
  return (
    <th onClick={() => toggle(k)}>
      {label}{sort.key === k ? (sort.dir === 'asc' ? ' ▲' : ' ▼') : ''}
    </th>
  );
}

export function BrandTable({ marcas, onSelect }) {
  const { sorted, sort, toggle } = useSort(marcas, { key: 'ventas', dir: 'desc' });
  return (
    <div className="scroll">
      <table className="tabular">
        <thead>
          <tr>
            <Th label="Marca" k="marca" sort={sort} toggle={toggle} />
            <Th label="Ventas" k="ventas" sort={sort} toggle={toggle} />
            <Th label="Δ periodo" k="delta" sort={sort} toggle={toggle} />
            <Th label="€/sem" k="vel" sort={sort} toggle={toggle} />
            <Th label="Uds" k="uds" sort={sort} toggle={toggle} />
            <Th label="ASINs" k="asins" sort={sort} toggle={toggle} />
            <Th label="BB" k="bb" sort={sort} toggle={toggle} />
            <th>Señal</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((m) => (
            <tr key={m.marca} onClick={() => onSelect(m.marca)} style={{ cursor: 'pointer' }}>
              <td>
                <span style={{
                  display: 'inline-block', width: 8, height: 8, borderRadius: 2,
                  background: MARCA_LINE[m.marca] || COLORS.muted, marginRight: 8,
                }} />
                {m.marca}
              </td>
              <td>{eur(m.ventas)}</td>
              <td style={{ color: m.delta > 0 ? COLORS.green : COLORS.muted }}>
                {m.delta == null ? '—' : `+${eur(m.delta)}`}
              </td>
              <td>{m.vel == null ? '—' : eur(m.vel)}</td>
              <td>{num(m.uds)}</td>
              <td>{m.asins}</td>
              <td style={{ color: bbColor(m.bb), fontWeight: 600 }}>{m.bb.toFixed(1)}%</td>
              <td>{m.senal}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function ProductTable({ rows, selected, onToggleSelect }) {
  const { sorted, sort, toggle } = useSort(rows, { key: 'ventas', dir: 'desc' });
  return (
    <div className="scroll">
      <table className="tabular">
        <thead>
          <tr>
            {onToggleSelect && <th style={{ width: 30 }} />}
            <Th label="Producto" k="titulo" sort={sort} toggle={toggle} />
            <Th label="ASIN" k="asin" sort={sort} toggle={toggle} />
            <Th label="Tipo" k="tipo" sort={sort} toggle={toggle} />
            <Th label="Uds" k="uds" sort={sort} toggle={toggle} />
            <Th label="Ventas" k="ventas" sort={sort} toggle={toggle} />
            <Th label="Δ periodo" k="deltaVentas" sort={sort} toggle={toggle} />
            <Th label="€/sem" k="vel" sort={sort} toggle={toggle} />
            <Th label="BB" k="bb" sort={sort} toggle={toggle} />
            <th>Tend.</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((r) => (
            <tr key={r.asin}>
              {onToggleSelect && (
                <td>
                  <input
                    type="checkbox"
                    checked={selected?.includes(r.asin) || false}
                    onChange={() => onToggleSelect(r.asin)}
                  />
                </td>
              )}
              <td>
                {r.titulo || r.asin}
                {r.esNuevo && (
                  <span style={{ color: COLORS.blue, fontSize: 11, marginLeft: 6 }}>NUEVO</span>
                )}
              </td>
              <td style={{ color: COLORS.muted, fontFamily: 'monospace', fontSize: 12 }}>{r.asin}</td>
              <td style={{ color: COLORS.muted, fontSize: 12 }}>{r.tipo}</td>
              <td>{num(r.uds)}</td>
              <td>{eur(r.ventas)}</td>
              <td style={{ color: r.deltaVentas > 0 ? COLORS.green : COLORS.muted }}>
                {r.deltaVentas == null ? '—' : `+${eur(r.deltaVentas)}`}
              </td>
              <td>{r.vel == null ? '—' : eur(r.vel)}</td>
              <td style={{ color: bbColor(r.bb), fontWeight: 600 }}>{r.bb.toFixed(1)}%</td>
              <td>{r.tendencia || '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function AlertList({ alerts }) {
  const estilo = {
    urgente: { color: COLORS.red, label: 'URGENTE' },
    medio: { color: COLORS.orange, label: 'MEDIO' },
    positivo: { color: COLORS.green, label: 'POSITIVO' },
    nuevo: { color: COLORS.blue, label: 'NUEVO' },
  };
  if (alerts.length === 0) {
    return <div style={{ color: COLORS.muted }}>Sin alertas en este periodo.</div>;
  }
  return (
    <div style={{ display: 'grid', gap: 8 }}>
      {alerts.map((a, i) => {
        const e = estilo[a.nivel];
        return (
          <div key={`${a.asin}-${i}`} style={{ borderLeft: `3px solid ${e.color}`, paddingLeft: 10 }}>
            <div style={{ fontSize: 11, color: e.color, fontWeight: 700, letterSpacing: '.05em' }}>
              {e.label} · {a.marca}
            </div>
            <div style={{ fontWeight: 600 }}>{a.titulo || a.asin}</div>
            <div style={{ color: COLORS.muted, fontSize: 13 }}>
              {a.msg}
              {a.perdida ? ` Pérdida estimada ≈ ${eur(a.perdida)}.` : ''}
            </div>
          </div>
        );
      })}
    </div>
  );
}
