import { daysBetween } from './store.js';

/**
 * Proyección a una fecha objetivo a partir de la velocidad actual por producto,
 * con multiplicadores manuales por tipo (ej: vendimia -> AVISPAS x1.4).
 *
 * Escenarios: lineal mantiene la velocidad; bueno y muy bueno aplican un
 * factor adicional sobre el tramo proyectado.
 */
export const FACTORES = { lineal: 1.0, bueno: 1.25, muyBueno: 1.45 };

export function proyectar(rows, { desde, hasta, multiplicadores = {} }) {
  const dias = daysBetween(desde, hasta);
  const semanas = dias / 7;

  const base = rows.reduce((acc, r) => acc + (r.ventas || 0), 0);

  const incrementoLineal = rows.reduce((acc, r) => {
    const mult = multiplicadores[r.tipo] ?? 1;
    return acc + (r.vel || 0) * semanas * mult;
  }, 0);

  return {
    dias,
    semanas: Math.round(semanas * 10) / 10,
    base: Math.round(base),
    escenarios: Object.fromEntries(
      Object.entries(FACTORES).map(([k, f]) => [k, Math.round(base + incrementoLineal * f)]),
    ),
  };
}

/** Trayectoria semanal para el gráfico de área. */
export function trayectoria(rows, { desde, hasta, multiplicadores = {} }) {
  const dias = daysBetween(desde, hasta);
  const pasos = Math.max(1, Math.ceil(dias / 7));
  const base = rows.reduce((acc, r) => acc + (r.ventas || 0), 0);
  const velSemanal = rows.reduce((acc, r) => acc + (r.vel || 0) * (multiplicadores[r.tipo] ?? 1), 0);

  const punto = (semanas, fecha) => ({
    semana: Math.round(semanas * 10) / 10,
    fecha,
    lineal: Math.round(base + velSemanal * semanas * FACTORES.lineal),
    bueno: Math.round(base + velSemanal * semanas * FACTORES.bueno),
    muyBueno: Math.round(base + velSemanal * semanas * FACTORES.muyBueno),
  });

  const out = [punto(0, desde)];
  for (let i = 1; i < pasos; i++) {
    const d = new Date(desde + 'T00:00:00Z');
    d.setUTCDate(d.getUTCDate() + i * 7);
    out.push(punto(i, d.toISOString().slice(0, 10)));
  }
  // El último punto es la fecha objetivo exacta, no la semana redondeada.
  out.push(punto(dias / 7, hasta));
  return out;
}
