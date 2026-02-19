/**
 * AchievementCard Component
 * Displays a single achievement with unlock status and progress
 */

import React from 'react';
import { Lock, Check } from 'lucide-react';

export interface Achievement {
  id: string;
  name: string;
  description: string;
  category: 'reading' | 'engagement' | 'social' | 'spiritual' | 'special';
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
  icon_name: string;
  points_reward: number;
  coins_reward: number;
  unlocked: boolean;
  progress: number;
  progress_target: number;
  unlocked_at?: string;
}

interface AchievementCardProps {
  achievement: Achievement;
  onClick?: () => void;
}

const rarityColors: Record<string, string> = {
  common: 'from-gray-400 to-gray-500',
  rare: 'from-blue-400 to-blue-600',
  epic: 'from-purple-500 to-pink-600',
  legendary: 'from-yellow-500 to-secondary',
};

const rarityBorders: Record<string, string> = {
  common: 'border-gray-300 dark:border-gray-600',
  rare: 'border-blue-300 dark:border-blue-700',
  epic: 'border-purple-400 dark:border-purple-700',
  legendary: 'border-yellow-400 dark:border-secondary/70',
};

export const AchievementCard: React.FC<AchievementCardProps> = ({ achievement, onClick }) => {
  const { name, description, icon_name, rarity, unlocked, progress, progress_target, points_reward, coins_reward } = achievement;

  const progressPercentage = (progress / progress_target) * 100;
  const rarityGradient = rarityColors[rarity] || rarityColors.common;
  const rarityBorder = rarityBorders[rarity] || rarityBorders.common;

  return (
    <div
      onClick={onClick}
      className={`relative bg-white dark:bg-gray-800 rounded-xl p-4 border-2 ${rarityBorder} transition-all duration-200 ${
        onClick ? 'cursor-pointer hover:shadow-lg hover:scale-105' : ''
      } ${unlocked ? '' : 'opacity-60'}`}
    >
      {/* Unlocked Badge */}
      {unlocked && (
        <div className="absolute top-2 right-2 w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
          <Check className="w-4 h-4 text-white" />
        </div>
      )}

      {/* Icon */}
      <div className={`w-16 h-16 rounded-full flex items-center justify-center text-4xl mb-3 mx-auto bg-gradient-to-br ${rarityGradient} shadow-lg ${
        !unlocked ? 'grayscale' : ''
      }`}>
        {unlocked ? icon_name : <Lock className="w-8 h-8 text-white" />}
      </div>

      {/* Title */}
      <div className="text-center mb-2">
        <h4 className="font-semibold text-gray-900 dark:text-white text-sm mb-1">
          {name}
        </h4>
        <p className="text-xs text-gray-600 dark:text-gray-400">
          {description}
        </p>
      </div>

      {/* Progress */}
      {!unlocked && progress_target > 1 && (
        <div className="mt-3">
          <div className="flex items-center justify-between text-xs text-gray-600 dark:text-gray-400 mb-1">
            <span>Progress</span>
            <span>{progress} / {progress_target}</span>
          </div>
          <div className="w-full h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className={`h-full bg-gradient-to-r ${rarityGradient} rounded-full transition-all duration-300`}
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
        </div>
      )}

      {/* Rewards */}
      <div className="mt-3 flex items-center justify-center gap-3 text-xs">
        <div className="flex items-center gap-1 text-blue-600 dark:text-blue-400">
          <span className="font-semibold">+{points_reward}</span>
          <span>XP</span>
        </div>
        {coins_reward > 0 && (
          <div className="flex items-center gap-1 text-yellow-600 dark:text-yellow-400">
            <span className="font-semibold">+{coins_reward}</span>
            <span>coins</span>
          </div>
        )}
      </div>

      {/* Rarity Badge */}
      <div className="mt-2 text-center">
        <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium bg-gradient-to-r ${rarityGradient} text-white capitalize`}>
          {rarity}
        </span>
      </div>
    </div>
  );
};
