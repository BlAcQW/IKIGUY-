/**
 * ConfirmDialog Component
 *
 * A polished, modern confirmation dialog with smooth animations,
 * clear visual hierarchy, and variant-specific styling.
 */

import { useEffect, useRef, useState } from 'react';
import {
  AlertTriangle,
  Trash2,
  CheckCircle,
  Info,
  X,
  Loader2,
  ShieldAlert,
} from 'lucide-react';

export type DialogVariant = 'danger' | 'warning' | 'info' | 'success';

export interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void | Promise<void>;
  title: string;
  message: string | React.ReactNode;
  /** Additional description text below the main message */
  description?: string;
  confirmText?: string;
  cancelText?: string;
  variant?: DialogVariant;
  isLoading?: boolean;
  /** Item name to display prominently (e.g., conference name) */
  itemName?: string;
  /** Show a destructive warning badge */
  showDestructiveWarning?: boolean;
}

const variantConfig: Record<DialogVariant, {
  icon: React.ReactNode;
  iconBg: string;
  iconColor: string;
  iconRing: string;
  confirmBg: string;
  confirmHover: string;
  confirmActive: string;
  focusRing: string;
  itemBg: string;
  itemBorder: string;
  itemText: string;
  gradient: string;
}> = {
  danger: {
    icon: <Trash2 className="w-7 h-7" />,
    iconBg: 'bg-red-100',
    iconColor: 'text-red-600',
    iconRing: 'ring-red-600/20',
    confirmBg: 'bg-red-600',
    confirmHover: 'hover:bg-red-700',
    confirmActive: 'active:bg-red-800',
    focusRing: 'focus-visible:ring-red-500',
    itemBg: 'bg-red-50',
    itemBorder: 'border-red-200',
    itemText: 'text-red-800',
    gradient: 'from-red-500 to-rose-600',
  },
  warning: {
    icon: <AlertTriangle className="w-7 h-7" />,
    iconBg: 'bg-amber-100',
    iconColor: 'text-amber-600',
    iconRing: 'ring-amber-600/20',
    confirmBg: 'bg-amber-600',
    confirmHover: 'hover:bg-amber-700',
    confirmActive: 'active:bg-amber-800',
    focusRing: 'focus-visible:ring-amber-500',
    itemBg: 'bg-amber-50',
    itemBorder: 'border-amber-200',
    itemText: 'text-amber-800',
    gradient: 'from-amber-500 to-orange-600',
  },
  info: {
    icon: <Info className="w-7 h-7" />,
    iconBg: 'bg-blue-100',
    iconColor: 'text-blue-600',
    iconRing: 'ring-blue-600/20',
    confirmBg: 'bg-blue-600',
    confirmHover: 'hover:bg-blue-700',
    confirmActive: 'active:bg-blue-800',
    focusRing: 'focus-visible:ring-blue-500',
    itemBg: 'bg-blue-50',
    itemBorder: 'border-blue-200',
    itemText: 'text-blue-800',
    gradient: 'from-blue-500 to-indigo-600',
  },
  success: {
    icon: <CheckCircle className="w-7 h-7" />,
    iconBg: 'bg-green-100',
    iconColor: 'text-green-600',
    iconRing: 'ring-green-600/20',
    confirmBg: 'bg-green-600',
    confirmHover: 'hover:bg-green-700',
    confirmActive: 'active:bg-green-800',
    focusRing: 'focus-visible:ring-green-500',
    itemBg: 'bg-green-50',
    itemBorder: 'border-green-200',
    itemText: 'text-green-800',
    gradient: 'from-green-500 to-emerald-600',
  },
};

