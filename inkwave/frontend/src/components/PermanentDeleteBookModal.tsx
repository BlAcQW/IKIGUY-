/**
 * PermanentDeleteBookModal Component
 *
 * Modal for permanently deleting a book (admin action - cannot be undone).
 * Requires reason, confirmation checkbox, and typing "DELETE" to confirm.
 */

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Trash2, AlertTriangle, Loader } from 'lucide-react';
import { generatePlaceholderCover, getBookCoverUrl } from '../lib/bookCoverUtils';

interface PermanentDeleteBookModalProps {
  isOpen: boolean;
  onClose: () => void;
  book: {
    id: string;
    title: string;
    author: string;
    cover_url?: string;
  };
  onDelete: (reason: string) => Promise<void>;
}

export default function PermanentDeleteBookModal({
  isOpen,
  onClose,
  book,
  onDelete,
}: PermanentDeleteBookModalProps) {
  const [reason, setReason] = useState('');
  const [confirmText, setConfirmText] = useState('');
  const [understood, setUnderstood] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [preview, setPreview] = useState<any>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);

  const isValid =
    reason.trim().length >= 10 &&
    confirmText.toUpperCase() === 'DELETE' &&
    understood;

  // Load deletion preview
  useEffect(() => {
    if (isOpen && book.id) {
      loadDeletionPreview();
    }
  }, [isOpen, book.id]);

  const loadDeletionPreview = async () => {
    setLoadingPreview(true);
    try {
      // Import api dynamically to avoid circular dependencies
      const { api } = await import('../lib/api');
      const response = await api.books.getDeletionPreview(book.id);
      setPreview(response.data);
    } catch (error) {
      console.error('Failed to load deletion preview:', error);
    } finally {
      setLoadingPreview(false);
    }
  };

  const handleDelete = async () => {
    if (!isValid) return;

    setDeleting(true);
    try {
      await onDelete(reason.trim());
      setReason('');
      setConfirmText('');
      setUnderstood(false);
      onClose();
    } catch (error) {
      // Error handled by parent
    } finally {
      setDeleting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="bg-gray-800 border-2 border-red-600 rounded-xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <div className="p-2 bg-red-600/20 rounded-lg">
                <Trash2 className="w-6 h-6 text-red-500" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-red-500">Permanent Deletion</h2>
                <p className="text-xs text-red-400">This action cannot be undone!</p>
              </div>
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

          {/* Severe Warning */}
          <div className="mb-6 p-4 bg-red-600/20 border-2 border-red-600 rounded-lg">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-6 h-6 text-red-500 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h4 className="text-red-500 font-bold mb-2">⚠️ PERMANENT DELETION WARNING</h4>
                <p className="text-sm text-red-300 mb-3 font-semibold">
                  This will PERMANENTLY DELETE all book data. This action CANNOT be undone!
                </p>

                {loadingPreview ? (
                  <div className="flex items-center gap-2 text-gray-400">
                    <Loader className="w-4 h-4 animate-spin" />
                    <span className="text-xs">Loading deletion preview...</span>
                  </div>
                ) : preview ? (
                  <div className="text-xs text-gray-300 space-y-1">
                    <p className="font-semibold text-red-400 mb-2">Will delete:</p>
                    <ul className="space-y-0.5 pl-2">
                      <li>• {preview.will_delete.book_record} book record</li>
                      <li>• {preview.will_delete.chunks} text chunks</li>
                      <li>• {preview.will_delete.embeddings} embeddings</li>
                      <li>• {preview.will_delete.reading_sessions} reading sessions</li>
                      <li>• {preview.will_delete.interactions} interactions</li>
                      <li>• {preview.will_delete.voice_settings} voice settings</li>
                      <li>• {preview.will_delete.audio_cache_files} audio cache files</li>
                      {preview.will_delete.storage_files?.length > 0 && (
                        <li>• {preview.will_delete.storage_files.length} storage files</li>
                      )}
                    </ul>
                  </div>
                ) : null}
              </div>
            </div>
          </div>

          {/* Reason Input */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Reason for permanent deletion <span className="text-red-400">*</span>
            </label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Enter detailed reason for permanent deletion (minimum 10 characters)..."
              rows={3}
              className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-red-500 resize-none"
              disabled={deleting}
            />
            <p
              className={`text-xs mt-1 ${
                reason.trim().length >= 10 ? 'text-green-400' : 'text-gray-500'
              }`}
            >
              {reason.trim().length}/10 characters
            </p>
          </div>

          {/* Confirmation Checkbox */}
          <div className="mb-4">
            <label className="flex items-start gap-3 cursor-pointer group">
              <input
                type="checkbox"
                checked={understood}
                onChange={(e) => setUnderstood(e.target.checked)}
                disabled={deleting}
                className="mt-1 w-4 h-4 text-red-600 bg-gray-900 border-gray-600 rounded focus:ring-red-500 focus:ring-2"
              />
              <span className="text-sm text-gray-300 group-hover:text-white transition-colors">
                I understand this action is <strong className="text-red-400">permanent and cannot be undone</strong>. All book data will be permanently deleted.
              </span>
            </label>
          </div>

          {/* Type DELETE Confirmation */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Type <code className="px-2 py-1 bg-red-600/20 text-red-400 rounded">DELETE</code> to confirm <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={confirmText}
              onChange={(e) => setConfirmText(e.target.value)}
              placeholder="Type DELETE in capital letters"
              className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-red-500"
              disabled={deleting}
            />
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3">
            <button
              onClick={onClose}
              disabled={deleting}
              className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleDelete}
              disabled={!isValid || deleting}
              className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-bold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {deleting ? 'Deleting...' : 'DELETE PERMANENTLY'}
            </button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
