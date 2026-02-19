/**
 * Enhanced Delete Confirmation Modal Component
 * 
 * A comprehensive, reusable deletion confirmation dialog with:
 * - Multiple variants (destructive, warning, info)
 * - Customizable warnings and consequences
 * - Loading states and animations
 * - Accessibility features
 * - Keyboard navigation
 * - Type safety
 * 
 * Usage:
 * ```tsx
 * <DeleteConfirmationModal
 *   isOpen={showDelete}
 *   onClose={() => setShowDelete(false)}
 *   onConfirm={handleDelete}
 *   itemName="My Book"
 *   itemType="book"
 *   consequences={[
 *     "All associated data will be permanently deleted",
 *     "This action cannot be undone"
 *   ]}
 *   variant="destructive"
 *   isDeleting={isDeleting}
 * />
 * ```
 */

import React, { useEffect, useRef } from 'react';
import { AlertTriangle, Trash2, X, Loader2 } from 'lucide-react';

export type DeleteVariant = 'destructive' | 'warning' | 'info';

export interface DeleteConfirmationModalProps {
  /** Whether the modal is open */
  isOpen: boolean;
  /** Callback when modal should close */
  onClose: () => void;
  /** Callback when deletion is confirmed */
  onConfirm: () => void | Promise<void>;
  /** Name of the item being deleted (e.g., "My Book") */
  itemName?: string;
  /** Type of item being deleted (e.g., "book", "organization", "user") */
  itemType?: string;
  /** Custom title (defaults to "Delete {itemType}" or "Confirm Deletion") */
  title?: string;
  /** Custom message (defaults to generated message) */
  message?: string;
  /** List of consequences/warnings to display */
  consequences?: string[];
  /** Variant style: destructive (red), warning (orange), info (blue) */
  variant?: DeleteVariant;
  /** Whether deletion is in progress */
  isDeleting?: boolean;
  /** Custom confirm button text */
  confirmText?: string;
  /** Custom cancel button text */
  cancelText?: string;
  /** Whether to require typing item name to confirm (for critical deletions) */
  requireTypeToConfirm?: boolean;
  /** Text that must be typed to confirm (usually item name) */
  typeToConfirmText?: string;
  /** Additional warning message */
  warningMessage?: string;
  /** Custom className for the modal */
  className?: string;
  /** Whether to show icon */
  showIcon?: boolean;
  /** Size of the modal: sm, md, lg */
  size?: 'sm' | 'md' | 'lg';
}

const variantStyles = {
  destructive: {
    iconBg: 'bg-red-100',
    iconColor: 'text-red-600',
    buttonBg: 'bg-red-600',
    buttonHover: 'hover:bg-red-700',
    buttonFocus: 'focus:ring-red-500',
    borderColor: 'border-red-200',
    bgColor: 'bg-red-50',
    textColor: 'text-red-900',
    textSecondary: 'text-red-700',
  },
  warning: {
    iconBg: 'bg-orange-100',
    iconColor: 'text-orange-600',
    buttonBg: 'bg-orange-600',
    buttonHover: 'hover:bg-orange-700',
    buttonFocus: 'focus:ring-orange-500',
    borderColor: 'border-orange-200',
    bgColor: 'bg-orange-50',
    textColor: 'text-orange-900',
    textSecondary: 'text-orange-700',
  },
  info: {
    iconBg: 'bg-blue-100',
    iconColor: 'text-blue-600',
    buttonBg: 'bg-blue-600',
    buttonHover: 'hover:bg-blue-700',
    buttonFocus: 'focus:ring-blue-500',
    borderColor: 'border-blue-200',
    bgColor: 'bg-blue-50',
    textColor: 'text-blue-900',
    textSecondary: 'text-blue-700',
  },
};

const sizeStyles = {
  sm: 'sm:max-w-md',
  md: 'sm:max-w-lg',
  lg: 'sm:max-w-2xl',
};

