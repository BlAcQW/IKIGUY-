/**
 * Comparison Badge Component
 *
 * Displays percentage change between current and previous values.
 * Uses color coding (green=up, red=down, gray=neutral) and directional icons.
 */

import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface ComparisonBadgeProps {
  current: number;
  previous: number;
}

export default function ComparisonBadge({
  current,
  previous,
}: ComparisonBadgeProps) {
  // Don't render if no previous value
  if (!previous || previous === 0) {
    return null;
  }

  // Calculate percentage change
  const change = ((current - previous) / previous) * 100;
  const direction = change > 0 ? 'up' : change < 0 ? 'down' : 'neutral';
  const absChange = Math.abs(change);

  const styles = {
    up: {
      bg: 'bg-green-100/90',
      text: 'text-green-700',
      icon: TrendingUp,
    },
    down: {
      bg: 'bg-red-100/90',
      text: 'text-red-700',
      icon: TrendingDown,
    },
    neutral: {
      bg: 'bg-gray-100/90',
      text: 'text-gray-700',
      icon: Minus,
    },
  };

  const style = styles[direction];
  const Icon = style.icon;

  return (
    <div
      className={`
        inline-flex items-center gap-0.5
        px-1.5 py-0.5 rounded
        ${style.bg} ${style.text}
        text-xs font-bold font-mono
        backdrop-blur-sm
      `}
      role="status"
      aria-label={`${direction === 'up' ? 'Increased' : direction === 'down' ? 'Decreased' : 'No change'} by ${absChange.toFixed(1)}%`}
    >
      <Icon className="w-2.5 h-2.5" aria-hidden="true" />
      <span>{absChange.toFixed(1)}%</span>
    </div>
  );
}
