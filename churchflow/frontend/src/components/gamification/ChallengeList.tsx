/**
 * Challenge List Component
 *
 * Displays all available challenges with filtering and participation tracking.
 *
 * Features:
 * - Tab filtering (All, Active, My Challenges)
 * - Challenge cards with join/leave functionality
 * - Empty states
 * - Loading and error handling
 * - Automatic refresh on participation changes
 */

import React, { useEffect, useState } from 'react';
import { Target, Loader2 } from 'lucide-react';
import { ChallengeCard, Challenge } from './ChallengeCard';
import { API_BASE_URL } from '../../config/api-config';

interface ChallengeListProps {
  organizationId: string;
  userId: string;
}

export const ChallengeList: React.FC<ChallengeListProps> = ({
  organizationId,
  userId
}) => {
  const [challenges, setChallenges] = useState<Challenge[]>([]);
  const [myChallenges, setMyChallenges] = useState<Challenge[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'all' | 'active' | 'mine'>('active');

  /**
   * Fetch challenges
   */
  const fetchChallenges = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch all challenges
      const allResponse = await fetch(
        `${API_BASE_URL}/gamification/challenges?organization_id=${organizationId}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        }
      );

      if (!allResponse.ok) {
        throw new Error('Failed to fetch challenges');
      }

      const allData = await allResponse.json();
      setChallenges(allData.challenges || []);

      // Fetch my challenges
      const myResponse = await fetch(
        `${API_BASE_URL}/gamification/my-challenges?organization_id=${organizationId}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        }
      );

      if (myResponse.ok) {
        const myData = await myResponse.json();
        setMyChallenges(myData.challenges || []);
      }

    } catch (err) {
      console.error('Error fetching challenges:', err);
      setError(err instanceof Error ? err.message : 'Failed to load challenges');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (organizationId && userId) {
      fetchChallenges();
    }
  }, [organizationId, userId]);

  /**
   * Handle join challenge
   */
  const handleJoin = async (challengeId: string) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/gamification/challenges/${challengeId}/join`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          },
          body: JSON.stringify({
            organization_id: organizationId
          })
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to join challenge');
      }

      // Refresh challenges list
      await fetchChallenges();

    } catch (err) {
      console.error('Error joining challenge:', err);
      alert(err instanceof Error ? err.message : 'Failed to join challenge');
    }
  };

  /**
   * Handle leave challenge
   */
  const handleLeave = async (challengeId: string) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/gamification/challenges/${challengeId}/leave`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to leave challenge');
      }

      // Refresh challenges list
      await fetchChallenges();

    } catch (err) {
      console.error('Error leaving challenge:', err);
      alert(err instanceof Error ? err.message : 'Failed to leave challenge');
    }
  };

  /**
   * Check if user is participating in challenge
   */
  const getUserParticipation = (challenge: Challenge) => {
    const participant = challenge.participants.find(p => p.user_id === userId);
    if (participant) {
      return {
        is_participant: true,
        progress: participant.current_progress,
        completed: participant.completed
      };
    }
    return { is_participant: false };
  };

  /**
   * Get filtered challenges based on active tab
   */
  const getFilteredChallenges = (): Challenge[] => {
    switch (activeTab) {
      case 'active':
        return challenges.filter(c => c.status === 'active');
      case 'mine':
        return myChallenges;
      case 'all':
      default:
        return challenges;
    }
  };

  const filteredChallenges = getFilteredChallenges();

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center h-96">
            <div className="text-center">
              <Loader2 className="h-12 w-12 text-purple-600 animate-spin mx-auto mb-4" />
              <p className="text-gray-600">Loading challenges...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 py-8 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <Target className="h-12 w-12 text-red-400 mx-auto mb-3" />
            <p className="text-red-600">{error}</p>
            <button
              onClick={fetchChallenges}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Challenges</h1>
          <p className="text-gray-600">Join challenges to earn points and badges</p>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="flex border-b">
            <button
              onClick={() => setActiveTab('active')}
              className={`flex-1 px-6 py-4 font-medium transition-colors
                ${activeTab === 'active'
                  ? 'text-purple-600 border-b-2 border-purple-600'
                  : 'text-gray-600 hover:text-gray-900'
                }`}
            >
              Active Challenges
            </button>
            <button
              onClick={() => setActiveTab('mine')}
              className={`flex-1 px-6 py-4 font-medium transition-colors
                ${activeTab === 'mine'
                  ? 'text-purple-600 border-b-2 border-purple-600'
                  : 'text-gray-600 hover:text-gray-900'
                }`}
            >
              My Challenges ({myChallenges.length})
            </button>
            <button
              onClick={() => setActiveTab('all')}
              className={`flex-1 px-6 py-4 font-medium transition-colors
                ${activeTab === 'all'
                  ? 'text-purple-600 border-b-2 border-purple-600'
                  : 'text-gray-600 hover:text-gray-900'
                }`}
            >
              All Challenges
            </button>
          </div>
        </div>

        {/* Challenges Grid */}
        {filteredChallenges.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredChallenges.map((challenge) => (
              <ChallengeCard
                key={challenge.id}
                challenge={challenge}
                userParticipation={getUserParticipation(challenge)}
                onJoin={handleJoin}
                onLeave={handleLeave}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <Target className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-600 mb-2">No challenges found</p>
            <p className="text-sm text-gray-500">
              {activeTab === 'active' && 'No active challenges at the moment'}
              {activeTab === 'mine' && "You haven't joined any challenges yet"}
              {activeTab === 'all' && 'No challenges have been created yet'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChallengeList;
