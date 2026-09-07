import { describe, it, expect } from 'vitest';
import { parseAmazonInt, parseAmazonCurrency, parseAmazonPercent } from '../src/lib/parseValue.js';
import { classifyBrand, classifyTipo } from '../src/lib/classify.js';
import { splitLine, detectDelimiter, parseBusinessReport } from '../src/lib/csv.js';
import { daysBetween, diffSnapshots } from '../src/lib/store.js';
import { buildAlerts } from '../src/lib/alerts.js';

describe('parseAmazonInt', () => {
  it('trata la coma como separador de miles', () => {
    expect(parseAmazonInt('2,800')).toBe(2800);
    expect(parseAmazonInt('1.234')).toBe(1234);
    expect(parseAmazonInt('12')).toBe(12);
    expect(parseAmazonInt('')).toBe(0);
  });
});

describe('parseAmazonCurrency', () => {
  it('parsea formato es-ES', () => {
    expect(parseAmazonCurrency('48.541,14')).toBeCloseTo(48541.14);
    expect(parseAmazonCurrency('127.156,00 €')).toBeCloseTo(127156);
    expect(parseAmazonCurrency('12,50')).toBeCloseTo(12.5);
  });
  it('no convierte 2,800 en 2.8 (el bug clásico)', () => {
    expect(parseAmazonCurrency('2,800')).toBe(2800);
  });
  it('tolera formato en-US', () => {
    expect(parseAmazonCurrency('2,800.50')).toBeCloseTo(2800.5);
  });
  it('devuelve 0 ante basura', () => {
    expect(parseAmazonCurrency('n/a')).toBe(0);
    expect(parseAmazonCurrency(null)).toBe(0);
  });
});

describe('parseAmazonPercent', () => {
  it('usa el punto como decimal', () => {
    expect(parseAmazonPercent('95.11')).toBeCloseTo(95.11);
    expect(parseAmazonPercent('52,4%')).toBeCloseTo(52.4);
  });
});

describe('classifyBrand', () => {
  it('prioriza Vinfermaton sobre Vinfer', () => {
    expect(classifyBrand('VINFERMATON Avispas Pack')).toBe('Vinfermaton');
    expect(classifyBrand('VINFERMATÓN Moscas')).toBe('Vinfermaton');
    expect(classifyBrand('Matón Cucarachas')).toBe('Vinfermaton');
    expect(classifyBrand('VINFER Limpiainox 600ml')).toBe('Vinfer');
  });
  it('aplica el override por ASIN', () => {
    expect(classifyBrand('Limpiasalpicaderos 750ml', 'B00ID2NEMS')).toBe('Vinfer');
  });
  it('clasifica el resto de marcas', () => {
    expect(classifyBrand('BIOLEAF Gel WC')).toBe('Bioleaf');
    expect(classifyBrand('WINS Fregasuelos 5L')).toBe('Wins');
    expect(classifyBrand('VINCARE Biberones')).toBe('Vincare');
    expect(classifyBrand('Producto sin marca')).toBe('Otros');
  });
});

describe('classifyTipo', () => {
  it('detecta la familia por título', () => {
    expect(classifyTipo('Insecticida Avispas 600ml')).toBe('AVISPAS');
    expect(classifyTipo('Antimosquitos pack')).toBe('MOSQUITOS');
    expect(classifyTipo('Antipolillas 300ml')).toBe('ANTIPOLILLAS');
    expect(classifyTipo('Cucarachas residual')).toBe('INSECT');
  });
});

describe('csv', () => {
  it('respeta comillas al partir la línea', () => {
    expect(splitLine('a;"b;c";d', ';')).toEqual(['a', 'b;c', 'd']);
    expect(splitLine('a,"1,234",b', ',')).toEqual(['a', '1,234', 'b']);
  });
  it('detecta el delimitador', () => {
    expect(detectDelimiter('a;b;c;d')).toBe(';');
    expect(detectDelimiter('a,b,c,d')).toBe(',');
  });

  const csv = [
    'SKU;Título;ASIN (parent);ASIN (child);Sesiones: total;Porcentaje de ofertas destacadas (Buy Box);Unidades encargadas;Ventas de productos encargados',
    'SKU1;VINFERMATON Avispas Pack 2x600ml;B0FDL4Q2JB;B0FDL4Q2JB;3,200;97.80;7,391;127.156,00',
    'SKU2;VINFERMATON Mosquitos Pack;B0H6BQ4BG5;B0H6BQ4BG5;900;52.40;656;8.894,00',
    'SKU2B;VINFERMATON Mosquitos Pack;B0H6BQ4BG5;B0H6BQ4BG6;100;52.40;44;1.106,00',
  ].join('\n');

  it('parsea y agrupa por ASIN parent', () => {
    const { rows } = parseBusinessReport(csv);
    expect(rows).toHaveLength(2);
    const avispas = rows.find((r) => r.asin === 'B0FDL4Q2JB');
    expect(avispas.ventas).toBeCloseTo(127156);
    expect(avispas.uds).toBe(7391);
    expect(avispas.marca).toBe('Vinfermaton');
    expect(avispas.tipo).toBe('AVISPAS');

    // Los dos child se suman bajo el mismo parent.
    const mosquitos = rows.find((r) => r.asin === 'B0H6BQ4BG5');
    expect(mosquitos.ventas).toBeCloseTo(10000);
    expect(mosquitos.uds).toBe(700);
    expect(mosquitos.bb).toBeCloseTo(52.4, 1);
  });
});

