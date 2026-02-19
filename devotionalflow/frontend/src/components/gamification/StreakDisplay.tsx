/**
 * StreakDisplay Component
 * Shows user's current reading streak with visual indicators and next milestone
 */

import React from 'react';
import { Flame, Snowflake } from 'lucide-react';

interface StreakDisplayProps {
  currentStreak: number;
  longestStreak: number;
  freezesAvailable: number;
  nextMilestone?: {
    days: number;
    reward: string;
  };
  compact?: boolean;
}

export const StreakDisplay: React.FC<StreakDisplayProps> = ({
  currentStreak,
  longestStreak,
  freezesAvailable,
  nextMilestone,
  compact = false
}) => {
  if (compact) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 bg-secondary/10 dark:bg-secondary/20 rounded-lg">
        <Flame className={`w-5 h-5 ${currentStreak > 0 ? 'text-secondary' : 'text-gray-400'}`} />
        <div>
          <div className="text-sm font-semibold text-gray-900 dark:text-white">
            {currentStreak} Day Streak
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
          Reading Streak
        </h3>
        {freezesAvailable > 0 && (
          <div className="flex items-center gap-1 text-sm text-blue-600 dark:text-blue-400">
            <Snowflake className="w-4 h-4" />
            <span>{freezesAvailable} freeze{freezesAvailable !== 1 ? 's' : ''}</span>
          </div>
        )}
      </div>

      {/* Current Streak */}
      <div className="flex items-center gap-4 mb-4">
        <div className="relative">
          <div className={`w-16 h-16 rounded-full flex items-center justify-center ${
            currentStreak > 0
              ? 'bg-gradient-to-br from-secondary to-accent'
              : 'bg-gray-200 dark:bg-gray-700'
          }`}>
            <Flame className={`w-8 h-8 ${currentStreak > 0 ? 'text-white' : 'text-gray-400'}`} />
          </div>
        </div>
        <div>
          <div className="text-4xl font-bold text-gray-900 dark:text-white">
            {currentStreak}
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400">
            {currentStreak === 1 ? 'day' : 'days'} current streak
          </div>
        </div>
      </div>

      {/* Best Streak */}
      <div className="flex items-center justify-between py-2 border-t border-gray-100 dark:border-gray-700">
        <span className="text-sm text-gray-600 dark:text-gray-400">Best streak</span>
        <span className="text-sm font-semibold text-gray-900 dark:text-white">
          {longestStreak} {longestStreak === 1 ? 'day' : 'days'}
        </span>
      </div>

      {/* Next Milestone */}
      {nextMilestone && (
        <div className="mt-4 p-3 bg-gradient-to-r from-secondary/10 to-yellow-50 dark:from-secondary/20 dark:to-yellow-950 rounded-lg">
          <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">
            Next milestone
          </div>
          <div className="text-sm font-medium text-gray-900 dark:text-white mb-1">
            {nextMilestone.days} days
          </div>
          <div className="text-xs text-gray-600 dark:text-gray-400">
            {nextMilestone.reward}
          </div>
          {/* Progress bar */}
          <div className="mt-2 w-full h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-secondary to-accent rounded-full transition-all duration-300"
              style={{ width: `${(currentStreak / nextMilestone.days) * 100}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
};
