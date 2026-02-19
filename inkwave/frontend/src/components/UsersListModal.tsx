/**
 * UsersListModal Component
 * Modal for displaying followers/following lists
 */

import { useEffect, useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Search } from 'lucide-react';
import UserCard from './UserCard';
import { useFollowers, useFollowing } from '../hooks/useSocial';

interface UsersListModalProps {
  isOpen: boolean;
  onClose: () => void;
  userId: string;
  type: 'followers' | 'following';
  title?: string;
}

export default function UsersListModal({
  isOpen,
  onClose,
  userId,
  type,
  title,
}: UsersListModalProps) {
  const [searchQuery, setSearchQuery] = useState('');

  // React Query hooks - only enabled when modal is open
  const followersQuery = useFollowers(userId, undefined, undefined, { enabled: isOpen && type === 'followers' });
  const followingQuery = useFollowing(userId, undefined, undefined, { enabled: isOpen && type === 'following' });

  // Select the appropriate query based on type
  const query = type === 'followers' ? followersQuery : followingQuery;
  const users = query.data?.users || [];
  const loading = query.isLoading;

  // Reset search when modal opens
  useEffect(() => {
    if (isOpen) {
      setSearchQuery('');
    }
  }, [isOpen]);

  // Filter users based on search query
  const filteredUsers = useMemo(() => {
    if (!searchQuery.trim()) {
      return users;
    }

    const query = searchQuery.toLowerCase();
    return users.filter(
      (user) =>
        user.display_name?.toLowerCase().includes(query) ||
        user.username?.toLowerCase().includes(query)
    );
  }, [searchQuery, users]);

  const handleClose = () => {
    setSearchQuery('');
    onClose();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleClose}
            className="fixed inset-0 bg-black bg-opacity-75 backdrop-blur-sm z-40"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            className="fixed inset-x-0 top-1/2 -translate-y-1/2 mx-auto max-w-lg w-full bg-gray-900 rounded-2xl shadow-2xl z-50 max-h-[80vh] flex flex-col"
            style={{ margin: '0 1rem' }}
          >
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-700">
              <h2 className="text-xl font-bold text-white">
                {title || (type === 'followers' ? 'Followers' : 'Following')}
              </h2>
              <button
                onClick={handleClose}
                className="p-2 hover:bg-gray-800 rounded-full transition-colors"
              >
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>

            {/* Search Bar */}
            <div className="p-4 border-b border-gray-700">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search users..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-500 transition-colors"
                />
              </div>
            </div>

            {/* Users List */}
            <div className="flex-1 overflow-y-auto p-4">
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
                </div>
              ) : filteredUsers.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-gray-400">
                    {searchQuery.trim()
                      ? 'No users found'
                      : `No ${type} yet`}
                  </p>
                </div>
              ) : (
                <div className="space-y-2">
                  {filteredUsers.map((user) => (
                    <UserCard
                      key={user.user_id}
                      user={user}
                      variant="compact"
                      showFollowButton={true}
                      showStats={false}
                    />
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
