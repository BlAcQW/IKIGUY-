/**
 * Badge Card Component
 *
 * Displays a single badge with its details, progress, and earned status.
 *
 * Features:
 * - Visual distinction between earned, in-progress, and locked badges
 * - Progress bar for in-progress badges
 * - Grayscale styling for locked badges
 * - Earned date display
 * - Hover effects
 */

import React from 'react';
import { Lock, CheckCircle } from 'lucide-react';

export interface Badge {
  badge_id: string;
  name: string;
  description: string;
  category: string;
  icon_emoji: string;
  requirement_type: string;
  requirement_value: number;
  points_reward: number;
  tier: string;
}

export interface EarnedBadge extends Badge {
  earned_at: string;
}

export interface BadgeProgress {
  badge: Badge;
  current_value: number;
  requirement_value: number;
  progress_percentage: number;
}

interface BadgeCardProps {
  badge: Badge;
  status: 'earned' | 'in_progress' | 'locked';
  earnedAt?: string;
  progress?: number;
  currentValue?: number;
}

const TIER_COLORS = {
  bronze: 'border-amber-600 bg-amber-50',
  silver: 'border-gray-400 bg-gray-50',
  gold: 'border-yellow-500 bg-yellow-50',
  platinum: 'border-purple-500 bg-purple-50'
};

const CATEGORY_COLORS = {
  attendance: 'text-blue-600',
  engagement: 'text-green-600',
  volunteering: 'text-purple-600',
  giving: 'text-pink-600',
  special: 'text-indigo-600'
};

export const BadgeCard: React.FC<BadgeCardProps> = ({
  badge,
  status,
  earnedAt,
  progress = 0,
  currentValue = 0
}) => {
  const tierColor = TIER_COLORS[badge.tier as keyof typeof TIER_COLORS] || TIER_COLORS.bronze;
  const categoryColor = CATEGORY_COLORS[badge.category as keyof typeof CATEGORY_COLORS] || 'text-gray-600';

  // Format earned date
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  // Base card classes
  const cardClasses = `
    relative rounded-xl p-6 transition-all duration-300
    border-2 hover:shadow-lg
    ${status === 'locked' ? 'opacity-50 grayscale' : ''}
    ${status === 'earned' ? tierColor : 'border-gray-200 bg-white'}
    ${status === 'in_progress' ? 'border-blue-200 bg-blue-50' : ''}
  `;

  return (
    <div className={cardClasses}>
      {/* Earned Badge Indicator */}
      {status === 'earned' && (
        <div className="absolute top-3 right-3">
          <CheckCircle className="h-6 w-6 text-green-600" />
        </div>
      )}

      {/* Locked Badge Indicator */}
      {status === 'locked' && (
        <div className="absolute top-3 right-3">
          <Lock className="h-5 w-5 text-gray-400" />
        </div>
      )}

      {/* Badge Icon */}
      <div className="text-center mb-4">
        <div className="text-6xl mb-2">{badge.icon_emoji}</div>
        <h3 className="text-xl font-bold text-gray-900">{badge.name}</h3>
        <p className={`text-sm font-medium capitalize ${categoryColor} mt-1`}>
          {badge.category}
        </p>
      </div>

      {/* Description */}
      <p className="text-sm text-gray-600 text-center mb-4">
        {badge.description}
      </p>

      {/* Progress Bar (for in-progress badges) */}
      {status === 'in_progress' && (
        <div className="mb-4">
          <div className="flex justify-between text-xs text-gray-600 mb-1">
            <span>{currentValue} / {badge.requirement_value}</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <div className="bg-gray-200 rounded-full h-2 overflow-hidden">
            <div
              className="bg-gradient-to-r from-blue-500 to-purple-500 h-full
                         transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Points Reward */}
      <div className="flex items-center justify-center space-x-2 text-sm">
        <span className="text-yellow-600 font-medium">+{badge.points_reward} pts</span>
        {status === 'earned' && earnedAt && (
          <>
            <span className="text-gray-400">•</span>
            <span className="text-gray-500">Earned {formatDate(earnedAt)}</span>
          </>
        )}
      </div>

      {/* Tier Badge */}
      <div className="mt-3 text-center">
        <span className={`
          inline-block px-3 py-1 rounded-full text-xs font-medium capitalize
          ${status === 'earned' ? tierColor : 'bg-gray-100 text-gray-600'}
        `}>
          {badge.tier} Tier
        </span>
      </div>
    </div>
  );
};

export default BadgeCard;
