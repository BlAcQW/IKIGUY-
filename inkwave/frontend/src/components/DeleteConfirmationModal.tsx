/**
 * Delete Confirmation Modal
 *
 * Reusable modal for confirming delete actions.
 */

import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, X } from 'lucide-react';

interface DeleteConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title?: string;
  message?: string;
  itemName?: string;
  confirmText?: string;
  cancelText?: string;
  isDeleting?: boolean;
}

export function DeleteConfirmationModal({
  isOpen,
  onClose,
  onConfirm,
  title = 'Confirm Delete',
  message = 'Are you sure you want to delete this item? This action cannot be undone.',
  itemName,
  confirmText = 'Delete',
  cancelText = 'Cancel',
  isDeleting = false,
}: DeleteConfirmationModalProps) {
  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-black/60 backdrop-blur-sm"
          onClick={onClose}
        />

        {/* Modal */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="relative z-10 w-full max-w-md mx-4 bg-gray-800 rounded-2xl shadow-2xl border border-gray-700"
        >
          {/* Close button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-gray-400 hover:text-white transition"
          >
            <X className="h-5 w-5" />
          </button>

          {/* Content */}
          <div className="p-6">
            {/* Warning icon */}
            <div className="flex justify-center mb-4">
              <div className="p-3 bg-red-500/20 rounded-full">
                <AlertTriangle className="h-8 w-8 text-red-400" />
              </div>
            </div>

            {/* Title */}
            <h3 className="text-xl font-bold text-white text-center mb-2">
              {title}
            </h3>

            {/* Message */}
            <p className="text-gray-400 text-center mb-2">
              {message}
            </p>

            {/* Item name */}
            {itemName && (
              <p className="text-center mb-4">
                <span className="text-purple-400 font-semibold">"{itemName}"</span>
              </p>
            )}

            {/* Actions */}
            <div className="flex gap-3 mt-6">
              <button
                onClick={onClose}
                disabled={isDeleting}
                className="flex-1 px-4 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-xl font-medium transition disabled:opacity-50"
              >
                {cancelText}
              </button>
              <button
                onClick={onConfirm}
                disabled={isDeleting}
                className="flex-1 px-4 py-3 bg-red-600 hover:bg-red-700 text-white rounded-xl font-medium transition disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {isDeleting ? (
                  <>
                    <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Deleting...
                  </>
                ) : (
                  confirmText
                )}
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}

export default DeleteConfirmationModal;
