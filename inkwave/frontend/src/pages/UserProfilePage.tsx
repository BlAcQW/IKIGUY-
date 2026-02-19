/**
 * UserProfilePage Component
 * Public user profile with activity tabs and stats
 * Route: /user/:userId
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  User,
  Calendar,
  Clock,
  BookOpen,
  MessageCircle,
  Share2,
  Users,
  Trophy,
  Loader,
  ArrowLeft,
} from 'lucide-react';
import { usePublicProfile, useCurrentlyReading, useUserActivity } from '../hooks/useUserProfile';
import { useFollowers, useFollowing } from '../hooks/useSocial';
import { useLeaderboard, useUserRank } from '../hooks/useLeaderboard';
import { useAuthStore } from '../store/authStore';
import FollowButton from '../components/FollowButton';
import UsersListModal from '../components/UsersListModal';
import toast from 'react-hot-toast';
import { formatDistanceToNow } from 'date-fns';

type TabType = 'activity' | 'books' | 'reviews';

export default function UserProfilePage() {
	useEffect(() => {
		document.title = 'User Profile - InkWave';
	}, []);

  const { userId } = useParams<{ userId: string }>();
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [activeTab, setActiveTab] = useState<TabType>('activity');
  const [showFollowersModal, setShowFollowersModal] = useState(false);
  const [showFollowingModal, setShowFollowingModal] = useState(false);
  const [modalType, setModalType] = useState<'followers' | 'following'>('followers');

  // React Query hooks
  const { data: profile, isLoading: profileLoading } = usePublicProfile(userId!);
  const { data: currentlyReadingData } = useCurrentlyReading(userId!);
  const { data: activityData } = useUserActivity(userId!, 20);
  const { data: followersData } = useFollowers(userId!);
  const { data: followingData } = useFollowing(userId!);
  const { data: leaderboardData } = useLeaderboard('all_time', 100);
  const { data: userRankData } = useUserRank('all_time');

  const isOwnProfile = user?.id === userId;
  const currentlyReading = currentlyReadingData?.books || [];
  const activities = activityData?.activities || [];
  const followers = followersData?.users || [];
  const following = followingData?.users || [];

  // Find user's rank on leaderboard
  const userLeaderboardPosition = leaderboardData?.entries?.findIndex(
    (entry) => entry.user_id === userId
  );
  const userRank = userLeaderboardPosition !== undefined && userLeaderboardPosition >= 0
    ? userLeaderboardPosition + 1
    : userRankData?.rank;

  // Format date
  const memberSince = profile?.created_at
    ? new Date(profile.created_at).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
      })
    : null;

  // Handle share profile
  const handleShareProfile = () => {
    const url = `${window.location.origin}/user/${userId}`;
    if (navigator.share) {
      navigator.share({
        title: `${profile?.display_name || profile?.username || 'User'}'s Profile`,
        url,
      });
    } else {
      navigator.clipboard.writeText(url);
      toast.success('Profile link copied to clipboard!');
    }
  };

  // Handle followers/following click
  const handleFollowersClick = () => {
    setModalType('followers');
    setShowFollowersModal(true);
  };

  const handleFollowingClick = () => {
    setModalType('following');
    setShowFollowingModal(true);
  };

  if (profileLoading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <Loader className="h-12 w-12 text-purple-400 animate-spin" />
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
        <div className="text-center">
          <User className="h-16 w-16 text-gray-600 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">User not found</h2>
          <p className="text-gray-400 mb-6">This profile doesn't exist or is private</p>
          <button
            onClick={() => navigate(-1)}
            className="px-6 py-3 bg-purple-500 hover:bg-purple-600 text-white rounded-lg transition"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="min-h-screen bg-gray-950 py-8 px-4"
    >
      <div className="max-w-7xl mx-auto">
        {/* Back Button */}
        <button
          onClick={() => navigate(-1)}
          className="flex items-center space-x-2 text-gray-400 hover:text-white mb-6 transition"
        >
          <ArrowLeft className="h-5 w-5" />
          <span>Back</span>
        </button>

        <div className="lg:grid lg:grid-cols-3 lg:gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Profile Header */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-2xl p-8 border border-gray-700"
            >
              <div className="flex flex-col sm:flex-row items-center sm:items-start space-y-4 sm:space-y-0 sm:space-x-6">
                {/* Avatar */}
                <div className="relative flex-shrink-0">
                  {profile.avatar_url ? (
                    <img
                      src={profile.avatar_url}
                      alt={profile.display_name || profile.username || 'User'}
                      className="w-28 h-28 rounded-2xl object-cover border-4 border-purple-500/30"
                    />
                  ) : (
                    <div className="w-28 h-28 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center border-4 border-purple-500/30">
                      <span className="text-4xl font-bold text-white">
                        {(profile.display_name || profile.username || '?')[0].toUpperCase()}
                      </span>
                    </div>
                  )}
                  {userRank && userRank <= 10 && (
                    <div className="absolute -top-2 -right-2 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-full p-2 border-2 border-gray-900">
                      <Trophy className="h-5 w-5 text-white" />
                    </div>
                  )}
                </div>

                {/* Name & Bio */}
                <div className="flex-1 text-center sm:text-left space-y-3 w-full">
                  <div>
                    <h1 className="text-3xl font-bold text-white mb-1">
                      {profile.display_name || profile.username || 'Anonymous'}
                    </h1>
                    {profile.username && profile.display_name && (
                      <p className="text-gray-400">@{profile.username}</p>
                    )}
                  </div>

                  {profile.bio && (
                    <p className="text-gray-300 max-w-2xl">{profile.bio}</p>
                  )}

                  <div className="flex flex-wrap gap-4 justify-center sm:justify-start text-sm text-gray-400">
                    {memberSince && (
                      <div className="flex items-center space-x-2">
                        <Calendar className="h-4 w-4" />
                        <span>Joined {memberSince}</span>
                      </div>
                    )}
                    {profile.listening_stats && (
                      <div className="flex items-center space-x-2">
                        <Clock className="h-4 w-4" />
                        <span>{profile.listening_stats.total_listening_hours.toFixed(1)}h listened</span>
                      </div>
                    )}
                  </div>

                  {/* Action Buttons */}
                  <div className="flex flex-wrap gap-3 justify-center sm:justify-start">
                    {!isOwnProfile && (
                      <FollowButton
                        userId={userId!}
                        isFollowing={profile.is_following || false}
                        size="md"
                      />
                    )}
                    {isOwnProfile && (
                      <Link
                        to="/profile"
                        className="px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-lg font-medium transition"
                      >
                        Edit Profile
                      </Link>
                    )}
                    <button
                      onClick={handleShareProfile}
                      className="flex items-center space-x-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-medium transition"
                    >
                      <Share2 className="h-4 w-4" />
                      <span>Share</span>
                    </button>
                  </div>
                </div>
              </div>

              {/* Social Stats */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-8 pt-6 border-t border-gray-700">
                <button
                  onClick={handleFollowersClick}
                  className="text-center hover:bg-gray-700/50 rounded-lg p-3 transition group"
                >
                  <p className="text-2xl font-bold text-white group-hover:text-purple-400 transition">
                    {profile.followers_count || 0}
                  </p>
                  <p className="text-sm text-gray-400">Followers</p>
                </button>

                <button
                  onClick={handleFollowingClick}
                  className="text-center hover:bg-gray-700/50 rounded-lg p-3 transition group"
                >
                  <p className="text-2xl font-bold text-white group-hover:text-purple-400 transition">
                    {profile.following_count || 0}
                  </p>
                  <p className="text-sm text-gray-400">Following</p>
                </button>

                <div className="text-center p-3">
                  <p className="text-2xl font-bold text-white">
                    {profile.listening_stats?.total_listening_hours?.toFixed(0) || 0}h
                  </p>
                  <p className="text-sm text-gray-400">Listening</p>
                </div>

                <div className="text-center p-3">
                  <p className="text-2xl font-bold text-white">
                    {profile.listening_stats?.books_completed || 0}
                  </p>
                  <p className="text-sm text-gray-400">Books</p>
                </div>
              </div>
            </motion.div>

            {/* Currently Reading */}
            {currentlyReading.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="bg-gray-800 rounded-xl p-6"
              >
                <h3 className="text-xl font-semibold text-white mb-4 flex items-center space-x-2">
                  <BookOpen className="h-5 w-5 text-purple-400" />
                  <span>Currently Reading</span>
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                  {currentlyReading.map((book) => (
                    <Link
                      key={book.book_id}
                      to={`/book/${book.book_id}`}
                      className="group"
                    >
                      <div className="relative aspect-[2/3] rounded-lg overflow-hidden bg-gray-700 mb-2">
                        {book.cover_url ? (
                          <img
                            src={book.cover_url}
                            alt={book.title}
                            className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center">
                            <BookOpen className="h-12 w-12 text-gray-500" />
                          </div>
                        )}
                        {/* Progress bar */}
                        <div className="absolute bottom-0 left-0 right-0 h-2 bg-gray-900/80">
                          <div
                            className="h-full bg-gradient-to-r from-purple-500 to-pink-500"
                            style={{ width: `${book.progress}%` }}
                          />
                        </div>
                      </div>
                      <p className="text-sm font-medium text-white line-clamp-2 group-hover:text-purple-400 transition">
                        {book.title}
                      </p>
                      <p className="text-xs text-gray-400">{book.progress}% complete</p>
                    </Link>
                  ))}
                </div>
              </motion.div>
            )}

            {/* Activity Tabs */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-gray-800 rounded-xl p-6"
            >
              {/* Tab Headers */}
              <div className="flex space-x-4 border-b border-gray-700 mb-6">
                <button
                  onClick={() => setActiveTab('activity')}
                  className={`pb-3 px-4 font-medium transition-colors relative ${
                    activeTab === 'activity'
                      ? 'text-purple-400'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  Recent Activity
                  {activeTab === 'activity' && (
                    <motion.div
                      layoutId="activeTab"
                      className="absolute bottom-0 left-0 right-0 h-0.5 bg-purple-400"
                    />
                  )}
                </button>
                <button
                  onClick={() => setActiveTab('books')}
                  className={`pb-3 px-4 font-medium transition-colors relative ${
                    activeTab === 'books'
                      ? 'text-purple-400'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  Completed Books
                  {activeTab === 'books' && (
                    <motion.div
                      layoutId="activeTab"
                      className="absolute bottom-0 left-0 right-0 h-0.5 bg-purple-400"
                    />
                  )}
                </button>
                <button
                  onClick={() => setActiveTab('reviews')}
                  className={`pb-3 px-4 font-medium transition-colors relative ${
                    activeTab === 'reviews'
                      ? 'text-purple-400'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  Reviews
                  {activeTab === 'reviews' && (
                    <motion.div
                      layoutId="activeTab"
                      className="absolute bottom-0 left-0 right-0 h-0.5 bg-purple-400"
                    />
                  )}
                </button>
              </div>

              {/* Tab Content */}
              <div className="min-h-[300px]">
                {activeTab === 'activity' && (
                  <div className="space-y-4">
                    {activities.length > 0 ? (
                      activities.map((activity) => {
                        const timeAgo = formatDistanceToNow(new Date(activity.created_at), {
                          addSuffix: true,
                        });

                        return (
                          <div
                            key={activity.id}
                            className="bg-gray-700/50 rounded-lg p-4 hover:bg-gray-700 transition"
                          >
                            <div className="flex items-start space-x-4">
                              {/* Book Cover (if available) */}
                              {activity.book_cover_url && (
                                <Link
                                  to={`/book/${activity.book_id}`}
                                  className="flex-shrink-0"
                                >
                                  <img
                                    src={activity.book_cover_url}
                                    alt={activity.book_title || 'Book'}
                                    className="w-16 h-20 object-cover rounded shadow-md hover:opacity-80 transition"
                                  />
                                </Link>
                              )}

                              <div className="flex-1 min-w-0">
                                {/* Activity Message */}
                                <p className="text-white font-medium mb-2">
                                  {activity.message}
                                </p>

                                {/* Book Title (if available) */}
                                {activity.book_title && activity.book_id && (
                                  <Link
                                    to={`/book/${activity.book_id}`}
                                    className="text-purple-400 hover:text-purple-300 transition font-medium"
                                  >
                                    {activity.book_title}
                                  </Link>
                                )}

                                {/* Metadata (progress, hours, etc.) */}
                                {activity.metadata && (
                                  <div className="flex flex-wrap gap-3 mt-2 text-sm text-gray-400">
                                    {activity.metadata.progress !== undefined && (
                                      <span>{activity.metadata.progress}% complete</span>
                                    )}
                                    {activity.metadata.listening_hours !== undefined && (
                                      <span>{activity.metadata.listening_hours}h listened</span>
                                    )}
                                    {activity.metadata.milestone && (
                                      <span className="text-purple-400">
                                        {activity.metadata.milestone}
                                      </span>
                                    )}
                                  </div>
                                )}

                                {/* Time Ago */}
                                <p className="text-xs text-gray-500 mt-2">{timeAgo}</p>
                              </div>
                            </div>
                          </div>
                        );
                      })
                    ) : (
                      <div className="text-center py-12">
                        <MessageCircle className="h-12 w-12 text-gray-600 mx-auto mb-3" />
                        <p className="text-gray-400">No recent activity</p>
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'books' && (
                  <div className="text-center py-12">
                    <BookOpen className="h-12 w-12 text-gray-600 mx-auto mb-3" />
                    <p className="text-gray-400">Completed books coming soon</p>
                  </div>
                )}

                {activeTab === 'reviews' && (
                  <div className="text-center py-12">
                    <MessageCircle className="h-12 w-12 text-gray-600 mx-auto mb-3" />
                    <p className="text-gray-400">Reviews coming soon</p>
                  </div>
                )}
              </div>
            </motion.div>
          </div>

          {/* Sidebar (Desktop Only) */}
          <div className="hidden lg:block space-y-6">
            {/* Leaderboard Position */}
            {userRank && userRank <= 100 && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 }}
                className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 border border-purple-500/30 rounded-xl p-6"
              >
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
                  <Trophy className="h-5 w-5 text-yellow-400" />
                  <span>Leaderboard</span>
                </h3>
                <div className="text-center">
                  <p className="text-4xl font-bold text-purple-400 mb-1">#{userRank}</p>
                  <p className="text-sm text-gray-300">All-time rank</p>
                </div>
                <Link
                  to="/leaderboard"
                  className="block mt-4 text-center text-purple-400 hover:text-purple-300 text-sm font-medium transition"
                >
                  View Full Leaderboard →
                </Link>
              </motion.div>
            )}

            {/* Mutual Followers */}
            {!isOwnProfile && followers.length > 0 && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 }}
                className="bg-gray-800 rounded-xl p-6"
              >
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
                  <Users className="h-5 w-5 text-purple-400" />
                  <span>Followers</span>
                </h3>
                <div className="space-y-3">
                  {followers.slice(0, 5).map((follower) => (
                    <Link
                      key={follower.user_id}
                      to={`/user/${follower.user_id}`}
                      className="flex items-center space-x-3 hover:bg-gray-700/50 rounded-lg p-2 -mx-2 transition"
                    >
                      {follower.avatar_url ? (
                        <img
                          src={follower.avatar_url}
                          alt={follower.display_name || follower.username || 'User'}
                          className="w-10 h-10 rounded-full object-cover"
                        />
                      ) : (
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                          <span className="text-white font-bold text-sm">
                            {(follower.display_name || follower.username || '?')[0].toUpperCase()}
                          </span>
                        </div>
                      )}
                      <div className="flex-1 min-w-0">
                        <p className="text-white font-medium truncate">
                          {follower.display_name || follower.username}
                        </p>
                        {follower.username && follower.display_name && (
                          <p className="text-xs text-gray-400 truncate">@{follower.username}</p>
                        )}
                      </div>
                    </Link>
                  ))}
                </div>
                {followers.length > 5 && (
                  <button
                    onClick={handleFollowersClick}
                    className="block w-full mt-4 text-center text-purple-400 hover:text-purple-300 text-sm font-medium transition"
                  >
                    View All {profile.followers_count} Followers →
                  </button>
                )}
              </motion.div>
            )}
          </div>
        </div>
      </div>

      {/* Modals */}
      <UsersListModal
        isOpen={showFollowersModal || showFollowingModal}
        onClose={() => {
          setShowFollowersModal(false);
          setShowFollowingModal(false);
        }}
        userId={userId!}
        type={modalType}
      />
    </motion.div>
  );
}
