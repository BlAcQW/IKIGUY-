/**
 * UserListeningHistoryModal Component
 * Shows detailed listening history for a user (admin only)
 * Displays all books listened to and time spent on each
 */

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  BookOpen,
  Clock,
  Loader,
  TrendingUp,
  Calendar,
} from 'lucide-react';
import { api } from '../lib/api';
import toast from 'react-hot-toast';

interface BookListeningHistory {
  book_id: string;
  book_title: string;
  listening_minutes: number;
  listening_hours: number;
  session_count: number;
  last_listened: string | null;
}

interface UserListeningHistory {
  user_id: string;
  email: string;
  display_name: string | null;
  total_listening_hours: number;
  total_books: number;
  books: BookListeningHistory[];
}

interface UserListeningHistoryModalProps {
  userId: string;
  onClose: () => void;
}

export default function UserListeningHistoryModal({
  userId,
  onClose,
}: UserListeningHistoryModalProps) {
  const [history, setHistory] = useState<UserListeningHistory | null>(null);
  const [loading, setLoading] = useState(true);

  // Fetch user listening history
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        setLoading(true);
        const response = await api.leaderboard.getUserHistory(userId);
        setHistory(response.data);
      } catch (error: any) {
        console.error('Failed to fetch user history:', error);
        const message = error.response?.data?.detail || 'Failed to load listening history';
        toast.error(message);
        // Close modal if we get a 403 (not admin)
        if (error.response?.status === 403) {
          onClose();
        }
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [userId, onClose]);

  // Format date
  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        />

        {/* Modal */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className="relative bg-gray-900 rounded-xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden border border-gray-800"
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-4 flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-white">Listening History</h2>
              {history && (
                <p className="text-white/80 text-sm mt-1">
                  {history.display_name || history.email}
                </p>
              )}
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/10 rounded-lg transition-colors"
              aria-label="Close"
            >
              <X size={20} className="text-white" />
            </button>
          </div>

          {/* Content */}
          <div className="overflow-y-auto max-h-[calc(80vh-80px)]">
            {loading ? (
              <div className="flex items-center justify-center py-20">
                <Loader className="animate-spin text-blue-500" size={32} />
              </div>
            ) : !history ? (
              <div className="text-center py-20">
                <BookOpen size={48} className="text-gray-600 mx-auto mb-4" />
                <p className="text-gray-400 text-lg">No listening history found</p>
              </div>
            ) : (
              <>
                {/* Summary Stats */}
                <div className="grid grid-cols-3 gap-4 p-6 border-b border-gray-800">
                  <div className="bg-gray-800/50 rounded-lg p-4">
                    <div className="flex items-center gap-2 text-gray-400 text-sm mb-2">
                      <Clock size={16} />
                      <span>Total Hours</span>
                    </div>
                    <p className="text-2xl font-bold text-white">
                      {history.total_listening_hours.toFixed(1)}
                    </p>
                  </div>
                  <div className="bg-gray-800/50 rounded-lg p-4">
                    <div className="flex items-center gap-2 text-gray-400 text-sm mb-2">
                      <BookOpen size={16} />
                      <span>Books</span>
                    </div>
                    <p className="text-2xl font-bold text-white">
                      {history.total_books}
                    </p>
                  </div>
                  <div className="bg-gray-800/50 rounded-lg p-4">
                    <div className="flex items-center gap-2 text-gray-400 text-sm mb-2">
                      <TrendingUp size={16} />
                      <span>Sessions</span>
                    </div>
                    <p className="text-2xl font-bold text-white">
                      {history.books.reduce((sum, book) => sum + book.session_count, 0)}
                    </p>
                  </div>
                </div>

                {/* Books List */}
                <div className="p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">
                    Books Listened ({history.books.length})
                  </h3>
                  {history.books.length === 0 ? (
                    <div className="text-center py-10">
                      <BookOpen size={32} className="text-gray-600 mx-auto mb-3" />
                      <p className="text-gray-400">No books listened yet</p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {history.books.map((book, index) => (
                        <motion.div
                          key={book.book_id}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: index * 0.05 }}
                          className="bg-gray-800/30 border border-gray-800 rounded-lg p-4 hover:bg-gray-800/50 transition-colors"
                        >
                          <div className="flex items-start justify-between gap-4">
                            {/* Book Info */}
                            <div className="flex-1 min-w-0">
                              <h4 className="text-white font-medium truncate mb-1">
                                {book.book_title}
                              </h4>
                              <div className="flex items-center gap-4 text-sm text-gray-400">
                                <div className="flex items-center gap-1">
                                  <Clock size={14} />
                                  <span>{book.listening_hours.toFixed(1)} hrs</span>
                                </div>
                                <div className="flex items-center gap-1">
                                  <TrendingUp size={14} />
                                  <span>{book.session_count} sessions</span>
                                </div>
                              </div>
                            </div>

                            {/* Last Listened */}
                            <div className="text-right flex-shrink-0">
                              <div className="flex items-center gap-1 text-xs text-gray-500 mb-1">
                                <Calendar size={12} />
                                <span>Last listened</span>
                              </div>
                              <p className="text-sm text-gray-400">
                                {formatDate(book.last_listened)}
                              </p>
                            </div>
                          </div>

                          {/* Progress Bar */}
                          <div className="mt-3">
                            <div className="w-full bg-gray-700 rounded-full h-1.5">
                              <div
                                className="bg-gradient-to-r from-blue-500 to-purple-500 h-1.5 rounded-full"
                                style={{
                                  width: `${Math.min(
                                    (book.listening_hours / history.total_listening_hours) * 100,
                                    100
                                  )}%`,
                                }}
                              />
                            </div>
                            <p className="text-xs text-gray-500 mt-1">
                              {((book.listening_hours / history.total_listening_hours) * 100).toFixed(1)}% of
                              total listening time
                            </p>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
