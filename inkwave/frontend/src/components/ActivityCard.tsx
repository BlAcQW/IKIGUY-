/**
 * ActivityCard Component
 * Displays a reading activity (started, milestone, completed)
 */

import { Link } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';
import { BookOpen, CheckCircle, Target } from 'lucide-react';

interface ActivityCardProps {
  activity: {
    activity_id: string;
    user_id: string;
    user?: {
      user_id: string;
      username?: string;
      display_name?: string;
      avatar_url?: string;
    };
    activity_type: 'started_book' | 'completed_book' | 'milestone_reached';
    book_id: string;
    book_title: string;
    book_cover_url?: string;
    book_author?: string;
    progress_percentage?: number;
    created_at: string;
  };
  showUser?: boolean;
  className?: string;
}

export default function ActivityCard({
  activity,
  showUser = true,
  className = '',
}: ActivityCardProps) {
  const getActivityIcon = () => {
    switch (activity.activity_type) {
      case 'started_book':
        return <BookOpen className="w-5 h-5 text-blue-400" />;
      case 'completed_book':
        return <CheckCircle className="w-5 h-5 text-green-400" />;
      case 'milestone_reached':
        return <Target className="w-5 h-5 text-purple-400" />;
      default:
        return <BookOpen className="w-5 h-5 text-gray-400" />;
    }
  };

  const getActivityText = () => {
    switch (activity.activity_type) {
      case 'started_book':
        return 'started listening to';
      case 'completed_book':
        return 'completed';
      case 'milestone_reached':
        return `reached ${activity.progress_percentage}% of`;
      default:
        return 'interacted with';
    }
  };

  const getActivityColor = () => {
    switch (activity.activity_type) {
      case 'started_book':
        return 'border-blue-500';
      case 'completed_book':
        return 'border-green-500';
      case 'milestone_reached':
        return 'border-purple-500';
      default:
        return 'border-gray-500';
    }
  };

  const timeAgo = formatDistanceToNow(new Date(activity.created_at), {
    addSuffix: true,
  });

  const user = activity.user;
  const displayName = user?.display_name || user?.username || 'Someone';

  return (
    <div
      className={`bg-gray-800 rounded-lg p-4 border-l-4 ${getActivityColor()} hover:bg-gray-750 transition-colors ${className}`}
    >
      <div className="flex items-start space-x-3">
        {/* Activity Icon */}
        <div className="flex-shrink-0 mt-1">{getActivityIcon()}</div>

        <div className="flex-1 min-w-0">
          {/* User Info */}
          {showUser && user && (
            <Link
              to={`/user/${user.user_id}`}
              className="flex items-center space-x-2 mb-2 hover:opacity-80 transition-opacity"
            >
              {user.avatar_url ? (
                <img
                  src={user.avatar_url}
                  alt={displayName}
                  className="w-6 h-6 rounded-full object-cover"
                />
              ) : (
                <div className="w-6 h-6 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                  <span className="text-white text-xs font-bold">
                    {displayName[0]?.toUpperCase()}
                  </span>
                </div>
              )}
              <span className="font-medium text-white text-sm">
                {displayName}
              </span>
            </Link>
          )}

          {/* Activity Description */}
          <p className="text-gray-300 text-sm mb-2">
            {showUser && <span className="text-gray-400">•</span>}{' '}
            <span className="text-gray-400">{getActivityText()}</span>
          </p>

          {/* Book Info */}
          <Link
            to={`/book/${activity.book_id}`}
            className="flex items-start space-x-3 hover:opacity-80 transition-opacity"
          >
            {activity.book_cover_url && (
              <img
                src={activity.book_cover_url}
                alt={activity.book_title}
                className="w-12 h-16 object-cover rounded shadow-md flex-shrink-0"
              />
            )}
            <div className="flex-1 min-w-0">
              <p className="font-medium text-white line-clamp-2">
                {activity.book_title}
              </p>
              {activity.book_author && (
                <p className="text-sm text-gray-400 truncate">
                  by {activity.book_author}
                </p>
              )}
            </div>
          </Link>

          {/* Time Ago */}
          <p className="text-xs text-gray-500 mt-2">{timeAgo}</p>
        </div>
      </div>
    </div>
  );
}
