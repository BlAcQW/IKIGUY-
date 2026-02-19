/**
 * UnhideBookModal Component
 *
 * Modal for unhiding a previously hidden book (admin action).
 * Shows original hide reason and allows optional reason for unhiding.
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Eye, CheckCircle, AlertCircle } from 'lucide-react';
import { generatePlaceholderCover, getBookCoverUrl } from '../lib/bookCoverUtils';

interface UnhideBookModalProps {
  isOpen: boolean;
  onClose: () => void;
  book: {
    id: string;
    title: string;
    author: string;
    cover_url?: string;
    hidden_reason?: string;
    hidden_at?: string;
    hidden_by_email?: string;
  };
  onUnhide: (reason?: string) => Promise<void>;
}

export default function UnhideBookModal({
  isOpen,
  onClose,
  book,
  onUnhide,
}: UnhideBookModalProps) {
  const [reason, setReason] = useState('');
  const [unhiding, setUnhiding] = useState(false);

  const handleUnhide = async () => {
    setUnhiding(true);
    try {
      await onUnhide(reason.trim() || undefined);
      setReason('');
      onClose();
    } catch (error) {
      // Error handled by parent
    } finally {
      setUnhiding(false);
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="bg-gray-800 border border-green-500/30 rounded-xl p-6 w-full max-w-md"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <div className="p-2 bg-green-500/20 rounded-lg">
                <Eye className="w-5 h-5 text-green-400" />
              </div>
              <h2 className="text-xl font-bold text-white">Unhide Book</h2>
            </div>
            <button
              onClick={onClose}
              className="p-1 hover:bg-gray-700 rounded transition-colors"
            >
              <X className="w-5 h-5 text-gray-400" />
            </button>
          </div>

          {/* Book Preview */}
          <div className="mb-6 p-4 bg-gray-900/50 border border-gray-700 rounded-lg">
            <div className="flex items-start gap-3">
              <img
                src={getBookCoverUrl(book.cover_url, book.title, book.author)}
                alt={book.title}
                className="w-16 h-24 object-cover rounded shadow-lg"
                onError={(e) => {
                  e.currentTarget.src = generatePlaceholderCover(book.title, book.author);
                  e.currentTarget.onerror = null;
                }}
              />
              <div className="flex-1 min-w-0">
                <h3 className="text-white font-semibold truncate">{book.title}</h3>
                <p className="text-sm text-gray-400">by {book.author}</p>
              </div>
            </div>
          </div>

          {/* Original Hide Info */}
          {book.hidden_reason && (
            <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h4 className="text-red-400 font-semibold mb-1">Originally hidden because:</h4>
                  <p className="text-sm text-gray-300">{book.hidden_reason}</p>
                  {book.hidden_by_email && (
                    <p className="text-xs text-gray-500 mt-2">
                      Hidden by {book.hidden_by_email}
                      {book.hidden_at &&
                        ` on ${new Date(book.hidden_at).toLocaleDateString()}`}
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Success Info */}
          <div className="mb-6 p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
            <div className="flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h4 className="text-green-400 font-semibold mb-1">Unhiding this book will:</h4>
                <ul className="text-sm text-gray-300 space-y-1">
                  <li>• Restore it to its previous visibility state</li>
                  <li>• Make it visible to users again (if public)</li>
                  <li>• Remove the "Hidden by Admin" badge</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Optional Reason Input */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Reason for unhiding <span className="text-gray-500">(optional)</span>
            </label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Enter optional reason for unhiding this book..."
              rows={3}
              className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-green-500 resize-none"
              disabled={unhiding}
            />
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3">
            <button
              onClick={onClose}
              disabled={unhiding}
              className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleUnhide}
              disabled={unhiding}
              className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors disabled:opacity-50"
            >
              {unhiding ? 'Unhiding...' : 'Unhide Book'}
            </button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
