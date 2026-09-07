/**
 * Alertas automáticas. Los umbrales son los acordados con el cliente;
 * cambiarlos aquí cambia todo el dashboard.
 */
export const UMBRALES = {
  bbUrgente: 55,
  ventasMinimasUrgente: 500,
  bbMedio: 70,
  caidaVelocidad: -0.30,
  subidaVelocidad: 0.20,
  nuevoRelevante: 100,
};

export function buildAlerts(rows) {
  const alerts = [];

  for (const r of rows) {
    if (r.bb < UMBRALES.bbUrgente && r.ventas > UMBRALES.ventasMinimasUrgente) {
      alerts.push({
        nivel: 'urgente',
        asin: r.asin,
        titulo: r.titulo,
        marca: r.marca,
        // Pérdida estimada: las ventas que se van al competidor que gana la BB.
        perdida: Math.round((r.ventas / (r.bb / 100)) - r.ventas),
        msg: `BuyBox ${r.bb.toFixed(1)}% con ${Math.round(r.ventas).toLocaleString('es-ES')} € de ventas. Repricing inmediato.`,
      });
      continue;
    }

    if (r.bb < UMBRALES.bbMedio && r.ventas > 0) {
      alerts.push({
        nivel: 'medio',
        asin: r.asin,
        titulo: r.titulo,
        marca: r.marca,
        msg: `BuyBox ${r.bb.toFixed(1)}% — por debajo del ${UMBRALES.bbMedio}%.`,
      });
    }

    if (r.velPrev != null && r.velPrev > 0 && r.vel != null) {
      const cambio = (r.vel - r.velPrev) / r.velPrev;
      if (cambio <= UMBRALES.caidaVelocidad) {
        alerts.push({
          nivel: 'medio',
          asin: r.asin,
          titulo: r.titulo,
          marca: r.marca,
          msg: `Velocidad ${(cambio * 100).toFixed(0)}% vs semana anterior (${Math.round(r.velPrev)} → ${Math.round(r.vel)} €/sem).`,
        });
      } else if (cambio >= UMBRALES.subidaVelocidad) {
        alerts.push({
          nivel: 'positivo',
          asin: r.asin,
          titulo: r.titulo,
          marca: r.marca,
          msg: `Velocidad +${(cambio * 100).toFixed(0)}% (${Math.round(r.velPrev)} → ${Math.round(r.vel)} €/sem).`,
        });
      }
    }

    if (r.esNuevo) {
      alerts.push({
        nivel: r.vel != null && r.vel > UMBRALES.nuevoRelevante ? 'positivo' : 'nuevo',
        asin: r.asin,
        titulo: r.titulo,
        marca: r.marca,
        msg: r.vel != null && r.vel > UMBRALES.nuevoRelevante
          ? `Producto nuevo arrancando fuerte: ${Math.round(r.vel)} €/sem.`
          : 'Producto nuevo, primera aparición en el informe.',
      });
    }
  }

  const orden = { urgente: 0, medio: 1, positivo: 2, nuevo: 3 };
  alerts.sort((a, b) => (orden[a.nivel] - orden[b.nivel]) || ((b.perdida || 0) - (a.perdida || 0)));
  return alerts;
}

/** Productos en riesgo: BB bajando Y velocidad bajando a la vez. */
export function productosEnRiesgo(rows) {
  return rows
    .filter((r) => r.deltaBB != null && r.deltaBB < 0 && r.velPrev != null && r.vel != null && r.vel < r.velPrev)
    .sort((a, b) => b.ventas - a.ventas);
}
