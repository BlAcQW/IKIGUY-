/**
 * Challenge Card Component
 *
 * Displays a single challenge with details, progress, and join/leave actions.
 *
 * Features:
 * - Visual status indicators (upcoming, active, completed)
 * - Progress tracking for participants
 * - Join/Leave buttons
 * - Participant count
 * - Deadline countdown
 * - Rewards display
 */

import React, { useState } from 'react';
import { Target, Users, Award, Clock, CheckCircle, Calendar } from 'lucide-react';
import { API_BASE_URL } from '../../config/api-config';

export interface Challenge {
  id: string;
  name: string;
  description: string;
  challenge_type: string;
  start_date: string;
  end_date: string;
  status: string;
  goal_type: string;
  goal_target: number;
  goal_unit: string;
  points_reward: number;
  badge_reward?: string;
  participants: Array<{
    user_id: string;
    current_progress: number;
    completed: boolean;
  }>;
  max_participants?: number;
  is_public: boolean;
}

interface ChallengeCardProps {
  challenge: Challenge;
  userParticipation?: {
    is_participant: boolean;
    progress?: number;
    completed?: boolean;
  };
  onJoin?: (challengeId: string) => void;
  onLeave?: (challengeId: string) => void;
}

const STATUS_COLORS = {
  upcoming: 'bg-blue-50 text-blue-700 border-blue-200',
  active: 'bg-green-50 text-green-700 border-green-200',
  completed: 'bg-gray-50 text-gray-700 border-gray-200'
};

export const ChallengeCard: React.FC<ChallengeCardProps> = ({
  challenge,
  userParticipation,
  onJoin,
  onLeave
}) => {
  const [isJoining, setIsJoining] = useState(false);

  /**
   * Calculate days remaining
   */
  const getDaysRemaining = (): number => {
    const end = new Date(challenge.end_date);
    const now = new Date();
    const diff = end.getTime() - now.getTime();
    return Math.ceil(diff / (1000 * 60 * 60 * 24));
  };

  /**
   * Format date
   */
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  /**
   * Get progress percentage
   */
  const getProgressPercentage = (): number => {
    if (!userParticipation || !userParticipation.progress) return 0;
    return (userParticipation.progress / challenge.goal_target) * 100;
  };

  /**
   * Handle join challenge
   */
  const handleJoin = async () => {
    if (!onJoin) return;
    setIsJoining(true);
    try {
      await onJoin(challenge.id);
    } finally {
      setIsJoining(false);
    }
  };

  const daysRemaining = getDaysRemaining();
  const progressPercentage = getProgressPercentage();
  const statusColor = STATUS_COLORS[challenge.status as keyof typeof STATUS_COLORS] || STATUS_COLORS.active;

  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200 overflow-hidden
                    hover:shadow-lg transition-shadow">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center space-x-3">
            <div className="bg-purple-100 p-2 rounded-lg">
              <Target className="h-6 w-6 text-purple-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">{challenge.name}</h3>
              <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium capitalize
                              ${statusColor} mt-1`}>
                {challenge.status}
              </span>
            </div>
          </div>
        </div>
        <p className="text-sm text-gray-600">{challenge.description}</p>
      </div>

      {/* Body */}
      <div className="p-6 space-y-4">
        {/* Goal */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Goal:</span>
          <span className="font-semibold text-gray-900 capitalize">
            {challenge.goal_target} {challenge.goal_unit} • {challenge.goal_type}
          </span>
        </div>

        {/* Timeline */}
        <div className="flex items-center space-x-2 text-sm text-gray-600">
          <Calendar className="h-4 w-4" />
          <span>{formatDate(challenge.start_date)} → {formatDate(challenge.end_date)}</span>
        </div>

        {/* Days Remaining */}
        {challenge.status === 'active' && (
          <div className="flex items-center space-x-2 text-sm">
            <Clock className="h-4 w-4 text-orange-500" />
            <span className={`font-medium ${daysRemaining <= 3 ? 'text-red-600' : 'text-gray-700'}`}>
              {daysRemaining} day{daysRemaining !== 1 ? 's' : ''} remaining
            </span>
          </div>
        )}

        {/* Participants */}
        <div className="flex items-center space-x-2 text-sm text-gray-600">
          <Users className="h-4 w-4" />
          <span>
            {challenge.participants.length} participant{challenge.participants.length !== 1 ? 's' : ''}
            {challenge.max_participants && ` / ${challenge.max_participants}`}
          </span>
        </div>

        {/* User Progress (if participating) */}
        {userParticipation?.is_participant && (
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Your Progress</span>
              <span className="text-sm font-semibold text-purple-600">
                {userParticipation.progress} / {challenge.goal_target}
              </span>
            </div>
            <div className="bg-gray-200 rounded-full h-2 overflow-hidden">
              <div
                className="bg-gradient-to-r from-purple-500 to-blue-500 h-full
                           transition-all duration-500 ease-out"
                style={{ width: `${Math.min(progressPercentage, 100)}%` }}
              />
            </div>
            {userParticipation.completed && (
              <div className="flex items-center space-x-2 mt-2 text-green-600">
                <CheckCircle className="h-4 w-4" />
                <span className="text-sm font-medium">Completed!</span>
              </div>
            )}
          </div>
        )}

        {/* Rewards */}
        <div className="bg-yellow-50 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <Award className="h-5 w-5 text-yellow-600" />
            <span className="text-sm font-medium text-gray-700">Rewards</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Points:</span>
            <span className="text-lg font-bold text-yellow-600">+{challenge.points_reward}</span>
          </div>
          {challenge.badge_reward && (
            <div className="flex items-center justify-between mt-1">
              <span className="text-sm text-gray-600">Badge:</span>
              <span className="text-sm font-semibold text-purple-600">{challenge.badge_reward}</span>
            </div>
          )}
        </div>
      </div>

      {/* Footer Actions */}
      <div className="p-6 bg-gray-50 border-t border-gray-200">
        {challenge.status === 'active' && !userParticipation?.is_participant && (
          <button
            onClick={handleJoin}
            disabled={isJoining || (challenge.max_participants !== undefined &&
                     challenge.participants.length >= challenge.max_participants)}
            className="w-full bg-purple-600 text-white py-2 px-4 rounded-lg
                     hover:bg-purple-700 transition-colors disabled:opacity-50
                     disabled:cursor-not-allowed font-medium"
          >
            {isJoining ? 'Joining...' : 'Join Challenge'}
          </button>
        )}

        {challenge.status === 'active' && userParticipation?.is_participant && !userParticipation.completed && (
          <button
            onClick={() => onLeave && onLeave(challenge.id)}
            className="w-full bg-gray-200 text-gray-700 py-2 px-4 rounded-lg
                     hover:bg-gray-300 transition-colors font-medium"
          >
            Leave Challenge
          </button>
        )}

        {challenge.status === 'upcoming' && (
          <div className="text-center text-sm text-gray-600">
            Challenge starts {formatDate(challenge.start_date)}
          </div>
        )}

        {challenge.status === 'completed' && (
          <div className="text-center text-sm font-medium text-gray-700">
            Challenge Completed
            {userParticipation?.completed && (
              <span className="text-green-600"> • You earned {challenge.points_reward} points!</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ChallengeCard;
