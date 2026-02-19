/**
 * MetricCard Component - Enhanced with animations
 *
 * Reusable card component for displaying metrics with trends.
 * Features animated counters, hover effects, and modern design.
 */

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: number;
  trendLabel?: string;
  icon?: React.ReactNode;
  format?: 'number' | 'currency' | 'percentage';
  loading?: boolean;
  className?: string;
}

/**
 * Format value based on specified format type
 */
function formatValue(value: string | number, format?: 'number' | 'currency' | 'percentage'): string {
  if (typeof value === 'string') return value;

  switch (format) {
    case 'currency':
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
      }).format(value);
    case 'percentage':
      return `${value.toFixed(1)}%`;
    case 'number':
    default:
      return new Intl.NumberFormat('en-US').format(value);
  }
}

/**
 * Get trend color and icon based on trend value
 */
function getTrendInfo(trend: number) {
  const absChange = Math.abs(trend);

  if (trend > 0) {
    return {
      color: 'text-green-700',
      bgColor: 'bg-green-100/90',
      icon: <TrendingUp className="w-2.5 h-2.5" />,
      label: `${absChange.toFixed(1)}%`,
    };
  } else if (trend < 0) {
    return {
      color: 'text-red-700',
      bgColor: 'bg-red-100/90',
      icon: <TrendingDown className="w-2.5 h-2.5" />,
      label: `${absChange.toFixed(1)}%`,
    };
  } else {
    return {
      color: 'text-gray-700',
      bgColor: 'bg-gray-100/90',
      icon: <Minus className="w-2.5 h-2.5" />,
      label: '0%',
    };
  }
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  trend,
  trendLabel,
  icon,
  format,
  loading = false,
  className = '',
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const trendInfo = trend !== undefined ? getTrendInfo(trend) : null;

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-sm p-3 animate-pulse border border-gray-200 ${className}`}>
        <div className="h-3 bg-gray-200 rounded w-1/2 mb-2"></div>
        <div className="h-6 bg-gray-200 rounded w-3/4 mb-2"></div>
        <div className="h-2 bg-gray-200 rounded w-1/3"></div>
      </div>
    );
  }

  return (
    <motion.div
      whileHover={{ y: -2 }}
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
      className={`
        relative overflow-hidden
        bg-white
        rounded-lg shadow-sm hover:shadow-md
        transition-all duration-200
        cursor-pointer group
        border border-gray-200 border-l-purple-500 border-l-4
        hover:border-purple-200
        ${className}
      `}
      role="button"
      tabIndex={0}
    >
      <div className="relative p-3">
        {/* Header with icon */}
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-xs font-medium text-gray-600 uppercase tracking-wider">{title}</h3>
          {icon && (
            <div className="p-1.5 bg-purple-50 rounded-md text-purple-600">
              {icon}
            </div>
          )}
        </div>

        {/* Value with trend badge */}
        <div className="flex items-baseline justify-between mb-2">
          <div className="text-2xl font-bold text-gray-900 leading-none">
            {formatValue(value, format)}
          </div>
          {trendInfo && (
            <div className={`
              inline-flex items-center gap-0.5
              px-1.5 py-0.5 rounded
              ${trendInfo.bgColor} ${trendInfo.color}
              text-xs font-bold font-mono
              backdrop-blur-sm
            `}>
              {trendInfo.icon}
              <span>{trendInfo.label}</span>
            </div>
          )}
        </div>

        {/* Subtitle */}
        {(subtitle || trendLabel) && (
          <div className="flex items-center gap-2">
            <p className="text-xs text-gray-500 font-medium">
              {trendLabel || subtitle}
            </p>
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default MetricCard;
