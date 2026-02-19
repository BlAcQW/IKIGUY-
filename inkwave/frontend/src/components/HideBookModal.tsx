/**
 * HideBookModal Component
 *
 * Modal for hiding a book (admin action) with required reason.
 * Hidden books remain visible to the author with a badge.
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, AlertTriangle, Eye, EyeOff } from 'lucide-react';
import { generatePlaceholderCover, getBookCoverUrl } from '../lib/bookCoverUtils';

interface HideBookModalProps {
  isOpen: boolean;
  onClose: () => void;
  book: {
    id: string;
    title: string;
    author: string;
    cover_url?: string;
  };
  onHide: (reason: string) => Promise<void>;
}

export default function HideBookModal({
  isOpen,
  onClose,
  book,
  onHide,
}: HideBookModalProps) {
  const [reason, setReason] = useState('');
  const [hiding, setHiding] = useState(false);

  const handleHide = async () => {
    if (reason.trim().length < 10) {
      return;
    }

    setHiding(true);
    try {
      await onHide(reason.trim());
      setReason('');
      onClose();
    } catch (error) {
      // Error handled by parent
    } finally {
      setHiding(false);
    }
  };

  const isValid = reason.trim().length >= 10;

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
          className="bg-gray-800 border border-red-500/30 rounded-xl p-6 w-full max-w-md"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <div className="p-2 bg-red-500/20 rounded-lg">
                <EyeOff className="w-5 h-5 text-red-400" />
              </div>
              <h2 className="text-xl font-bold text-white">Hide Book</h2>
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

          {/* Warning */}
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h4 className="text-red-400 font-semibold mb-1">Hiding this book will:</h4>
                <ul className="text-sm text-gray-300 space-y-1">
                  <li>• Remove it from "All Books" discovery</li>
                  <li>• Make it invisible to other users</li>
                  <li>• Author will still see it with "Hidden by Admin" badge</li>
                  <li>• Can be unhidden later if needed</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Reason Input */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Reason for hiding <span className="text-red-400">*</span>
            </label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Enter reason for hiding this book (minimum 10 characters)..."
              rows={4}
              className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-red-500 resize-none"
              disabled={hiding}
            />
            <div className="mt-1 flex items-center justify-between">
              <p className="text-xs text-gray-500">
                Minimum 10 characters required
              </p>
              <p
                className={`text-xs ${
                  isValid ? 'text-green-400' : 'text-gray-500'
                }`}
              >
                {reason.trim().length}/10
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3">
            <button
              onClick={onClose}
              disabled={hiding}
              className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleHide}
              disabled={!isValid || hiding}
              className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {hiding ? 'Hiding...' : 'Hide Book'}
            </button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
