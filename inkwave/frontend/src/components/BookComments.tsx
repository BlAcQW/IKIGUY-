/**
 * BookComments Component
 *
 * Displays and manages user comments/reviews for a book.
 * Features:
 * - Star ratings
 * - Comment threads
 * - Helpful votes
 * - Create/edit/delete comments
 */

import { useState, useEffect } from 'react';
import { Star, ThumbsUp, Edit2, Trash2, Send, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '../lib/api';
import toast from 'react-hot-toast';

interface Comment {
  comment_id: string;
  user_id: string;
  user_email: string;
  user_display_name?: string;
  user_avatar_url?: string;
  rating?: number;
  title?: string;
  comment_text: string;
  helpful_count: number;
  user_found_helpful: boolean;
  is_author: boolean;
  created_at: string;
  updated_at: string;
}

interface BookCommentsProps {
  bookId: string;
}

export default function BookComments({ bookId }: BookCommentsProps) {
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState<'recent' | 'helpful' | 'rating'>('recent');

  // New comment form
  const [showCommentForm, setShowCommentForm] = useState(false);
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [title, setTitle] = useState('');
  const [commentText, setCommentText] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Edit mode
  const [editingCommentId, setEditingCommentId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [editText, setEditText] = useState('');
  const [editRating, setEditRating] = useState(0);

  useEffect(() => {
    fetchComments();
  }, [bookId, sortBy]);

  const fetchComments = async () => {
    setLoading(true);
    try {
      const response = await api.comments.list(bookId, {
        sort_by: sortBy,
        limit: 50,
      });
      setComments(response.data);
    } catch (error) {
      console.error('Failed to fetch comments:', error);
      toast.error('Failed to load comments');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitComment = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!commentText.trim()) {
      toast.error('Please enter a comment');
      return;
    }

    setSubmitting(true);
    try {
      await api.comments.create(bookId, {
        rating: rating > 0 ? rating : undefined,
        title: title.trim() || undefined,
        comment_text: commentText.trim(),
      });

      toast.success('Comment posted successfully!');
      setShowCommentForm(false);
      setRating(0);
      setTitle('');
      setCommentText('');
      fetchComments();
    } catch (error: any) {
      console.error('Failed to post comment:', error);
      toast.error(error.response?.data?.detail || 'Failed to post comment');
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggleHelpful = async (commentId: string) => {
    try {
      const response = await api.comments.toggleHelpful(commentId);

      // Update local state
      setComments(prev =>
        prev.map(c =>
          c.comment_id === commentId
            ? {
                ...c,
                user_found_helpful: response.data.helpful,
                helpful_count: response.data.helpful_count,
              }
            : c
        )
      );

      toast.success(response.data.helpful ? 'Marked as helpful' : 'Removed helpful mark');
    } catch (error: any) {
      console.error('Failed to toggle helpful:', error);
      toast.error(error.response?.data?.detail || 'Failed to update');
    }
  };

  const handleStartEdit = (comment: Comment) => {
    setEditingCommentId(comment.comment_id);
    setEditTitle(comment.title || '');
    setEditText(comment.comment_text);
    setEditRating(comment.rating || 0);
  };

  const handleSaveEdit = async (commentId: string) => {
    try {
      await api.comments.update(commentId, {
        rating: editRating > 0 ? editRating : undefined,
        title: editTitle.trim() || undefined,
        comment_text: editText.trim(),
      });

      toast.success('Comment updated successfully!');
      setEditingCommentId(null);
      fetchComments();
    } catch (error: any) {
      console.error('Failed to update comment:', error);
      toast.error(error.response?.data?.detail || 'Failed to update comment');
    }
  };

  const handleDeleteComment = async (commentId: string) => {
    if (!confirm('Are you sure you want to delete this comment?')) {
      return;
    }

    try {
      await api.comments.delete(commentId);
      toast.success('Comment deleted successfully!');
      fetchComments();
    } catch (error: any) {
      console.error('Failed to delete comment:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete comment');
    }
  };

  const renderStars = (currentRating: number, interactive: boolean = false, onRate?: (rating: number) => void) => {
    const displayRating = interactive ? (hoverRating || currentRating) : currentRating;

    return (
      <div className="flex items-center gap-1">
        {[1, 2, 3, 4, 5].map(star => (
          <button
            key={star}
            type="button"
            disabled={!interactive}
            onClick={() => onRate && onRate(star === currentRating ? 0 : star)}
            onMouseEnter={() => interactive && setHoverRating(star)}
            onMouseLeave={() => interactive && setHoverRating(0)}
            className={`${interactive ? 'cursor-pointer' : 'cursor-default'} transition-transform hover:scale-110`}
          >
            <Star
              className={`w-5 h-5 ${
                star <= displayRating
                  ? 'fill-yellow-500 text-yellow-500'
                  : 'text-gray-400'
              }`}
            />
          </button>
        ))}
      </div>
    );
  };

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      const now = new Date();
      const diff = now.getTime() - date.getTime();
      const days = Math.floor(diff / (1000 * 60 * 60 * 24));

      if (days === 0) return 'Today';
      if (days === 1) return 'Yesterday';
      if (days < 7) return `${days} days ago`;
      if (days < 30) return `${Math.floor(days / 7)} weeks ago`;
      if (days < 365) return `${Math.floor(days / 30)} months ago`;
      return `${Math.floor(days / 365)} years ago`;
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">
          Reviews & Comments ({comments.length})
        </h2>

        <button
          onClick={() => setShowCommentForm(!showCommentForm)}
          className="px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-lg transition-colors"
        >
          Write a Review
        </button>
      </div>

      {/* Sort Options */}
      <div className="flex items-center gap-3 text-sm">
        <span className="text-gray-400">Sort by:</span>
        {['recent', 'helpful', 'rating'].map(option => (
          <button
            key={option}
            onClick={() => setSortBy(option as any)}
            className={`px-3 py-1 rounded-full transition-colors ${
              sortBy === option
                ? 'bg-purple-500 text-white'
                : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
            }`}
          >
            {option.charAt(0).toUpperCase() + option.slice(1)}
          </button>
        ))}
      </div>

      {/* Comment Form */}
      <AnimatePresence>
        {showCommentForm && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-gray-800 rounded-xl p-6 border border-gray-700"
          >
            <form onSubmit={handleSubmitComment} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Rating (Optional)
                </label>
                {renderStars(rating, true, setRating)}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Title (Optional)
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Summarize your review"
                  className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  maxLength={200}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Your Review *
                </label>
                <textarea
                  value={commentText}
                  onChange={(e) => setCommentText(e.target.value)}
                  placeholder="Share your thoughts about this book..."
                  required
                  rows={4}
                  className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
                  maxLength={5000}
                />
                <div className="text-xs text-gray-500 mt-1">
                  {commentText.length} / 5000
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  type="submit"
                  disabled={submitting || !commentText.trim()}
                  className="flex items-center gap-2 px-4 py-2 bg-purple-500 hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
                >
                  <Send className="w-4 h-4" />
                  {submitting ? 'Posting...' : 'Post Review'}
                </button>

                <button
                  type="button"
                  onClick={() => setShowCommentForm(false)}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg transition-colors"
                >
                  Cancel
                </button>
              </div>
            </form>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Comments List */}
      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500 mx-auto mb-3"></div>
          <p className="text-gray-400 text-sm">Loading comments...</p>
        </div>
      ) : comments.length === 0 ? (
        <div className="text-center py-12 bg-gray-800/50 rounded-xl border border-gray-700">
          <p className="text-gray-400">No reviews yet. Be the first to share your thoughts!</p>
        </div>
      ) : (
        <div className="space-y-4">
          {comments.map(comment => (
            <motion.div
              key={comment.comment_id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-gray-800 rounded-xl p-6 border border-gray-700"
            >
              {editingCommentId === comment.comment_id ? (
                // Edit Mode
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Rating
                    </label>
                    {renderStars(editRating, true, setEditRating)}
                  </div>

                  <input
                    type="text"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    placeholder="Title"
                    className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />

                  <textarea
                    value={editText}
                    onChange={(e) => setEditText(e.target.value)}
                    rows={4}
                    className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
                  />

                  <div className="flex gap-3">
                    <button
                      onClick={() => handleSaveEdit(comment.comment_id)}
                      className="px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-lg transition-colors"
                    >
                      Save
                    </button>
                    <button
                      onClick={() => setEditingCommentId(null)}
                      className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                // View Mode
                <>
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-semibold">
                        {(comment.user_display_name || comment.user_email).charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <p className="text-white font-medium">
                          {comment.user_display_name || comment.user_email}
                        </p>
                        <p className="text-sm text-gray-400">{formatDate(comment.created_at)}</p>
                      </div>
                    </div>

                    {comment.is_author && (
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleStartEdit(comment)}
                          className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
                          title="Edit"
                        >
                          <Edit2 className="w-4 h-4 text-gray-400" />
                        </button>
                        <button
                          onClick={() => handleDeleteComment(comment.comment_id)}
                          className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4 text-red-400" />
                        </button>
                      </div>
                    )}
                  </div>

                  {comment.rating && (
                    <div className="mb-3">{renderStars(comment.rating, false)}</div>
                  )}

                  {comment.title && (
                    <h3 className="text-lg font-semibold text-white mb-2">{comment.title}</h3>
                  )}

                  <p className="text-gray-300 whitespace-pre-wrap mb-4">{comment.comment_text}</p>

                  <button
                    onClick={() => handleToggleHelpful(comment.comment_id)}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors ${
                      comment.user_found_helpful
                        ? 'bg-purple-500/20 text-purple-400'
                        : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
                    }`}
                  >
                    <ThumbsUp className={`w-4 h-4 ${comment.user_found_helpful ? 'fill-current' : ''}`} />
                    <span className="text-sm">
                      Helpful ({comment.helpful_count})
                    </span>
                  </button>
                </>
              )}
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
