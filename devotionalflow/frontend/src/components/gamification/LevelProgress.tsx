/**
 * LevelProgress Component
 * Shows user's current level, tier, and XP progress bar
 */

import React from 'react';
import { TrendingUp, Award } from 'lucide-react';

interface LevelProgressProps {
  currentLevel: number;
  levelTier: string;
  totalXP: number;
  xpToNextLevel: number;
  compact?: boolean;
}

// Tier colors
const tierColors: Record<string, string> = {
  'Seeker': 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-950',
  'Disciple': 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950',
  'Faithful': 'text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-950',
  'Shepherd': 'text-secondary dark:text-secondary bg-secondary/10 dark:bg-secondary/20',
  'Elder': 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950',
};

const tierGradients: Record<string, string> = {
  'Seeker': 'from-green-400 to-emerald-500',
  'Disciple': 'from-blue-400 to-indigo-500',
  'Faithful': 'from-purple-400 to-pink-500',
  'Shepherd': 'from-secondary to-accent',
  'Elder': 'from-red-500 to-rose-600',
};

export const LevelProgress: React.FC<LevelProgressProps> = ({
  currentLevel,
  levelTier,
  totalXP,
  xpToNextLevel,
  compact = false
}) => {
  const currentLevelXP = totalXP % xpToNextLevel;
  const progressPercentage = (currentLevelXP / xpToNextLevel) * 100;
  const tierColor = tierColors[levelTier] || tierColors['Seeker'];
  const tierGradient = tierGradients[levelTier] || tierGradients['Seeker'];

  if (compact) {
    return (
      <div className="flex items-center gap-3">
        <div className={`w-10 h-10 rounded-full flex items-center justify-center bg-gradient-to-br ${tierGradient}`}>
          <span className="text-sm font-bold text-white">{currentLevel}</span>
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-xs font-medium text-gray-600 dark:text-gray-400">
            Level {currentLevel} • {levelTier}
          </div>
          <div className="mt-1 w-full h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className={`h-full bg-gradient-to-r ${tierGradient} rounded-full transition-all duration-300`}
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Level & Progress
        </h3>
        <Award className="w-5 h-5 text-gray-400" />
      </div>

      {/* Level Display */}
      <div className="flex items-center gap-4 mb-4">
        <div className={`w-16 h-16 rounded-full flex items-center justify-center bg-gradient-to-br ${tierGradient} shadow-lg`}>
          <span className="text-2xl font-bold text-white">{currentLevel}</span>
        </div>
        <div>
          <div className="text-2xl font-bold text-gray-900 dark:text-white">
            Level {currentLevel}
          </div>
          <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${tierColor}`}>
            {levelTier}
          </div>
        </div>
      </div>

      {/* XP Progress */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {currentLevelXP.toLocaleString()} / {xpToNextLevel.toLocaleString()} XP
          </span>
          <div className="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-400">
            <TrendingUp className="w-3.5 h-3.5" />
            <span>{Math.floor(progressPercentage)}%</span>
          </div>
        </div>

        {/* Progress bar */}
        <div className="w-full h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            className={`h-full bg-gradient-to-r ${tierGradient} rounded-full transition-all duration-500 ease-out`}
            style={{ width: `${progressPercentage}%` }}
          />
        </div>

        {/* Total XP */}
        <div className="mt-3 text-xs text-gray-500 dark:text-gray-500 text-center">
          Total: {totalXP.toLocaleString()} XP
        </div>
      </div>
    </div>
  );
};
