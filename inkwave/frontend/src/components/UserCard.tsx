/**
 * UserCard Component
 * Reusable card for displaying user information with follow button
 */

import { Link } from 'react-router-dom';
import FollowButton from './FollowButton';

interface UserCardProps {
  user: {
    user_id: string;
    username?: string;
    display_name?: string;
    avatar_url?: string;
    bio?: string;
    followers_count?: number;
    following_count?: number;
    listening_stats?: {
      total_listening_hours: number;
      books_completed: number;
    };
    is_following?: boolean;
  };
  showFollowButton?: boolean;
  showStats?: boolean;
  variant?: 'default' | 'compact';
  className?: string;
}

export default function UserCard({
  user,
  showFollowButton = true,
  showStats = true,
  variant = 'default',
  className = '',
}: UserCardProps) {
  const displayName = user.display_name || user.username || 'Unknown User';
  const initials = displayName[0]?.toUpperCase() || '?';

  if (variant === 'compact') {
    return (
      <div
        className={`flex items-center justify-between p-3 bg-gray-800 rounded-lg hover:bg-gray-750 transition-colors ${className}`}
      >
        <Link
          to={`/user/${user.user_id}`}
          className="flex items-center space-x-3 flex-1"
        >
          {/* Avatar */}
          {user.avatar_url ? (
            <img
              src={user.avatar_url}
              alt={displayName}
              className="w-10 h-10 rounded-full object-cover"
            />
          ) : (
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
              <span className="text-white font-bold text-lg">{initials}</span>
            </div>
          )}

          {/* Name */}
          <div>
            <p className="font-medium text-white">{displayName}</p>
            {user.username && (
              <p className="text-sm text-gray-400">@{user.username}</p>
            )}
          </div>
        </Link>

        {/* Follow Button */}
        {showFollowButton && (
          <FollowButton
            userId={user.user_id}
            isFollowing={user.is_following || false}
            size="sm"
          />
        )}
      </div>
    );
  }

  return (
    <div
      className={`bg-gray-800 rounded-xl p-6 hover:bg-gray-750 transition-all shadow-lg ${className}`}
    >
      {/* User Info */}
      <Link
        to={`/user/${user.user_id}`}
        className="flex items-start space-x-4 mb-4"
      >
        {/* Avatar */}
        {user.avatar_url ? (
          <img
            src={user.avatar_url}
            alt={displayName}
            className="w-16 h-16 rounded-full object-cover"
          />
        ) : (
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center flex-shrink-0">
            <span className="text-white font-bold text-2xl">{initials}</span>
          </div>
        )}

        {/* Name & Bio */}
        <div className="flex-1 min-w-0">
          <h3 className="font-bold text-lg text-white truncate">
            {displayName}
          </h3>
          {user.username && (
            <p className="text-gray-400 text-sm mb-2">@{user.username}</p>
          )}
          {user.bio && (
            <p className="text-gray-300 text-sm line-clamp-2">{user.bio}</p>
          )}
        </div>
      </Link>

      {/* Stats */}
      {showStats && (
        <div className="grid grid-cols-2 gap-4 mb-4">
          {user.followers_count !== undefined && (
            <div className="text-center">
              <p className="text-2xl font-bold text-white">
                {user.followers_count}
              </p>
              <p className="text-sm text-gray-400">Followers</p>
            </div>
          )}
          {user.following_count !== undefined && (
            <div className="text-center">
              <p className="text-2xl font-bold text-white">
                {user.following_count}
              </p>
              <p className="text-sm text-gray-400">Following</p>
            </div>
          )}
          {user.listening_stats && (
            <>
              <div className="text-center">
                <p className="text-2xl font-bold text-purple-400">
                  {user.listening_stats.total_listening_hours.toFixed(1)}h
                </p>
                <p className="text-sm text-gray-400">Listened</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-pink-400">
                  {user.listening_stats.books_completed}
                </p>
                <p className="text-sm text-gray-400">Completed</p>
              </div>
            </>
          )}
        </div>
      )}

      {/* Follow Button */}
      {showFollowButton && (
        <FollowButton
          userId={user.user_id}
          isFollowing={user.is_following || false}
          className="w-full"
        />
      )}
    </div>
  );
}
