export const COLORS = {
  bg: '#0F172A',
  card: '#1E293B',
  border: '#334155',
  text: '#E2E8F0',
  muted: '#94A3B8',
  green: '#22C55E',
  orange: '#F59E0B',
  red: '#EF4444',
  blue: '#38BDF8',
};

export const MARCA_COLOR = {
  Vinfermaton: '#1B4332',
  Wins: '#0F3460',
  Bioleaf: '#2D6A4F',
  Vinfer: '#6B4C1E',
  Vincare: '#7C3AED',
  Otros: '#475569',
};

/** Versiones legibles sobre fondo oscuro para las líneas de los gráficos. */
export const MARCA_LINE = {
  Vinfermaton: '#4ADE80',
  Wins: '#60A5FA',
  Bioleaf: '#34D399',
  Vinfer: '#FBBF24',
  Vincare: '#A78BFA',
  Otros: '#94A3B8',
};

export function bbColor(bb) {
  if (bb >= 90) return COLORS.green;
  if (bb >= 70) return COLORS.orange;
  return COLORS.red;
}

export const eur = (n) =>
  (n == null ? '—' : Math.round(n).toLocaleString('es-ES') + ' €');
export const num = (n) => (n == null ? '—' : Math.round(n).toLocaleString('es-ES'));
