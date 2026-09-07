import { useEffect, useMemo, useState } from 'react';
import { Upload } from './components/Upload.jsx';
import { KpiRow } from './components/Kpi.jsx';
import { BrandTable, ProductTable, AlertList } from './components/Tables.jsx';
import { VelocityChart } from './components/Charts.jsx';
import { BuyBoxHeatmap } from './components/BuyBoxHeatmap.jsx';
import { Projections } from './components/Projections.jsx';
import {
  loadSnapshots, addSnapshot, removeSnapshot, resetSnapshots,
  diffSnapshots, velocitySeries, brandVelocitySeries,
} from './lib/store.js';
import { buildAlerts, productosEnRiesgo } from './lib/alerts.js';
import { BRANDS } from './lib/classify.js';
import { COLORS, MARCA_LINE, eur, num } from './theme.js';

const TABS = ['General', 'Por marca', 'Histórico', 'Proyecciones', 'Datos'];

function señal(vel, velPrev) {
  if (vel == null || velPrev == null || velPrev === 0) return '—';
  const c = (vel - velPrev) / velPrev;
  if (c >= 0.2) return '↑↑';
  if (c >= 0.05) return '↑';
  if (c <= -0.3) return '☠';
  if (c <= -0.05) return '↓';
  return '→';
}