export const DeleteConfirmationModal: React.FC<DeleteConfirmationModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  itemName,
  itemType = 'item',
  title,
  message,
  consequences = [],
  variant = 'destructive',
  isDeleting = false,
  confirmText = 'Delete',
  cancelText = 'Cancel',
  requireTypeToConfirm = false,
  typeToConfirmText,
  warningMessage,
  className = '',
  showIcon = true,
  size = 'md',
}) => {
  const [typedText, setTypedText] = React.useState('');
  const [isConfirming, setIsConfirming] = React.useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const cancelButtonRef = useRef<HTMLButtonElement>(null);

  const styles = variantStyles[variant];
  const sizeClass = sizeStyles[size];

  // Generate default title
  const defaultTitle = title || (itemType ? `Delete ${itemType.charAt(0).toUpperCase() + itemType.slice(1)}` : 'Confirm Deletion');

  // Generate default message
  const defaultMessage = message || (
    itemName
      ? `Are you sure you want to delete "${itemName}"?`
      : `Are you sure you want to delete this ${itemType}?`
  );

  // Check if typed text matches required confirmation text
  const canConfirm = requireTypeToConfirm
    ? typedText === (typeToConfirmText || itemName)
    : true;

  // Handle ESC key and focus management
  useEffect(() => {
    if (!isOpen) return;

    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isDeleting && !isConfirming) {
        onClose();
      }
    };

    // Focus management
    if (requireTypeToConfirm && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 100);
    } else if (cancelButtonRef.current) {
      setTimeout(() => cancelButtonRef.current?.focus(), 100);
    }

    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [isOpen, isDeleting, isConfirming, onClose, requireTypeToConfirm]);

  // Reset typed text when modal closes
  useEffect(() => {
    if (!isOpen) {
      setTypedText('');
      setIsConfirming(false);
    }
  }, [isOpen]);

  // Handle confirm action
  const handleConfirm = async () => {
    if (!canConfirm || isDeleting || isConfirming) return;

    setIsConfirming(true);
    try {
      await onConfirm();
      // Don't close here - let parent handle it after successful deletion
    } catch (error) {
      console.error('Delete confirmation error:', error);
      // Keep modal open on error so user can retry
    } finally {
      setIsConfirming(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto"
      aria-labelledby="delete-modal-title"
      role="dialog"
      aria-modal="true"
      onClick={(e) => {
        // Close on backdrop click (but not when clicking inside modal)
        if (e.target === e.currentTarget && !isDeleting && !isConfirming) {
          onClose();
        }
      }}
    >
      {/* Backdrop with animation */}
      <div
        className="fixed inset-0 bg-gray-900 bg-opacity-50 transition-opacity"
        aria-hidden="true"
      />

      {/* Modal Container */}
      <div className="flex min-h-full items-center justify-center p-4 text-center sm:p-0">
        <div
          className={`
            relative transform overflow-hidden rounded-lg bg-white text-left shadow-xl 
            transition-all sm:my-8 sm:w-full ${sizeClass}
            ${className}
          `}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="bg-white px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
            <div className="sm:flex sm:items-start">
              {/* Icon */}
              {showIcon && (
                <div
                  className={`
                    mx-auto flex h-12 w-12 flex-shrink-0 items-center justify-center 
                    rounded-full ${styles.iconBg} sm:mx-0 sm:h-10 sm:w-10
                  `}
                >
                  {variant === 'destructive' ? (
                    <Trash2 className={`h-6 w-6 ${styles.iconColor}`} aria-hidden="true" />
                  ) : (
                    <AlertTriangle className={`h-6 w-6 ${styles.iconColor}`} aria-hidden="true" />
                  )}
                </div>
              )}

              {/* Content */}
              <div className={`mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left flex-1 ${!showIcon ? 'sm:ml-0' : ''}`}>
                <h3
                  className="text-lg font-semibold leading-6 text-gray-900"
                  id="delete-modal-title"
                >
                  {defaultTitle}
                </h3>
                <div className="mt-2">
                  <p className="text-sm text-gray-500">{defaultMessage}</p>
                </div>

                {/* Warning Message */}
                {warningMessage && (
                  <div className={`mt-3 p-3 rounded-md ${styles.bgColor} border ${styles.borderColor}`}>
                    <p className={`text-sm font-medium ${styles.textColor}`}>
                      {warningMessage}
                    </p>
                  </div>
                )}

                {/* Consequences List */}
                {consequences.length > 0 && (
                  <div className={`mt-3 p-3 rounded-md ${styles.bgColor} border ${styles.borderColor}`}>
                    <p className={`text-xs font-semibold ${styles.textColor} mb-2`}>
                      This will:
                    </p>
                    <ul className={`text-xs ${styles.textSecondary} space-y-1 list-disc list-inside`}>
                      {consequences.map((consequence, index) => (
                        <li key={index}>{consequence}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Type to Confirm Input */}
                {requireTypeToConfirm && (
                  <div className="mt-4">
                    <label
                      htmlFor="confirm-input"
                      className="block text-sm font-medium text-gray-700 mb-2"
                    >
                      Type <span className="font-mono font-semibold">{typeToConfirmText || itemName}</span> to confirm:
                    </label>
                    <input
                      ref={inputRef}
                      id="confirm-input"
                      type="text"
                      value={typedText}
                      onChange={(e) => setTypedText(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && canConfirm && !isDeleting && !isConfirming) {
                          handleConfirm();
                        }
                      }}
                      disabled={isDeleting || isConfirming}
                      className={`
                        w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm
                        focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500
                        disabled:bg-gray-100 disabled:cursor-not-allowed
                        ${typedText === (typeToConfirmText || itemName) ? 'border-green-500' : ''}
                      `}
                      placeholder={typeToConfirmText || itemName}
                    />
                  </div>
                )}
              </div>

              {/* Close Button */}
              <button
                type="button"
                onClick={onClose}
                disabled={isDeleting || isConfirming}
                className="absolute top-4 right-4 text-gray-400 hover:text-gray-500 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed"
                aria-label="Close"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          </div>

          {/* Actions */}
          <div className="bg-gray-50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6 gap-3">
            <button
              type="button"
              onClick={handleConfirm}
              disabled={!canConfirm || isDeleting || isConfirming}
              className={`
                inline-flex w-full justify-center items-center rounded-md px-4 py-2 text-sm 
                font-semibold text-white shadow-sm 
                ${styles.buttonBg} ${styles.buttonHover}
                focus:outline-none focus:ring-2 focus:ring-offset-2 ${styles.buttonFocus}
                sm:ml-3 sm:w-auto
                disabled:opacity-50 disabled:cursor-not-allowed
                transition-colors
              `}
            >
              {isDeleting || isConfirming ? (
                <>
                  <Loader2 className="animate-spin -ml-1 mr-2 h-4 w-4" />
                  Deleting...
                </>
              ) : (
                confirmText
              )}
            </button>
            <button
              ref={cancelButtonRef}
              type="button"
              onClick={onClose}
              disabled={isDeleting || isConfirming}
              className="
                mt-3 inline-flex w-full justify-center rounded-md bg-white px-4 py-2 text-sm 
                font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 
                hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 
                sm:mt-0 sm:w-auto
                disabled:opacity-50 disabled:cursor-not-allowed
                transition-colors
              "
            >
              {cancelText}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DeleteConfirmationModal;