export default function ConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  description,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'danger',
  isLoading = false,
  itemName,
  showDestructiveWarning = false,
}: ConfirmDialogProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const confirmButtonRef = useRef<HTMLButtonElement>(null);
  const config = variantConfig[variant];

  // Focus trap and keyboard handling
  useEffect(() => {
    if (isOpen) {
      // Focus confirm button when dialog opens
      setTimeout(() => confirmButtonRef.current?.focus(), 100);

      // Handle escape key
      const handleEscape = (e: KeyboardEvent) => {
        if (e.key === 'Escape' && !isLoading) {
          onClose();
        }
      };

      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';

      return () => {
        document.removeEventListener('keydown', handleEscape);
        document.body.style.overflow = 'unset';
      };
    }
  }, [isOpen, onClose, isLoading]);

  // Handle backdrop click
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget && !isLoading) {
      onClose();
    }
  };

  // Handle confirm with loading
  const handleConfirm = async () => {
    await onConfirm();
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-[70] flex items-center justify-center p-4"
      onClick={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby="dialog-title"
    >
      {/* Backdrop with blur */}
      <div className="absolute inset-0 bg-gray-900/60 backdrop-blur-sm transition-opacity duration-200" />

      {/* Dialog */}
      <div
        ref={dialogRef}
        className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden transform transition-all duration-200 scale-100"
        style={{
          animation: 'dialogEnter 0.2s ease-out',
        }}
      >
        {/* Top gradient accent bar */}
        <div className={`h-1.5 bg-gradient-to-r ${config.gradient}`} />

        {/* Close button */}
        <button
          onClick={onClose}
          disabled={isLoading}
          className="absolute top-4 right-4 p-1.5 rounded-full text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label="Close dialog"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Content */}
        <div className="px-6 pt-6 pb-4">
          {/* Icon with ring effect */}
          <div className="flex justify-center mb-5">
            <div className={`relative`}>
              <div className={`w-16 h-16 ${config.iconBg} rounded-full flex items-center justify-center ring-8 ${config.iconRing}`}>
                <span className={config.iconColor}>{config.icon}</span>
              </div>
              {/* Pulse animation for danger */}
              {variant === 'danger' && (
                <div className="absolute inset-0 rounded-full bg-red-400 animate-ping opacity-20" />
              )}
            </div>
          </div>

          {/* Title */}
          <h2
            id="dialog-title"
            className="text-xl font-bold text-gray-900 text-center mb-3"
          >
            {title}
          </h2>

          {/* Message */}
          <div className="text-center space-y-3">
            <p className="text-gray-600 leading-relaxed">
              {typeof message === 'string' ? message : message}
            </p>

            {/* Item name display */}
            {itemName && (
              <div className={`inline-block px-4 py-2.5 ${config.itemBg} border ${config.itemBorder} rounded-lg`}>
                <p className={`font-semibold ${config.itemText} text-sm`}>
                  {itemName}
                </p>
              </div>
            )}

            {/* Additional description */}
            {description && (
              <p className="text-sm text-gray-500">
                {description}
              </p>
            )}

            {/* Destructive warning */}
            {showDestructiveWarning && variant === 'danger' && (
              <div className="flex items-center justify-center gap-2 text-xs text-red-600 bg-red-50 rounded-lg py-2 px-3 mt-3">
                <ShieldAlert className="w-4 h-4 flex-shrink-0" />
                <span>This action cannot be undone</span>
              </div>
            )}
          </div>
        </div>

        {/* Actions - separated with subtle border */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-100 flex gap-3">
          {cancelText && (
            <button
              onClick={onClose}
              disabled={isLoading}
              className="flex-1 px-4 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 hover:border-gray-400 focus:outline-none focus-visible:ring-2 focus-visible:ring-gray-500 focus-visible:ring-offset-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {cancelText}
            </button>
          )}
          <button
            ref={confirmButtonRef}
            onClick={handleConfirm}
            disabled={isLoading}
            className={`flex-1 px-4 py-2.5 text-sm font-medium text-white ${config.confirmBg} ${config.confirmHover} ${config.confirmActive} rounded-lg focus:outline-none focus-visible:ring-2 ${config.focusRing} focus-visible:ring-offset-2 transition-all disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-2`}
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Processing...</span>
              </>
            ) : (
              confirmText
            )}
          </button>
        </div>
      </div>

      {/* Custom animation keyframes */}
      <style>{`
        @keyframes dialogEnter {
          from {
            opacity: 0;
            transform: scale(0.95) translateY(-10px);
          }
          to {
            opacity: 1;
            transform: scale(1) translateY(0);
          }
        }
      `}</style>
    </div>
  );
}

/**
 * Hook for managing confirm dialog state
 */
export function useConfirmDialog() {
  const [dialogState, setDialogState] = useState<{
    isOpen: boolean;
    props: Omit<ConfirmDialogProps, 'isOpen' | 'onClose' | 'onConfirm'>;
    resolver: ((value: boolean) => void) | null;
  }>({
    isOpen: false,
    props: { title: '', message: '' },
    resolver: null,
  });

  const confirm = (props: Omit<ConfirmDialogProps, 'isOpen' | 'onClose' | 'onConfirm'>): Promise<boolean> => {
    return new Promise((resolve) => {
      setDialogState({
        isOpen: true,
        props,
        resolver: resolve,
      });
    });
  };

  const handleClose = () => {
    dialogState.resolver?.(false);
    setDialogState((prev) => ({ ...prev, isOpen: false, resolver: null }));
  };

  const handleConfirm = () => {
    dialogState.resolver?.(true);
    setDialogState((prev) => ({ ...prev, isOpen: false, resolver: null }));
  };

  const DialogComponent = () => (
    <ConfirmDialog
      isOpen={dialogState.isOpen}
      onClose={handleClose}
      onConfirm={handleConfirm}
      {...dialogState.props}
    />
  );

  return { confirm, DialogComponent };
}
