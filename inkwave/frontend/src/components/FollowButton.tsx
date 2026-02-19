/**
 * FollowButton Component
 * Follow/Following button with optimistic UI updates
 */

import { useState } from 'react';
import { useFollowUser, useUnfollowUser } from '../hooks/useSocial';
import { useAuthStore } from '../store/authStore';
import { useNavigate } from 'react-router-dom';

interface FollowButtonProps {
  userId: string;
  isFollowing: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  onFollowChange?: (isFollowing: boolean) => void;
}

export default function FollowButton({
  userId,
  isFollowing: initialIsFollowing,
  size = 'md',
  className = '',
  onFollowChange,
}: FollowButtonProps) {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const [isFollowing, setIsFollowing] = useState(initialIsFollowing);

  // React Query mutations
  const followMutation = useFollowUser();
  const unfollowMutation = useUnfollowUser();

  const loading = followMutation.isPending || unfollowMutation.isPending;

  const handleClick = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    // Require authentication
    if (!user) {
      navigate('/login');
      return;
    }

    // Can't follow yourself
    if (user.id === userId) {
      return;
    }

    // Optimistic update
    const newFollowingState = !isFollowing;
    const previousState = isFollowing;
    setIsFollowing(newFollowingState);
    onFollowChange?.(newFollowingState);

    try {
      if (isFollowing) {
        // Unfollow
        await unfollowMutation.mutateAsync(userId);
      } else {
        // Follow
        await followMutation.mutateAsync(userId);
      }
    } catch (error) {
      // Revert on error (toast is already shown by mutation)
      setIsFollowing(previousState);
      onFollowChange?.(previousState);
    }
  };

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  const baseClasses =
    'font-medium rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed';

  if (isFollowing) {
    return (
      <button
        onClick={handleClick}
        disabled={loading}
        className={`
          ${baseClasses}
          ${sizeClasses[size]}
          bg-gray-600 text-white
          hover:bg-red-600 hover:text-white
          active:scale-95
          group
          ${className}
        `}
      >
        <span className="group-hover:hidden">
          {loading ? 'Loading...' : 'Following'}
        </span>
        <span className="hidden group-hover:inline">Unfollow</span>
      </button>
    );
  }

  return (
    <button
      onClick={handleClick}
      disabled={loading}
      className={`
        ${baseClasses}
        ${sizeClasses[size]}
        bg-gradient-to-r from-purple-600 to-pink-600
        text-white
        hover:from-purple-700 hover:to-pink-700
        active:scale-95
        ${className}
      `}
    >
      {loading ? 'Loading...' : 'Follow'}
    </button>
  );
}
