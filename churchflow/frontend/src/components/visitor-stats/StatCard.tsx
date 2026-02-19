/**
 * Stat Card Component
 *
 * Sophisticated summary card with animated counter, sparkline trends,
 * comparison badges, and glass-morphism effects. Inspired by Linear,
 * Stripe, Vercel, and Apple design systems.
 */

import { useState } from 'react';
import { motion } from 'framer-motion';
import { LucideIcon } from 'lucide-react';
import AnimatedCounter from './AnimatedCounter';
import MiniSparkline from './MiniSparkline';
import ComparisonBadge from './ComparisonBadge';
import StatTooltip from './StatTooltip';

interface StatCardProps {
  title: string;
  value: number;
  previousValue?: number;
  icon: LucideIcon;
  color: 'purple' | 'blue' | 'green' | 'orange';
  subtitle: string;
  trendData?: number[];
  additionalInfo?: string;
  onClick?: () => void;
  decimals?: number;
}

const colorClasses = {
  purple: {
    borderAccent: 'border-l-purple-500',
    iconBg: 'bg-purple-50',
    iconColor: 'text-purple-600',
    hoverBorder: 'border-purple-200',
  },
  blue: {
    borderAccent: 'border-l-blue-500',
    iconBg: 'bg-blue-50',
    iconColor: 'text-blue-600',
    hoverBorder: 'border-blue-200',
  },
  green: {
    borderAccent: 'border-l-emerald-500',
    iconBg: 'bg-emerald-50',
    iconColor: 'text-emerald-600',
    hoverBorder: 'border-emerald-200',
  },
  orange: {
    borderAccent: 'border-l-orange-500',
    iconBg: 'bg-orange-50',
    iconColor: 'text-orange-600',
    hoverBorder: 'border-orange-200',
  },
};

export default function StatCard({
  title,
  value,
  previousValue,
  icon: Icon,
  color,
  subtitle,
  trendData,
  additionalInfo,
  onClick,
  decimals = 0,
}: StatCardProps) {
  const [isHovered, setIsHovered] = useState(false);
  const styles = colorClasses[color];

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
        border border-gray-200 ${styles.borderAccent} border-l-4
        hover:${styles.hoverBorder}
      `}
      onClick={onClick}
      role="button"
      tabIndex={0}
      aria-label={`${title}: ${value}`}
      onKeyDown={(e) => {
        if (onClick && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault();
          onClick();
        }
      }}
    >
      <div className="relative p-3">
        {/* Header */}
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-xs font-medium text-gray-600 uppercase tracking-wider">
            {title}
          </h3>
          <div className={`p-1.5 ${styles.iconBg} rounded-md`}>
            <Icon className={`w-3.5 h-3.5 ${styles.iconColor}`} aria-hidden="true" />
          </div>
        </div>

        {/* Value with animation and comparison badge */}
        <div className="flex items-baseline justify-between mb-2">
          <div className="text-2xl font-bold text-gray-900 leading-none">
            <AnimatedCounter value={value} decimals={decimals} />
          </div>
          {previousValue !== undefined && (
            <ComparisonBadge current={value} previous={previousValue} />
          )}
        </div>

        {/* Sparkline */}
        {trendData && trendData.length > 0 && (
          <div className="mb-1.5 h-6">
            <MiniSparkline data={trendData} color={color} height={24} />
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center gap-2">
          <p className="text-xs text-gray-500 font-medium">{subtitle}</p>
        </div>
      </div>

      {/* Tooltip */}
      {additionalInfo && (
        <StatTooltip isVisible={isHovered} content={additionalInfo} />
      )}
    </motion.div>
  );
}
