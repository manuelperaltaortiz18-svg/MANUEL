import { parseAmazonInt, parseAmazonCurrency, parseAmazonPercent } from './parseValue.js';
import { classifyBrand, classifyTipo } from './classify.js';

/** Split de una línea CSV respetando comillas. */
export function splitLine(line, delim) {
  const out = [];
  let cur = '';
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const c = line[i];
    if (c === '"') {
      if (inQuotes && line[i + 1] === '"') { cur += '"'; i++; }
      else inQuotes = !inQuotes;
    } else if (c === delim && !inQuotes) {
      out.push(cur); cur = '';
    } else {
      cur += c;
    }
  }
  out.push(cur);
  return out.map((s) => s.trim());
}

/**
 * Detecta el delimitador. Amazon ES exporta con ";" o con "," según la
 * configuración regional de la cuenta, así que no se puede asumir.
 */
export function detectDelimiter(headerLine) {
  const candidates = [';', ',', '\t'];
  let best = ';';
  let bestCount = -1;
  for (const d of candidates) {
    const count = splitLine(headerLine, d).length;
    if (count > bestCount) { bestCount = count; best = d; }
  }
  return best;
}

const norm = (s) =>
  (s || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, ' ').trim();

/** Localiza columnas por nombre aproximado, tolerando variantes de Amazon. */
function findCol(headers, ...needles) {
  const H = headers.map(norm);
  for (const needle of needles) {
    const n = norm(needle);
    const exact = H.indexOf(n);
    if (exact !== -1) return exact;
  }
  for (const needle of needles) {
    const n = norm(needle);
    const idx = H.findIndex((h) => h.includes(n));
    if (idx !== -1) return idx;
  }
  return -1;
}

/**
 * Parsea un Business Report y devuelve filas agrupadas por ASIN parent.
 * Devuelve { rows, warnings, headers }.
 */
export function parseBusinessReport(text) {
  const warnings = [];
  const lines = text.split(/\r?\n/).filter((l) => l.trim() !== '');
  if (lines.length < 2) return { rows: [], warnings: ['CSV vacío o sin filas de datos.'], headers: [] };

  const delim = detectDelimiter(lines[0]);
  const headers = splitLine(lines[0], delim).map((h) => h.replace(/^"|"$/g, ''));

  const cTitulo = findCol(headers, 'titulo', 'title', 'nombre del producto');
  const cParent = findCol(headers, 'asin parent', 'asin (parent)', 'parent asin');
  const cChild = findCol(headers, 'asin child', 'asin (child)', 'child asin', 'asin');
  const cBB = findCol(headers, 'porcentaje de ofertas destacadas', 'buy box', 'featured offer');
  const cUds = findCol(headers, 'unidades encargadas', 'units ordered');
  const cVentas = findCol(headers, 'ventas de productos encargados', 'ordered product sales');
  const cSesiones = findCol(headers, 'sesiones total', 'sessions total', 'sesiones');

  if (cVentas === -1) warnings.push('No se encontró la columna de ventas; los importes serán 0.');
  if (cUds === -1) warnings.push('No se encontró la columna de unidades.');
  if (cParent === -1 && cChild === -1) warnings.push('No se encontró ninguna columna de ASIN.');

  // Agregación por ASIN parent (nunca por SKU individual).
  const byAsin = new Map();

  for (let i = 1; i < lines.length; i++) {
    const f = splitLine(lines[i], delim).map((s) => s.replace(/^"|"$/g, ''));
    const asin = (cParent !== -1 ? f[cParent] : '') || (cChild !== -1 ? f[cChild] : '');
    if (!asin) continue;

    const titulo = cTitulo !== -1 ? f[cTitulo] : '';
    const ventas = cVentas !== -1 ? parseAmazonCurrency(f[cVentas]) : 0;
    const uds = cUds !== -1 ? parseAmazonInt(f[cUds]) : 0;
    const bb = cBB !== -1 ? parseAmazonPercent(f[cBB]) : 0;
    const sesiones = cSesiones !== -1 ? parseAmazonInt(f[cSesiones]) : 0;

    const prev = byAsin.get(asin);
    if (prev) {
      prev.ventas += ventas;
      prev.uds += uds;
      prev.sesiones += sesiones;
      // BB agregado: ponderado por ventas, que es lo que nos importa proteger.
      prev._bbPeso += bb * (ventas || 1);
      prev._peso += ventas || 1;
      if (!prev.titulo && titulo) prev.titulo = titulo;
    } else {
      byAsin.set(asin, {
        asin,
        titulo,
        marca: classifyBrand(titulo, asin),
        tipo: classifyTipo(titulo),
        ventas,
        uds,
        sesiones,
        _bbPeso: bb * (ventas || 1),
        _peso: ventas || 1,
      });
    }
  }

  const rows = [...byAsin.values()].map((r) => {
    const bb = r._peso > 0 ? r._bbPeso / r._peso : 0;
    delete r._bbPeso;
    delete r._peso;
    return { ...r, bb: Math.round(bb * 10) / 10 };
  });

  rows.sort((a, b) => b.ventas - a.ventas);

  const sinMarca = rows.filter((r) => r.marca === 'Otros').length;
  if (sinMarca > 0) warnings.push(`${sinMarca} ASINs no se pudieron clasificar por marca (marca "Otros").`);

  return { rows, warnings, headers, delimiter: delim };
}