export function App() {
  const [snapshots, setSnapshots] = useState(() => loadSnapshots());
  const [tab, setTab] = useState('General');
  const [marca, setMarca] = useState('Vinfermaton');
  const [tipo, setTipo] = useState('TODOS');
  const [idxCurr, setIdxCurr] = useState(snapshots.length - 1);
  const [idxPrev, setIdxPrev] = useState(Math.max(0, snapshots.length - 2));
  const [seleccion, setSeleccion] = useState([]);

  // Al cargar un informe nuevo, el selector salta al último corte.
  useEffect(() => {
    setIdxCurr(snapshots.length - 1);
    setIdxPrev(Math.max(0, snapshots.length - 2));
  }, [snapshots.length]);

  const curr = snapshots[Math.min(idxCurr, snapshots.length - 1)];
  const prev = idxPrev !== idxCurr ? snapshots[idxPrev] : null;

  const rows = useMemo(() => diffSnapshots(prev, curr), [prev, curr]);
  const alerts = useMemo(() => buildAlerts(rows), [rows]);
  const enRiesgo = useMemo(() => productosEnRiesgo(rows), [rows]);

  const marcasResumen = useMemo(() => {
    const presentes = [...new Set(rows.map((r) => r.marca))];
    const orden = [...BRANDS, 'Otros'].filter((m) => presentes.includes(m));
    return orden.map((m) => {
      const rs = rows.filter((r) => r.marca === m);
      const ventas = rs.reduce((a, r) => a + r.ventas, 0);
      const vel = rs.reduce((a, r) => a + (r.vel || 0), 0);
      const velPrev = rs.reduce((a, r) => a + (r.velPrev || 0), 0);
      const delta = rs.some((r) => r.deltaVentas != null)
        ? rs.reduce((a, r) => a + (r.deltaVentas || 0), 0) : null;
      const bb = ventas > 0 ? rs.reduce((a, r) => a + r.bb * r.ventas, 0) / ventas : 0;
      return {
        marca: m, ventas, uds: rs.reduce((a, r) => a + r.uds, 0), asins: rs.length,
        vel, delta, bb, senal: señal(vel, velPrev || null),
      };
    });
  }, [rows]);

  const totales = useMemo(() => {
    const ventas = rows.reduce((a, r) => a + r.ventas, 0);
    return {
      ventas,
      uds: rows.reduce((a, r) => a + r.uds, 0),
      vel: rows.reduce((a, r) => a + (r.vel || 0), 0),
      asins: rows.length,
      bb: ventas > 0 ? rows.reduce((a, r) => a + r.bb * r.ventas, 0) / ventas : 0,
    };
  }, [rows]);

  const velChartData = useMemo(() => {
    const series = BRANDS.map((m) => ({ m, data: brandVelocitySeries(snapshots, m) }));
    const fechas = [...new Set(series.flatMap((s) => s.data.map((d) => d.fecha)))].sort();
    return fechas.map((f) => {
      const row = { fecha: f };
      for (const s of series) row[s.m] = s.data.find((d) => d.fecha === f)?.vel ?? null;
      return row;
    });
  }, [snapshots]);

  const rowsMarca = rows.filter((r) => r.marca === marca && (tipo === 'TODOS' || r.tipo === tipo));
  const tiposDisponibles = ['TODOS', ...new Set(rows.filter((r) => r.marca === marca).map((r) => r.tipo))];

  const compareData = useMemo(() => {
    if (seleccion.length === 0) return [];
    const series = seleccion.map((a) => ({ a, data: velocitySeries(snapshots, a) }));
    const fechas = [...new Set(series.flatMap((s) => s.data.map((d) => d.fecha)))].sort();
    return fechas.map((f) => {
      const row = { fecha: f };
      for (const s of series) row[s.a] = s.data.find((d) => d.fecha === f)?.vel ?? null;
      return row;
    });
  }, [seleccion, snapshots]);

  const urgentes = alerts.filter((a) => a.nivel === 'urgente');
  const perdidaTotal = urgentes.reduce((a, x) => a + (x.perdida || 0), 0);

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto', padding: 20, display: 'grid', gap: 16 }}>
      <header style={{ display: 'flex', alignItems: 'baseline', gap: 12, flexWrap: 'wrap' }}>
        <h1 style={{ margin: 0, fontSize: 20 }}>Dashboard Vinfermaton</h1>
        <span style={{ color: COLORS.muted, fontSize: 13 }}>
          Laboratorios Vinfer · Amazon España · corte {curr.fecha}
          {prev ? ` vs ${prev.fecha}` : ' (sin periodo de comparación)'}
        </span>
      </header>

      <nav style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
        {TABS.map((t) => (
          <button
            key={t} onClick={() => setTab(t)}
            style={{
              background: tab === t ? COLORS.card : 'transparent',
              color: tab === t ? COLORS.text : COLORS.muted,
              border: `1px solid ${tab === t ? COLORS.border : 'transparent'}`,
              borderRadius: 8, padding: '6px 12px',
            }}
          >
            {t}
          </button>
        ))}
      </nav>

      <div className="card" style={{ display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'center' }}>
        <span style={{ color: COLORS.muted, fontSize: 12 }}>Periodo</span>
        <select
          value={idxPrev} onChange={(e) => setIdxPrev(Number(e.target.value))}
          style={{ background: COLORS.bg, color: COLORS.text, border: `1px solid ${COLORS.border}`, borderRadius: 6, padding: '6px 8px' }}
        >
          {snapshots.map((s, i) => <option key={s.fecha} value={i}>{s.fecha}</option>)}
        </select>
        <span style={{ color: COLORS.muted }}>→</span>
        <select
          value={idxCurr} onChange={(e) => setIdxCurr(Number(e.target.value))}
          style={{ background: COLORS.bg, color: COLORS.text, border: `1px solid ${COLORS.border}`, borderRadius: 6, padding: '6px 8px' }}
        >
          {snapshots.map((s, i) => <option key={s.fecha} value={i}>{s.fecha}</option>)}
        </select>
      </div>

      {tab === 'General' && (
        <>
          <KpiRow items={[
            { label: 'Ventas acumuladas', value: eur(totales.ventas) },
            { label: 'Unidades', value: num(totales.uds) },
            { label: 'Velocidad', value: `${num(totales.vel)} €/sem` },
            { label: 'ASINs', value: totales.asins },
            {
              label: 'BB medio (pond.)',
              value: `${totales.bb.toFixed(1)}%`,
              color: totales.bb >= 90 ? COLORS.green : totales.bb >= 70 ? COLORS.orange : COLORS.red,
            },
            {
              label: 'Fuga BuyBox',
              value: eur(perdidaTotal),
              color: perdidaTotal > 0 ? COLORS.red : COLORS.muted,
              sub: `${urgentes.length} productos críticos`,
            },
          ]} />

          <div className="card">
            <h2 style={{ margin: '0 0 12px', fontSize: 15 }}>Velocidad semanal por marca (€/sem)</h2>
            <VelocityChart
              data={velChartData}
              series={BRANDS.map((m) => ({ key: m, name: m, color: MARCA_LINE[m] }))}
            />
          </div>

          <div className="card">
            <h2 style={{ margin: '0 0 12px', fontSize: 15 }}>Marcas</h2>
            <BrandTable marcas={marcasResumen} onSelect={(m) => { setMarca(m); setTipo('TODOS'); setTab('Por marca'); }} />
          </div>

          <div className="card">
            <h2 style={{ margin: '0 0 12px', fontSize: 15 }}>Alertas ({alerts.length})</h2>
            <AlertList alerts={alerts} />
          </div>
        </>
      )}

      {tab === 'Por marca' && (
        <>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {marcasResumen.map((m) => (
              <button
                key={m.marca} onClick={() => { setMarca(m.marca); setTipo('TODOS'); }}
                style={{
                  background: marca === m.marca ? MARCA_LINE[m.marca] : COLORS.card,
                  color: marca === m.marca ? COLORS.bg : COLORS.text,
                  border: `1px solid ${COLORS.border}`, borderRadius: 8, padding: '6px 12px', fontWeight: 600,
                }}
              >
                {m.marca}
              </button>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {tiposDisponibles.map((t) => (
              <button
                key={t} onClick={() => setTipo(t)}
                style={{
                  background: 'transparent', color: tipo === t ? COLORS.text : COLORS.muted,
                  border: `1px solid ${tipo === t ? COLORS.border : 'transparent'}`,
                  borderRadius: 6, padding: '4px 10px', fontSize: 12,
                }}
              >
                {t}
              </button>
            ))}
          </div>
          <div className="card">
            <h2 style={{ margin: '0 0 12px', fontSize: 15 }}>
              {marca} — {rowsMarca.length} ASINs
            </h2>
            <ProductTable
              rows={rowsMarca}
              selected={seleccion}
              onToggleSelect={(a) => setSeleccion((s) =>
                s.includes(a) ? s.filter((x) => x !== a) : s.length < 5 ? [...s, a] : s)}
            />
            <div style={{ color: COLORS.muted, fontSize: 12, marginTop: 8 }}>
              Marca hasta 5 productos y ve sus curvas en la pestaña Histórico.
            </div>
          </div>
        </>
      )}

      {tab === 'Histórico' && (
        <>
          <div className="card">
            <h2 style={{ margin: '0 0 12px', fontSize: 15 }}>
              Comparativa de productos {seleccion.length ? `(${seleccion.length})` : ''}
            </h2>
            {seleccion.length === 0
              ? <div style={{ color: COLORS.muted }}>Selecciona productos en la pestaña “Por marca”.</div>
              : <VelocityChart
                  data={compareData}
                  series={seleccion.map((a, i) => ({
                    key: a, name: rows.find((r) => r.asin === a)?.titulo || a,
                    color: ['#4ADE80', '#60A5FA', '#FBBF24', '#A78BFA', '#F472B6'][i % 5],
                  }))}
                />}
          </div>
          <div className="card">
            <h2 style={{ margin: '0 0 12px', fontSize: 15 }}>Heatmap BuyBox — {marca}</h2>
            <BuyBoxHeatmap snapshots={snapshots} marca={marca} />
          </div>
          <div className="card">
            <h2 style={{ margin: '0 0 12px', fontSize: 15 }}>
              Productos en riesgo ({enRiesgo.length}) — BuyBox y velocidad bajando a la vez
            </h2>
            {enRiesgo.length === 0
              ? <div style={{ color: COLORS.muted }}>Ninguno en este periodo.</div>
              : <ProductTable rows={enRiesgo} />}
          </div>
        </>
      )}

      {tab === 'Proyecciones' && <Projections rows={rows} desde={curr.fecha} />}

      {tab === 'Datos' && (
        <>
          <Upload onSnapshot={(snap) => setSnapshots((s) => addSnapshot(s, snap))} />
          <div className="card">
            <h2 style={{ margin: '0 0 12px', fontSize: 15 }}>Informes cargados</h2>
            <table>
              <thead><tr><th>Corte</th><th>Origen</th><th>ASINs</th><th /></tr></thead>
              <tbody>
                {snapshots.map((s) => (
                  <tr key={s.fecha}>
                    <td>{s.fecha}</td>
                    <td style={{ color: COLORS.muted }}>{s.origen}</td>
                    <td>{s.rows.length}</td>
                    <td>
                      <button
                        onClick={() => setSnapshots((prevS) => removeSnapshot(prevS, s.fecha))}
                        style={{ background: 'transparent', color: COLORS.red, border: 'none' }}
                      >
                        Eliminar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <button
              onClick={() => setSnapshots(resetSnapshots())}
              style={{ marginTop: 12, background: 'transparent', color: COLORS.muted, border: `1px solid ${COLORS.border}`, borderRadius: 6, padding: '6px 12px' }}
            >
              Reiniciar a datos iniciales
            </button>
          </div>
        </>
      )}
    </div>
  );
}
