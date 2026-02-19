/**
 * Badge Showcase Page
 *
 * Displays all badges organized by status (earned, in-progress, locked).
 * Shows user's badge collection and progress toward earning new badges.
 *
 * Features:
 * - Three sections: Earned, In Progress, Locked
 * - Filter by category
 * - Search badges by name
 * - Progress tracking
 * - Statistics summary
 * - Responsive grid layout
 */

import React, { useEffect, useState } from 'react';
import { Search, Award, TrendingUp, Lock, Filter } from 'lucide-react';
import { BadgeCard, Badge, EarnedBadge, BadgeProgress } from './BadgeCard';
import { API_BASE_URL } from '../../config/api-config';

interface BadgeShowcaseProps {
  organizationId: string;
  userId: string;
}

interface BadgesData {
  earned_badges: EarnedBadge[];
  in_progress_badges: BadgeProgress[];
  locked_badges: Badge[];
  total_badges: number;
  total_earned: number;
  total_points_from_badges: number;
}

export const BadgeShowcase: React.FC<BadgeShowcaseProps> = ({
  organizationId,
  userId
}) => {
  const [badgesData, setBadgesData] = useState<BadgesData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [activeTab, setActiveTab] = useState<'earned' | 'in_progress' | 'locked'>('earned');

  const categories = ['all', 'attendance', 'engagement', 'volunteering', 'giving', 'special'];

  /**
   * Fetch badges data
   */
  useEffect(() => {
    const fetchBadges = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch(
          `${API_BASE_URL}/gamification/my-badges?organization_id=${organizationId}`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
          }
        );

        if (!response.ok) {
          throw new Error('Failed to fetch badges');
        }

        const data = await response.json();
        setBadgesData(data);

      } catch (err) {
        console.error('Error fetching badges:', err);
        setError(err instanceof Error ? err.message : 'Failed to load badges');
      } finally {
        setLoading(false);
      }
    };

    if (organizationId && userId) {
      fetchBadges();
    }
  }, [organizationId, userId]);

  /**
   * Filter badges by search and category
   */
  const filterBadges = <T extends Badge>(badges: T[]): T[] => {
    return badges.filter(badge => {
      const matchesSearch = badge.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                           badge.description.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesCategory = selectedCategory === 'all' || badge.category === selectedCategory;
      return matchesSearch && matchesCategory;
    });
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center h-96">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4" />
              <p className="text-gray-600">Loading badges...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !badgesData) {
    return (
      <div className="min-h-screen bg-gray-50 py-8 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <Award className="h-12 w-12 text-red-400 mx-auto mb-3" />
            <p className="text-red-600">{error || 'Failed to load badges'}</p>
          </div>
        </div>
      </div>
    );
  }

  const filteredEarnedBadges = filterBadges(badgesData.earned_badges);
  const filteredInProgressBadges = badgesData.in_progress_badges.filter(item =>
    filterBadges([item.badge]).length > 0
  );
  const filteredLockedBadges = filterBadges(badgesData.locked_badges);

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Badge Collection</h1>
          <p className="text-gray-600">Track your achievements and unlock new badges</p>
        </div>

        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Badges Earned</p>
                <p className="text-3xl font-bold text-purple-600">
                  {badgesData.total_earned}
                </p>
              </div>
              <Award className="h-12 w-12 text-purple-200" />
            </div>
            <p className="text-xs text-gray-500 mt-2">
              {badgesData.total_earned} of {badgesData.total_badges} total
            </p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">In Progress</p>
                <p className="text-3xl font-bold text-blue-600">
                  {badgesData.in_progress_badges.length}
                </p>
              </div>
              <TrendingUp className="h-12 w-12 text-blue-200" />
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Keep going to unlock more!
            </p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Badge Points</p>
                <p className="text-3xl font-bold text-yellow-600">
                  {badgesData.total_points_from_badges}
                </p>
              </div>
              <Lock className="h-12 w-12 text-yellow-200" />
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Points earned from badges
            </p>
          </div>
        </div>

        {/* Search and Filter Bar */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
            {/* Search */}
            <div className="relative flex-1 md:max-w-md">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search badges..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg
                         focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>

            {/* Category Filter */}
            <div className="flex items-center space-x-2">
              <Filter className="h-5 w-5 text-gray-400" />
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg
                         focus:ring-2 focus:ring-purple-500 focus:border-transparent
                         capitalize"
              >
                {categories.map(category => (
                  <option key={category} value={category}>
                    {category === 'all' ? 'All Categories' : category}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="flex border-b">
            <button
              onClick={() => setActiveTab('earned')}
              className={`flex-1 px-6 py-4 font-medium transition-colors
                ${activeTab === 'earned'
                  ? 'text-purple-600 border-b-2 border-purple-600'
                  : 'text-gray-600 hover:text-gray-900'
                }`}
            >
              Earned ({filteredEarnedBadges.length})
            </button>
            <button
              onClick={() => setActiveTab('in_progress')}
              className={`flex-1 px-6 py-4 font-medium transition-colors
                ${activeTab === 'in_progress'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
                }`}
            >
              In Progress ({filteredInProgressBadges.length})
            </button>
            <button
              onClick={() => setActiveTab('locked')}
              className={`flex-1 px-6 py-4 font-medium transition-colors
                ${activeTab === 'locked'
                  ? 'text-gray-600 border-b-2 border-gray-600'
                  : 'text-gray-600 hover:text-gray-900'
                }`}
            >
              Locked ({filteredLockedBadges.length})
            </button>
          </div>
        </div>

        {/* Badge Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Earned Badges */}
          {activeTab === 'earned' && filteredEarnedBadges.length > 0 && (
            filteredEarnedBadges.map(badge => (
              <BadgeCard
                key={badge.badge_id}
                badge={badge}
                status="earned"
                earnedAt={badge.earned_at}
              />
            ))
          )}

          {/* In Progress Badges */}
          {activeTab === 'in_progress' && filteredInProgressBadges.length > 0 && (
            filteredInProgressBadges.map(item => (
              <BadgeCard
                key={item.badge.badge_id}
                badge={item.badge}
                status="in_progress"
                progress={item.progress_percentage}
                currentValue={item.current_value}
              />
            ))
          )}

          {/* Locked Badges */}
          {activeTab === 'locked' && filteredLockedBadges.length > 0 && (
            filteredLockedBadges.map(badge => (
              <BadgeCard
                key={badge.badge_id}
                badge={badge}
                status="locked"
              />
            ))
          )}
        </div>

        {/* Empty State */}
        {((activeTab === 'earned' && filteredEarnedBadges.length === 0) ||
          (activeTab === 'in_progress' && filteredInProgressBadges.length === 0) ||
          (activeTab === 'locked' && filteredLockedBadges.length === 0)) && (
          <div className="text-center py-12">
            <Award className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-600 mb-2">No badges found</p>
            <p className="text-sm text-gray-500">
              {searchQuery || selectedCategory !== 'all'
                ? 'Try adjusting your search or filters'
                : activeTab === 'earned'
                ? 'Keep attending services and participating to earn badges!'
                : activeTab === 'in_progress'
                ? 'Complete activities to start working on badges'
                : 'All badges are unlocked!'
              }
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default BadgeShowcase;
