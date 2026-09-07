/**
 * Parseo de valores numéricos de los Business Report de Amazon España.
 *
 * Los CSV vienen en formato mixto y ésta es la fuente de casi todos los errores:
 *   - Enteros con coma como separador de miles:  "2,800"     -> 2800
 *   - Moneda es-ES:                              "48.541,14" -> 48541.14
 *   - Porcentajes con punto decimal:             "95.11"     -> 95.11
 *
 * Por eso NO usamos una única heurística: cada columna se parsea sabiendo
 * qué tipo de dato es. `parseAmazonValue` queda como fallback genérico para
 * columnas desconocidas.
 */

function clean(s) {
  if (s == null) return '';
  return String(s)
    .replace(/€/g, '')
    .replace(/\u00a0/g, '')
    .replace(/\u202f/g, '')
    .replace(/\s/g, '')
    .replace(/%/g, '')
    .trim();
}

/** Enteros: unidades, sesiones, vistas de página. Cualquier , o . es de miles. */
export function parseAmazonInt(s) {
  const v = clean(s);
  if (!v) return 0;
  const n = parseFloat(v.replace(/[.,]/g, ''));
  return Number.isFinite(n) ? n : 0;
}

/** Moneda es-ES: "." miles, "," decimal. Tolera también formato en-US. */
export function parseAmazonCurrency(s) {
  const v = clean(s);
  if (!v) return 0;
  const lastComma = v.lastIndexOf(',');
  const lastDot = v.lastIndexOf('.');

  if (lastComma !== -1 && lastDot !== -1) {
    // El separador que aparece más a la derecha es el decimal.
    const n = lastComma > lastDot
      ? parseFloat(v.replace(/\./g, '').replace(',', '.'))
      : parseFloat(v.replace(/,/g, ''));
    return Number.isFinite(n) ? n : 0;
  }

  if (lastComma !== -1) {
    const dec = v.length - lastComma - 1;
    // 3 decimales tras coma en un importe = separador de miles ("2,800").
    const n = dec === 3
      ? parseFloat(v.replace(/,/g, ''))
      : parseFloat(v.replace(',', '.'));
    return Number.isFinite(n) ? n : 0;
  }

  if (lastDot !== -1) {
    const dec = v.length - lastDot - 1;
    const n = dec === 3
      ? parseFloat(v.replace(/\./g, ''))
      : parseFloat(v);
    return Number.isFinite(n) ? n : 0;
  }

  const n = parseFloat(v);
  return Number.isFinite(n) ? n : 0;
}

/** Porcentajes: Amazon los emite con punto decimal ("95.11"), pero aceptamos coma. */
export function parseAmazonPercent(s) {
  const v = clean(s);
  if (!v) return 0;
  const n = parseFloat(v.replace(',', '.'));
  return Number.isFinite(n) ? n : 0;
}

/** Fallback genérico para columnas cuyo tipo no conocemos. */
export function parseAmazonValue(s) {
  if (typeof s === 'number') return s;
  const v = clean(s);
  if (!v) return 0;
  if (v.includes(',')) return parseAmazonCurrency(v);
  return parseAmazonCurrency(v);
}
