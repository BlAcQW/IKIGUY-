/**
 * ActivityFeedPage Component
 * Activity feed from users you follow
 * Route: /feed
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Activity,
  BookOpen,
  CheckCircle,
  TrendingUp,
  Loader,
  ArrowLeft,
  UserPlus,
  RefreshCw,
} from 'lucide-react';
import { useFollowingFeed } from '../hooks/useSocial';
import { useAuthStore } from '../store/authStore';
import ActivityCard from '../components/ActivityCard';
import { ActivityType } from '../types/social';

type FilterType = 'all' | 'started_book' | 'completed_book' | 'milestone_reached';

const FILTERS: { value: FilterType; label: string; icon: typeof Activity }[] = [
  { value: 'all', label: 'All Activity', icon: Activity },
  { value: 'started_book', label: 'Started', icon: BookOpen },
  { value: 'completed_book', label: 'Completed', icon: CheckCircle },
  { value: 'milestone_reached', label: 'Milestones', icon: TrendingUp },
];

export default function ActivityFeedPage() {
	useEffect(() => {
		document.title = 'Activity Feed - InkWave';
	}, []);

  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [activeFilter, setActiveFilter] = useState<FilterType>('all');

  // Fetch following feed (100 activities)
  const { data: feedData, isLoading, refetch, isFetching } = useFollowingFeed(100, {
    refetchInterval: 2 * 60 * 1000, // Auto-refetch every 2 minutes
  });

  const activities = feedData?.activities || [];

  // Filter activities by type
  const filteredActivities =
    activeFilter === 'all'
      ? activities
      : activities.filter((activity) => activity.activity_type === activeFilter);

  // Handle refresh
  const handleRefresh = () => {
    refetch();
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 flex items-center justify-center">
        <div className="text-center">
          <Activity size={48} className="text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400 text-lg mb-2">Sign in to see your feed</p>
          <p className="text-gray-500 text-sm mb-6">
            Follow users to see their reading activity
          </p>
          <button
            onClick={() => navigate('/login')}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-medium transition-colors"
          >
            Sign In
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950">
      {/* Header */}
      <div className="bg-gray-900/50 backdrop-blur-sm border-b border-gray-800 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <button
                onClick={() => navigate(-1)}
                className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
              >
                <ArrowLeft size={20} className="text-gray-400" />
              </button>
              <div className="flex items-center gap-2">
                <Activity size={24} className="text-blue-500" />
                <h1 className="text-xl font-bold text-white">Activity Feed</h1>
              </div>
            </div>

            {/* Refresh Button */}
            <button
              onClick={handleRefresh}
              disabled={isFetching}
              className="p-2 hover:bg-gray-800 rounded-lg transition-colors disabled:opacity-50"
              title="Refresh feed"
            >
              <RefreshCw
                size={20}
                className={`text-gray-400 ${isFetching ? 'animate-spin' : ''}`}
              />
            </button>
          </div>

          {/* Filter Tabs */}
          <div className="flex gap-2 overflow-x-auto pb-2">
            {FILTERS.map(({ value, label, icon: Icon }) => (
              <button
                key={value}
                onClick={() => setActiveFilter(value)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${
                  activeFilter === value
                    ? 'bg-blue-600 text-white shadow-lg'
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-gray-300'
                }`}
              >
                <Icon size={16} />
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-20">
            <Loader className="animate-spin text-blue-500" size={32} />
          </div>
        )}

        {/* Empty State - No Following */}
        {!isLoading && activities.length === 0 && (
          <div className="text-center py-20">
            <UserPlus size={48} className="text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400 text-lg mb-2">Your feed is empty</p>
            <p className="text-gray-500 text-sm mb-6">
              Follow other users to see their reading activity here
            </p>
            <button
              onClick={() => navigate('/discover')}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-medium transition-colors"
            >
              Discover Users
            </button>
          </div>
        )}

        {/* Empty State - No Filtered Activities */}
        {!isLoading &&
          activities.length > 0 &&
          filteredActivities.length === 0 && (
            <div className="text-center py-20">
              <Activity size={48} className="text-gray-600 mx-auto mb-4" />
              <p className="text-gray-400 text-lg">No {activeFilter.replace('_', ' ')} activities</p>
              <p className="text-gray-500 text-sm mt-2">
                Try selecting a different filter
              </p>
            </div>
          )}

        {/* Activity Feed */}
        {!isLoading && filteredActivities.length > 0 && (
          <div className="space-y-4">
            {filteredActivities.map((activity, index) => (
              <motion.div
                key={activity.activity_id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <ActivityCard activity={activity} />
              </motion.div>
            ))}

            {/* Footer Info */}
            <div className="text-center text-gray-500 text-sm pt-8">
              <p>
                Showing {filteredActivities.length}{' '}
                {filteredActivities.length === 1 ? 'activity' : 'activities'}
              </p>
              <p className="mt-2">Feed automatically refreshes every 2 minutes</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
