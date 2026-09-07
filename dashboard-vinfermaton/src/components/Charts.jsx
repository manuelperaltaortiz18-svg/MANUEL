import {
  LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { COLORS, MARCA_LINE, eur } from '../theme.js';

const axis = { stroke: COLORS.muted, fontSize: 12 };
const tooltipStyle = {
  contentStyle: { background: COLORS.card, border: `1px solid ${COLORS.border}`, borderRadius: 8 },
  labelStyle: { color: COLORS.text },
};

export function VelocityChart({ data, series }) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 8 }}>
        <CartesianGrid stroke={COLORS.border} strokeDasharray="3 3" />
        <XAxis dataKey="fecha" {...axis} />
        <YAxis {...axis} tickFormatter={(v) => `${Math.round(v / 1000)}k`} />
        <Tooltip {...tooltipStyle} formatter={(v, n) => [eur(v), n]} />
        {series.length > 1 && <Legend wrapperStyle={{ fontSize: 12 }} />}
        {series.map((s) => (
          <Line
            key={s.key} type="monotone" dataKey={s.key} name={s.name}
            stroke={s.color || MARCA_LINE.Vinfermaton} strokeWidth={2}
            dot={{ r: 2 }} connectNulls isAnimationActive={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

export function ProjectionChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 8 }}>
        <CartesianGrid stroke={COLORS.border} strokeDasharray="3 3" />
        <XAxis dataKey="fecha" {...axis} />
        <YAxis {...axis} tickFormatter={(v) => `${Math.round(v / 1000)}k`} />
        <Tooltip {...tooltipStyle} formatter={(v, n) => [eur(v), n]} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Area type="monotone" dataKey="muyBueno" name="Muy bueno" stroke="#A78BFA" fill="#A78BFA" fillOpacity={0.15} isAnimationActive={false} />
        <Area type="monotone" dataKey="bueno" name="Bueno" stroke="#34D399" fill="#34D399" fillOpacity={0.15} isAnimationActive={false} />
        <Area type="monotone" dataKey="lineal" name="Lineal" stroke="#60A5FA" fill="#60A5FA" fillOpacity={0.2} isAnimationActive={false} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
