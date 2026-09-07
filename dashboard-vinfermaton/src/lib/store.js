import { SEED_SNAPSHOT, HISTORICO_VELOCIDAD_VM, HISTORICO_MARCAS } from '../data/seed.js';

const KEY = 'vinfermaton.snapshots.v1';

/**
 * Un snapshot = un Business Report subido, con su fecha de corte.
 * Las ventas de Amazon vienen ACUMULADAS, así que la velocidad se calcula
 * como delta de acumulado dividido por días reales entre cortes.
 */

export function loadSnapshots() {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return [SEED_SNAPSHOT];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed) || parsed.length === 0) return [SEED_SNAPSHOT];
    return parsed;
  } catch {
    return [SEED_SNAPSHOT];
  }
}

export function saveSnapshots(snapshots) {
  try {
    localStorage.setItem(KEY, JSON.stringify(snapshots));
    return true;
  } catch {
    return false; // cuota llena o modo privado: la sesión sigue funcionando en memoria
  }
}

export function addSnapshot(snapshots, snap) {
  const rest = snapshots.filter((s) => s.fecha !== snap.fecha);
  const next = [...rest, snap].sort((a, b) => a.fecha.localeCompare(b.fecha));
  saveSnapshots(next);
  return next;
}

export function removeSnapshot(snapshots, fecha) {
  const next = snapshots.filter((s) => s.fecha !== fecha);
  saveSnapshots(next);
  return next;
}

export function resetSnapshots() {
  try { localStorage.removeItem(KEY); } catch { /* noop */ }
  return [SEED_SNAPSHOT];
}

export function daysBetween(a, b) {
  const ms = new Date(b + 'T00:00:00Z') - new Date(a + 'T00:00:00Z');
  return Math.max(1, Math.round(ms / 86400000));
}

/**
 * Compara dos snapshots y devuelve las filas del más reciente enriquecidas
 * con delta de ventas, velocidad €/sem y tendencia.
 */
export function diffSnapshots(prev, curr) {
  const prevByAsin = new Map((prev?.rows || []).map((r) => [r.asin, r]));
  const dias = prev ? daysBetween(prev.fecha, curr.fecha) : 7;

  return (curr.rows || []).map((r) => {
    const p = prevByAsin.get(r.asin);
    const delta = p ? r.ventas - p.ventas : null;
    const vel = delta != null ? (delta / dias) * 7 : (r.vel ?? null);
    const deltaBB = p ? r.bb - p.bb : null;

    let tendencia = '→';
    if (p && p.vel != null && vel != null) {
      if (vel > p.vel * 1.1) tendencia = '↑';
      else if (vel < p.vel * 0.9) tendencia = '↓';
    }

    return {
      ...r,
      deltaVentas: delta,
      vel: vel != null ? Math.round(vel) : null,
      velPrev: p?.vel ?? null,
      deltaBB,
      dias,
      // Sin periodo de comparación nada es "nuevo": no hay con qué compararlo.
      esNuevo: prev ? !p : false,
      tendencia,
    };
  });
}

/** Serie de velocidad semanal para un ASIN a lo largo de todos los snapshots. */
export function velocitySeries(snapshots, asin) {
  const out = [];
  for (let i = 1; i < snapshots.length; i++) {
    const prev = snapshots[i - 1];
    const curr = snapshots[i];
    const p = prev.rows.find((r) => r.asin === asin);
    const c = curr.rows.find((r) => r.asin === asin);
    if (!c) continue;
    const dias = daysBetween(prev.fecha, curr.fecha);
    const vel = p ? ((c.ventas - p.ventas) / dias) * 7 : null;
    out.push({ fecha: curr.fecha, vel: vel != null ? Math.round(vel) : null, bb: c.bb });
  }
  return out;
}

/** Velocidad de marca a lo largo del tiempo (incluye el histórico semilla). */
export function brandVelocitySeries(snapshots, marca) {
  const fromSeed = HISTORICO_MARCAS.map((h, i) => {
    if (i === 0) return null;
    const prev = HISTORICO_MARCAS[i - 1];
    const dias = daysBetween(prev.fecha, h.fecha);
    return { fecha: h.fecha, vel: Math.round(((h[marca] - prev[marca]) / dias) * 7) };
  }).filter(Boolean);

  const fromSnaps = [];
  for (let i = 1; i < snapshots.length; i++) {
    const prev = snapshots[i - 1];
    const curr = snapshots[i];
    if (prev.origen === 'seed') continue;
    const sum = (s) => s.rows.filter((r) => r.marca === marca).reduce((a, r) => a + r.ventas, 0);
    const dias = daysBetween(prev.fecha, curr.fecha);
    fromSnaps.push({ fecha: curr.fecha, vel: Math.round(((sum(curr) - sum(prev)) / dias) * 7) });
  }

  const byFecha = new Map(fromSeed.map((d) => [d.fecha, d]));
  for (const d of fromSnaps) byFecha.set(d.fecha, d);
  return [...byFecha.values()].sort((a, b) => a.fecha.localeCompare(b.fecha));
}

export { HISTORICO_VELOCIDAD_VM };
