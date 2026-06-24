// gère l'affichage des données de santé
import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceArea,
} from 'recharts';
import { FaChartArea } from 'react-icons/fa';


const VitalSignsChart = ({ data, series, title, normalRange }) => {
  const chartData = data.map((d) => {
    const point = { time: d.timestamp.toLocaleTimeString() };
    series.forEach((s) => {
      point[s.key] = d[s.key];
    });
    return point;
  });

  const primaryUnit = series[0]?.unit || '';

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="rounded-lg border border-gray-200 bg-white p-3 shadow-lg">
          <p className="mb-1 text-sm font-medium text-gray-600">{label}</p>
          {payload.map((entry) => (
            <p key={entry.dataKey} className="text-sm font-semibold" style={{ color: entry.color }}>
              {entry.name} : {entry.value} {series.find((s) => s.key === entry.dataKey)?.unit}
            </p>
          ))}
          {normalRange && (
            <p className="mt-1 text-xs text-gray-500">
              Normal : {normalRange.min}–{normalRange.max} {primaryUnit}
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  const isOutOfRange = (value) => {
    if (!normalRange || value === undefined || value === null) return false;
    return value < normalRange.min || value > normalRange.max;
  };

  const renderDot = (color) => (props) => {
    const { cx, cy, value, index } = props;
    if (cx === undefined || cy === undefined) return null;
    const abnormal = isOutOfRange(value);
    return (
      <circle
        key={`dot-${index}`}
        cx={cx}
        cy={cy}
        r={abnormal ? 4 : 3}
        fill={abnormal ? '#ef4444' : color}
        stroke="#fff"
        strokeWidth={1.5}
      />
    );
  };

  const yDomain = normalRange
    ? [
        Math.min(normalRange.min - 10, ...chartData.flatMap((d) => series.map((s) => d[s.key]).filter((v) => v != null))) ,
        Math.max(normalRange.max + 10, ...chartData.flatMap((d) => series.map((s) => d[s.key]).filter((v) => v != null))),
      ]
    : ['auto', 'auto'];

  return (
    <div className="rounded-xl bg-white p-4 shadow-sm">
      <h3 className="mb-4 font-semibold text-gray-800">{title}</h3>
      <div className="h-72">
        {chartData.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center gap-2 text-gray-400">
            <FaChartArea className="text-3xl" />
            <p className="text-sm">
              Aucune donnée — démarrez le simulateur ou envoyez une mesure
            </p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="time"
                tick={{ fontSize: 11 }}
                minTickGap={20}
              />
              <YAxis
                tick={{ fontSize: 11 }}
                domain={yDomain}
                tickFormatter={(v) => `${v}`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: 12 }} />

              {normalRange && (
                <ReferenceArea
                  y1={normalRange.min}
                  y2={normalRange.max}
                  fill={series[0]?.color || '#0ea5e9'}
                  fillOpacity={0.08}
                  ifOverflow="extendDomain"
                  label={{
                    value: 'Zone normale',
                    position: 'insideTopLeft',
                    fill: '#9ca3af',
                    fontSize: 10,
                  }}
                />
              )}

              {series.map((s) => (
                <Line
                  key={s.key}
                  type="monotone"
                  dataKey={s.key}
                  name={s.name}
                  stroke={s.color}
                  strokeWidth={2}
                  dot={renderDot(s.color)}
                  activeDot={{ r: 6, stroke: '#fff', strokeWidth: 2 }}
                  isAnimationActive={false}
                  connectNulls
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
};

export default VitalSignsChart;
