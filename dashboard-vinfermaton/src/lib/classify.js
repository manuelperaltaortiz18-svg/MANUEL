/** Clasificación de marca a partir del título del producto (o del ASIN). */

const BRANDS = ['Vinfermaton', 'Wins', 'Bioleaf', 'Vinfer', 'Vincare'];

// Excepción conocida: no lleva marca en el título.
const ASIN_OVERRIDES = { B00ID2NEMS: 'Vinfer' };

export function classifyBrand(titulo, asin) {
  if (asin && ASIN_OVERRIDES[asin]) return ASIN_OVERRIDES[asin];

  const t = (titulo || '')
    .toUpperCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, ''); // VINFERMATÓN -> VINFERMATON

  // El orden importa: "VINFERMATON" contiene "VINFER".
  if (t.includes('VINFERMATON') || t.includes('MATON')) return 'Vinfermaton';
  if (t.includes('BIOLEAF')) return 'Bioleaf';
  if (t.includes('WINS')) return 'Wins';
  if (t.includes('VINCARE')) return 'Vincare';
  if (t.includes('VINFER')) return 'Vinfer';
  return 'Otros';
}

/** Tipo de producto, para el filtro de la vista por marca. */
export function classifyTipo(titulo) {
  const t = (titulo || '')
    .toUpperCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');

  if (t.includes('AVISPA')) return 'AVISPAS';
  if (t.includes('MOSQUITO')) return 'MOSQUITOS';
  if (t.includes('MOSCA')) return 'MOSCAS';
  if (t.includes('POLILLA')) return 'ANTIPOLILLAS';
  if (t.includes('REPELENTE')) return 'REPELENTE';
  if (t.includes('CUCARACHA') || t.includes('HORMIGA') || t.includes('INSECT')) return 'INSECT';
  return 'OTROS';
}

export { BRANDS, ASIN_OVERRIDES };
