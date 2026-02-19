/**
 * BookVisibilityModal Component
 *
 * Modal for changing book visibility status with visual explanations.
 * Allows authors to toggle between draft, private, unlisted, and public states.
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  FileText,
  Lock,
  Link2,
  Globe,
  Eye,
  EyeOff,
  Users,
  CheckCircle,
} from 'lucide-react';
import toast from 'react-hot-toast';
import type { BookVisibility } from '../types/book';

interface BookVisibilityModalProps {
  isOpen: boolean;
  onClose: () => void;
  book: {
    id: string;
    title: string;
    visibility?: string;
  };
  onVisibilityChange: (bookId: string, visibility: BookVisibility) => Promise<void>;
}

interface VisibilityOption {
  value: BookVisibility;
  label: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  badgeColor: string;
  features: string[];
}

const visibilityOptions: VisibilityOption[] = [
  {
    value: 'draft',
    label: 'Draft',
    description: 'Work in progress, only you can see this book',
    icon: FileText,
    color: 'yellow',
    badgeColor: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    features: [
      'Visible only to you',
      'Not in All Books',
      'Not searchable',
      'Perfect for incomplete books',
    ],
  },
  {
    value: 'private',
    label: 'Private',
    description: 'Invitation only, not discoverable',
    icon: Lock,
    color: 'red',
    badgeColor: 'bg-red-500/20 text-red-400 border-red-500/30',
    features: [
      'Only invited users can access',
      'Not in All Books',
      'Not searchable',
      'Share via invitation links',
    ],
  },
  {
    value: 'unlisted',
    label: 'Unlisted',
    description: 'Anyone with the link can access, not in discovery',
    icon: Link2,
    color: 'blue',
    badgeColor: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    features: [
      'Anyone with link can access',
      'Not in All Books',
      'Not searchable',
      'Good for selective sharing',
    ],
  },
  {
    value: 'public',
    label: 'Public',
    description: 'Visible in All Books, fully discoverable',
    icon: Globe,
    color: 'green',
    badgeColor: 'bg-green-500/20 text-green-400 border-green-500/30',
    features: [
      'Visible to everyone',
      'Appears in All Books',
      'Searchable',
      'Maximum reach',
    ],
  },
];

export default function BookVisibilityModal({
  isOpen,
  onClose,
  book,
  onVisibilityChange,
}: BookVisibilityModalProps) {
  const [selectedVisibility, setSelectedVisibility] = useState<BookVisibility>(
    (book.visibility as BookVisibility) || 'private'
  );
  const [saving, setSaving] = useState(false);

  const currentOption = visibilityOptions.find(
    (opt) => opt.value === selectedVisibility
  );

  const handleSave = async () => {
    if (selectedVisibility === book.visibility) {
      onClose();
      return;
    }

    setSaving(true);
    try {
      await onVisibilityChange(book.id, selectedVisibility);
      onClose();
    } catch (error) {
      // Error already handled by parent
    } finally {
      setSaving(false);
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
          className="bg-gray-800 border border-gray-700 rounded-xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <Eye className="w-6 h-6 text-purple-400" />
                Change Book Visibility
              </h2>
              <p className="text-sm text-gray-400 mt-1">{book.title}</p>
            </div>
            <button
              onClick={onClose}
              className="p-1 hover:bg-gray-700 rounded transition-colors"
            >
              <X className="w-5 h-5 text-gray-400" />
            </button>
          </div>

          {/* Visibility Options */}
          <div className="space-y-3 mb-6">
            {visibilityOptions.map((option) => {
              const Icon = option.icon;
              const isSelected = selectedVisibility === option.value;
              const isCurrent = book.visibility === option.value;

              return (
                <button
                  key={option.value}
                  onClick={() => setSelectedVisibility(option.value)}
                  className={`w-full p-4 rounded-lg border-2 transition-all text-left ${
                    isSelected
                      ? `border-${option.color}-500 bg-${option.color}-500/10`
                      : 'border-gray-700 hover:border-gray-600 bg-gray-900/50'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div
                      className={`p-2 rounded-lg ${
                        isSelected
                          ? option.badgeColor
                          : 'bg-gray-700/50 text-gray-400'
                      }`}
                    >
                      <Icon className="w-5 h-5" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="text-white font-semibold">
                          {option.label}
                        </h3>
                        {isCurrent && (
                          <span className="text-xs px-2 py-0.5 bg-gray-700 text-gray-300 rounded-full">
                            Current
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-400 mb-3">
                        {option.description}
                      </p>
                      <ul className="space-y-1">
                        {option.features.map((feature, idx) => (
                          <li
                            key={idx}
                            className="text-xs text-gray-500 flex items-center gap-1.5"
                          >
                            <CheckCircle className="w-3 h-3 text-gray-600" />
                            {feature}
                          </li>
                        ))}
                      </ul>
                    </div>
                    {isSelected && (
                      <div className={`text-${option.color}-400`}>
                        <CheckCircle className="w-6 h-6" />
                      </div>
                    )}
                  </div>
                </button>
              );
            })}
          </div>

          {/* Selected Option Summary */}
          {currentOption && (
            <div className="mb-6 p-4 bg-gray-900/50 border border-gray-700 rounded-lg">
              <div className="flex items-start gap-3">
                <div className={`p-2 rounded-lg ${currentOption.badgeColor}`}>
                  <currentOption.icon className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <h4 className="text-white font-semibold mb-1">
                    Selected: {currentOption.label}
                  </h4>
                  <p className="text-sm text-gray-400">
                    {currentOption.description}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3">
            <button
              onClick={onClose}
              disabled={saving}
              className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving || selectedVisibility === book.visibility}
              className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
