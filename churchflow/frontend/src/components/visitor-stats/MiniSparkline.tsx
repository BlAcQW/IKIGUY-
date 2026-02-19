/**
 * Mini Sparkline Component
 *
 * Displays a compact trend visualization using Recharts.
 * Perfect for showing historical data in summary cards.
 */

import { AreaChart, Area, ResponsiveContainer } from 'recharts';

interface MiniSparklineProps {
  data: number[];
  color: 'purple' | 'blue' | 'green' | 'orange';
  height?: number;
}

const colorMap = {
  purple: '#9333ea',
  blue: '#3b82f6',
  green: '#10b981',
  orange: '#f59e0b',
};

export default function MiniSparkline({
  data,
  color,
  height = 40,
}: MiniSparklineProps) {
  // Transform array of numbers into format Recharts expects
  const chartData = data.map((value, index) => ({
    index,
    value,
  }));

  const strokeColor = colorMap[color];
  const gradientId = `gradient-${color}`;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart
        data={chartData}
        margin={{ top: 0, right: 0, left: 0, bottom: 0 }}
      >
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={strokeColor} stopOpacity={0.3} />
            <stop offset="95%" stopColor={strokeColor} stopOpacity={0} />
          </linearGradient>
        </defs>
        <Area
          type="monotone"
          dataKey="value"
          stroke={strokeColor}
          strokeWidth={2}
          fill={`url(#${gradientId})`}
          animationDuration={1000}
          animationEasing="ease-out"
          isAnimationActive={true}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
