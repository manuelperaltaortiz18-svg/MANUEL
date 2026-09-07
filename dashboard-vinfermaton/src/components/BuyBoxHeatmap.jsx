import { bbColor, COLORS } from '../theme.js';

/** Heatmap BuyBox: filas = producto, columnas = corte semanal. */
export function BuyBoxHeatmap({ snapshots, marca }) {
  const fechas = snapshots.map((s) => s.fecha);
  const asins = new Map();
  for (const s of snapshots) {
    for (const r of s.rows) {
      if (marca && r.marca !== marca) continue;
      if (!asins.has(r.asin)) asins.set(r.asin, r.titulo);
    }
  }

  const bbAt = (fecha, asin) =>
    snapshots.find((s) => s.fecha === fecha)?.rows.find((r) => r.asin === asin)?.bb ?? null;

  if (fechas.length < 2) {
    return (
      <div style={{ color: COLORS.muted, fontSize: 13 }}>
        Sube al menos dos informes para ver la evolución de BuyBox.
      </div>
    );
  }

  return (
    <div className="scroll">
      <table>
        <thead>
          <tr>
            <th>Producto</th>
            {fechas.map((f) => <th key={f}>{f.slice(5)}</th>)}
          </tr>
        </thead>
        <tbody>
          {[...asins.entries()].map(([asin, titulo]) => (
            <tr key={asin}>
              <td title={asin}>{titulo || asin}</td>
              {fechas.map((f) => {
                const bb = bbAt(f, asin);
                return (
                  <td key={f} style={{ padding: 4 }}>
                    <div
                      title={bb == null ? 'sin dato' : `${bb.toFixed(1)}%`}
                      style={{
                        background: bb == null ? '#24324a' : bbColor(bb),
                        opacity: bb == null ? 0.4 : 0.25 + (bb / 100) * 0.75,
                        borderRadius: 4, height: 22, minWidth: 40,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: 11, color: '#0F172A', fontWeight: 700,
                      }}
                    >
                      {bb == null ? '' : Math.round(bb)}
                    </div>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
