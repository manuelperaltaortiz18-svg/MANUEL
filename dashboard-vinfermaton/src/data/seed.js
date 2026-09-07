/** Datos históricos de arranque (consultoría, 3 jun -> 1 sep 2026). */

export const HISTORICO_VELOCIDAD_VM = [
  { fecha: '2026-06-09', vel: 9302, label: 'Base junio' },
  { fecha: '2026-06-16', vel: 11305, label: 'Acelerando' },
  { fecha: '2026-06-23', vel: 13486, label: 'Pre-Prime' },
  { fecha: '2026-06-29', vel: 19617, label: 'Post-Prime' },
  { fecha: '2026-07-07', vel: 21701, label: 'PICO' },
  { fecha: '2026-07-13', vel: 19462, label: 'Normalizando' },
  { fecha: '2026-07-17', vel: 18126, label: 'Estable alto' },
  { fecha: '2026-07-28', vel: 9955, label: 'Normalización' },
  { fecha: '2026-08-03', vel: 9703, label: 'Estable bajo' },
  { fecha: '2026-08-11', vel: 7406, label: 'Valle' },
  { fecha: '2026-08-19', vel: 5234, label: 'Valle profundo' },
  { fecha: '2026-08-25', vel: 4712, label: 'Mínimo' },
  { fecha: '2026-09-01', vel: 3598, label: 'Mínimo absoluto' },
];

export const MARCAS_ACUMULADO_01SEP = {
  Vinfermaton: { ventas: 191539, uds: 12228, asins: 31, bb: 78.6, vel: 3598 },
  Wins: { ventas: 27793, uds: 2179, asins: 25, bb: 82.6, vel: 792 },
  Bioleaf: { ventas: 16283, uds: 1427, asins: 11, bb: 98.7, vel: 367 },
  Vinfer: { ventas: 10839, uds: 1192, asins: 12, bb: 90.2, vel: 475 },
  Vincare: { ventas: 1874, uds: 156, asins: 5, bb: 86.8, vel: 35 },
};

/**
 * Acumulado por marca en cada corte semanal. Permite el selector de periodo
 * antes de haber subido ningún CSV.
 */
export const HISTORICO_MARCAS = [
  { fecha: '2026-06-03', Vinfermaton: 42401, Wins: 16457, Bioleaf: 10721, Vinfer: 6738, Vincare: 1162 },
  { fecha: '2026-06-09', Vinfermaton: 50374, Wins: 16951, Bioleaf: 11330, Vinfer: 7017, Vincare: 1265 },
  { fecha: '2026-06-16', Vinfermaton: 61680, Wins: 17692, Bioleaf: 11740, Vinfer: 7354, Vincare: 1265 },
  { fecha: '2026-06-23', Vinfermaton: 75166, Wins: 18599, Bioleaf: 12029, Vinfer: 7642, Vincare: 1275 },
  { fecha: '2026-06-29', Vinfermaton: 92572, Wins: 19309, Bioleaf: 12570, Vinfer: 7874, Vincare: 1345 },
  { fecha: '2026-07-07', Vinfermaton: 117825, Wins: 20303, Bioleaf: 13247, Vinfer: 8216, Vincare: 1360 },
  { fecha: '2026-07-13', Vinfermaton: 134506, Wins: 21875, Bioleaf: 13597, Vinfer: 8504, Vincare: 1385 },
  { fecha: '2026-07-17', Vinfermaton: 144864, Wins: 22681, Bioleaf: 13744, Vinfer: 8659, Vincare: 1438 },
  { fecha: '2026-07-28', Vinfermaton: 160507, Wins: 24102, Bioleaf: 14420, Vinfer: 9323, Vincare: 1622 },
  { fecha: '2026-08-03', Vinfermaton: 168824, Wins: 25053, Bioleaf: 14822, Vinfer: 9599, Vincare: 1681 },
  { fecha: '2026-08-06', Vinfermaton: 172630, Wins: 25436, Bioleaf: 15038, Vinfer: 9747, Vincare: 1694 },
  { fecha: '2026-08-11', Vinfermaton: 177920, Wins: 25691, Bioleaf: 15318, Vinfer: 9895, Vincare: 1694 },
  { fecha: '2026-08-19', Vinfermaton: 183902, Wins: 26399, Bioleaf: 15605, Vinfer: 10190, Vincare: 1764 },
  { fecha: '2026-08-25', Vinfermaton: 187941, Wins: 27001, Bioleaf: 15917, Vinfer: 10364, Vincare: 1839 },
  { fecha: '2026-09-01', Vinfermaton: 191539, Wins: 27793, Bioleaf: 16283, Vinfer: 10839, Vincare: 1874 },
];