describe('velocidad', () => {
  it('normaliza a 7 días aunque el corte no sea semanal', () => {
    expect(daysBetween('2026-08-25', '2026-09-01')).toBe(7);
    expect(daysBetween('2026-07-17', '2026-07-28')).toBe(11);

    const prev = { fecha: '2026-07-17', rows: [{ asin: 'A', ventas: 1000, uds: 10, bb: 90 }] };
    const curr = { fecha: '2026-07-28', rows: [{ asin: 'A', ventas: 2100, uds: 20, bb: 80 }] };
    const [r] = diffSnapshots(prev, curr);
    expect(r.deltaVentas).toBe(1100);
    expect(r.vel).toBe(700); // 1100 / 11 días * 7
    expect(r.deltaBB).toBe(-10);
  });

  it('marca como nuevos los ASINs sin antecedente', () => {
    const prev = { fecha: '2026-08-25', rows: [] };
    const curr = { fecha: '2026-09-01', rows: [{ asin: 'X', ventas: 500, uds: 5, bb: 99 }] };
    expect(diffSnapshots(prev, curr)[0].esNuevo).toBe(true);
  });
});

describe('alertas', () => {
  it('marca urgente el BB bajo con ventas relevantes', () => {
    const [a] = buildAlerts([
      { asin: 'B0H6BQ4BG5', titulo: 'Mosquitos Pack', marca: 'Vinfermaton', ventas: 8894, bb: 52.4, vel: 330, velPrev: 400 },
    ]);
    expect(a.nivel).toBe('urgente');
    expect(a.perdida).toBeGreaterThan(8000);
  });

  it('no eleva a urgente un BB bajo con ventas irrelevantes', () => {
    const alerts = buildAlerts([
      { asin: 'Z', titulo: 'Residual', marca: 'Wins', ventas: 100, bb: 40, vel: 5, velPrev: 5 },
    ]);
    expect(alerts.every((a) => a.nivel !== 'urgente')).toBe(true);
  });

  it('detecta caídas y subidas de velocidad', () => {
    const caida = buildAlerts([{ asin: 'A', titulo: 'A', marca: 'Vinfermaton', ventas: 5000, bb: 95, vel: 300, velPrev: 1000 }]);
    expect(caida.some((a) => a.msg.includes('Velocidad -70%'))).toBe(true);

    const subida = buildAlerts([{ asin: 'B', titulo: 'B', marca: 'Vinfermaton', ventas: 5000, bb: 95, vel: 1500, velPrev: 1000 }]);
    expect(subida.some((a) => a.nivel === 'positivo')).toBe(true);
  });
});

describe('sin periodo de comparación', () => {
  it('no marca todo como nuevo cuando no hay snapshot previo', () => {
    const curr = { fecha: '2026-09-01', rows: [{ asin: 'A', ventas: 100, uds: 1, bb: 90, vel: 50 }] };
    const [r] = diffSnapshots(null, curr);
    expect(r.esNuevo).toBe(false);
    expect(r.vel).toBe(50); // conserva la velocidad del snapshot semilla
  });
});

describe('proyecciones', () => {
  it('termina exactamente en la fecha objetivo y aplica multiplicadores', async () => {
    const { proyectar, trayectoria } = await import('../src/lib/projections.js');
    const rows = [
      { asin: 'A', tipo: 'AVISPAS', ventas: 100000, vel: 1000 },
      { asin: 'B', tipo: 'MOSQUITOS', ventas: 10000, vel: 1000 },
    ];
    const opts = { desde: '2026-09-01', hasta: '2026-09-29', multiplicadores: { AVISPAS: 1.4, MOSQUITOS: 0.5 } };

    const p = proyectar(rows, opts);
    expect(p.semanas).toBe(4);
    // 4 semanas x (1000*1.4 + 1000*0.5) = 7600 sobre una base de 110.000
    expect(p.escenarios.lineal).toBe(117600);
    expect(p.escenarios.muyBueno).toBeGreaterThan(p.escenarios.bueno);

    const t = trayectoria(rows, opts);
    expect(t.at(0).fecha).toBe('2026-09-01');
    expect(t.at(-1).fecha).toBe('2026-09-29');
    expect(t.at(-1).lineal).toBe(p.escenarios.lineal);
  });
});