/** Productos Vinfermaton a 1 sep, como snapshot inicial navegable. */
export const PRODUCTOS_01SEP = [
  ['Avispas Pack 2x600ml', 'B0FDL4Q2JB', 7391, 127156, 1637, 97.8, 'AVISPAS'],
  ['Hormigas Pack nuevo', 'B0H4FZYK8Z', 820, 13325, 550, 98.0, 'INSECT'],
  ['Mosquitos Pack', 'B0H6BQ4BG5', 656, 8894, 330, 52.4, 'MOSQUITOS'],
  ['Fregasuelos Insecticida', 'B0GTZB24Q5', 455, 6751, 0, 98.7, 'INSECT'],
  ['Cucarachas Residual', 'B06XD39V8J', 795, 6068, 15, 47.3, 'INSECT'],
  ['Hormigas Residual', 'B0FH2NLMGN', 377, 5591, 0, 91.5, 'INSECT'],
  ['Antihormigas Permanente', 'B0FGDF2SHZ', 352, 5530, 177, 87.4, 'INSECT'],
  ['Antipolillas 300ml', 'B0FHQJSLGJ', 342, 4385, 357, 99.1, 'ANTIPOLILLAS'],
  ['Cucarachas Instantáneo', 'B0FHKR4Q45', 198, 2539, 122, 97.8, 'INSECT'],
  ['Fregasuelos Pack NUEVO', 'B0H9YSCFRW', 173, 2511, 228, 95.9, 'INSECT'],
  ['Moscas Sin Olor', 'B0FHKQHYQ7', 173, 2473, 15, 94.8, 'MOSCAS'],
  ['Moscas Limón', 'B0FDKX6V41', 127, 1519, 35, 96.3, 'MOSCAS'],
  ['Cucar. Larga Duración', 'B0FH9NPJ1K', 72, 935, 13, 88.7, 'INSECT'],
  ['Mosquitos Individual', 'B0FGDGV4V4', 53, 780, 30, 96.6, 'MOSQUITOS'],
  ['Moscas Repelente', 'B0FDL3VP7W', 64, 762, 24, 97.3, 'MOSCAS'],
  ['Triple Acción Avispas', 'B0FH71NBJL', 21, 564, 0, 97.1, 'AVISPAS'],
  ['Avispas Individual', 'B0FGDJJ12N', 46, 552, 24, 87.9, 'AVISPAS'],
  ['Matón Cucas Individual', 'B07F8Z6XL1', 59, 464, 16, 53.1, 'INSECT'],
  ['Multiinsectos', 'B0FMRN3BNT', 16, 240, 15, 94.8, 'INSECT'],
  ['Repelente Insectos', 'B0DB2647JX', 19, 161, 0, 98.9, 'REPELENTE'],
  ['PRO Laca I-79', 'B0HCZ2WBRT', 2, 30, 0, 100, 'INSECT'],
  ['PRO I-96 Avispas', 'B0H4NLXP9W', 1, 15, 0, 92.3, 'AVISPAS'],
  ['PRO L-98 Limpiador', 'B0H4NQPFV1', 1, 15, 0, 100, 'INSECT'],
].map(([titulo, asin, uds, ventas, vel, bb, tipo]) => ({
  titulo, asin, uds, ventas, vel, bb, tipo, marca: 'Vinfermaton',
}));

/** Snapshot inicial en el mismo formato que produce el parser de CSV. */
export const SEED_SNAPSHOT = {
  fecha: '2026-09-01',
  origen: 'seed',
  // `vel` se conserva para que los KPIs tengan sentido antes de subir un
  // segundo informe (con un solo corte no hay delta del que calcularla).
  rows: PRODUCTOS_01SEP.map(({ titulo, asin, uds, ventas, vel, bb, tipo, marca }) => ({
    titulo, asin, uds, ventas, vel, bb, tipo, marca, sesiones: 0,
  })),
};
