/**
 * SleepTimer Component
 * Libby-inspired sleep timer for audiobook playback
 * Features: preset times, end-of-chapter option, custom duration
 */

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Moon, X, Clock, ChevronRight } from 'lucide-react';
import toast from 'react-hot-toast';

interface SleepTimerProps {
  isPlaying: boolean;
  onPause: () => void;
  currentTime: number;
  duration: number;
  chapterEndTime?: number; // Time when current chapter ends
  onTimerSet?: (minutes: number | 'end-of-chapter') => void;
  onTimerCancel?: () => void;
}

// Preset timer options in minutes
const PRESET_OPTIONS = [5, 10, 15, 30, 45, 60];

export default function SleepTimer({
  isPlaying,
  onPause,
  currentTime,
  duration,
  chapterEndTime,
  onTimerSet,
  onTimerCancel,
}: SleepTimerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTimer, setActiveTimer] = useState<number | null>(null); // seconds remaining
  const [timerMode, setTimerMode] = useState<'preset' | 'end-of-chapter' | null>(null);
  const [customMinutes, setCustomMinutes] = useState(30);

  // Timer countdown effect
  useEffect(() => {
    if (activeTimer === null || !isPlaying) return;

    const interval = setInterval(() => {
      setActiveTimer((prev) => {
        if (prev === null) return null;
        if (prev <= 1) {
          // Timer expired - pause playback
          onPause();
          toast.success('Sleep timer ended. Sweet dreams! 🌙', {
            duration: 4000,
            icon: '😴',
          });
          onTimerCancel?.();
          return null;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [activeTimer, isPlaying, onPause, onTimerCancel]);

  // End-of-chapter timer effect
  useEffect(() => {
    if (timerMode !== 'end-of-chapter' || !chapterEndTime || !isPlaying) return;

    if (currentTime >= chapterEndTime) {
      onPause();
      toast.success('Chapter complete. Sleep timer activated! 🌙', {
        duration: 4000,
        icon: '📖',
      });
      setTimerMode(null);
      onTimerCancel?.();
    }
  }, [currentTime, chapterEndTime, timerMode, isPlaying, onPause, onTimerCancel]);

  const handleSetTimer = useCallback((minutes: number) => {
    setActiveTimer(minutes * 60);
    setTimerMode('preset');
    setIsOpen(false);
    onTimerSet?.(minutes);
    toast.success(`Sleep timer set for ${minutes} minutes`, {
      icon: '🌙',
    });
  }, [onTimerSet]);

  const handleEndOfChapter = useCallback(() => {
    setTimerMode('end-of-chapter');
    setActiveTimer(null);
    setIsOpen(false);
    onTimerSet?.('end-of-chapter');
    toast.success('Will pause at end of chapter', {
      icon: '📖',
    });
  }, [onTimerSet]);

  const handleCancelTimer = useCallback(() => {
    setActiveTimer(null);
    setTimerMode(null);
    onTimerCancel?.();
    toast.success('Sleep timer cancelled');
  }, [onTimerCancel]);

  const formatTimeRemaining = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    if (mins > 0) {
      return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
    return `${secs}s`;
  };

  const isTimerActive = activeTimer !== null || timerMode === 'end-of-chapter';

  return (
    <div className="relative">
      {/* Timer Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`relative p-2 backdrop-blur-md rounded-full transition-all ${
          isTimerActive
            ? 'bg-purple-500/30 text-purple-300 border border-purple-500/50'
            : 'bg-gray-800/60 text-gray-300 hover:text-white hover:bg-gray-700/80'
        }`}
        title={isTimerActive ? 'Sleep timer active' : 'Set sleep timer'}
      >
        <Moon className="h-5 w-5" />

        {/* Active timer indicator */}
        {isTimerActive && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="absolute -top-1 -right-1 w-3 h-3 bg-purple-500 rounded-full"
          >
            <motion.div
              className="absolute inset-0 bg-purple-400 rounded-full"
              animate={{ scale: [1, 1.5, 1], opacity: [1, 0, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
            />
          </motion.div>
        )}
      </button>

      {/* Timer remaining badge */}
      {activeTimer !== null && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute -bottom-8 left-1/2 -translate-x-1/2 whitespace-nowrap"
        >
          <span className="text-xs text-purple-400 bg-purple-500/20 px-2 py-1 rounded-full border border-purple-500/30">
            {formatTimeRemaining(activeTimer)}
          </span>
        </motion.div>
      )}

      {/* End of chapter badge */}
      {timerMode === 'end-of-chapter' && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute -bottom-8 left-1/2 -translate-x-1/2 whitespace-nowrap"
        >
          <span className="text-xs text-purple-400 bg-purple-500/20 px-2 py-1 rounded-full border border-purple-500/30">
            End of chapter
          </span>
        </motion.div>
      )}

      {/* Timer Modal */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40"
              onClick={() => setIsOpen(false)}
            />

            {/* Timer Panel */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              className="fixed sm:absolute bottom-4 sm:bottom-full left-4 right-4 sm:left-auto sm:right-0 sm:mb-3 w-auto sm:w-72 bg-gray-900/95 backdrop-blur-xl rounded-2xl border border-gray-700/50 shadow-2xl z-50 overflow-hidden"
            >
              {/* Header */}
              <div className="flex items-center justify-between p-4 border-b border-gray-700/50">
                <div className="flex items-center gap-2">
                  <Moon className="h-5 w-5 text-purple-400" />
                  <h3 className="font-semibold text-white">Sleep Timer</h3>
                </div>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-1 text-gray-400 hover:text-white transition-colors"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              {/* Content */}
              <div className="p-4 space-y-4">
                {/* Active Timer Status */}
                {isTimerActive && (
                  <div className="bg-purple-500/20 border border-purple-500/30 rounded-xl p-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-purple-300">Timer Active</p>
                        <p className="text-lg font-bold text-white">
                          {timerMode === 'end-of-chapter'
                            ? 'End of chapter'
                            : activeTimer !== null
                            ? formatTimeRemaining(activeTimer)
                            : ''}
                        </p>
                      </div>
                      <button
                        onClick={handleCancelTimer}
                        className="px-3 py-1.5 text-sm bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}

                {/* End of Chapter Option */}
                <button
                  onClick={handleEndOfChapter}
                  disabled={!chapterEndTime}
                  className={`w-full flex items-center justify-between p-3 rounded-xl transition-all ${
                    chapterEndTime
                      ? 'bg-gray-800/50 hover:bg-gray-800 text-white'
                      : 'bg-gray-800/20 text-gray-500 cursor-not-allowed'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-purple-500/30 to-pink-500/30 rounded-full flex items-center justify-center">
                      📖
                    </div>
                    <span className="font-medium">End of chapter</span>
                  </div>
                  <ChevronRight className="h-5 w-5 text-gray-500" />
                </button>

                {/* Preset Options */}
                <div>
                  <p className="text-xs text-gray-500 mb-2 px-1">Quick presets</p>
                  <div className="grid grid-cols-3 gap-2">
                    {PRESET_OPTIONS.map((minutes) => (
                      <button
                        key={minutes}
                        onClick={() => handleSetTimer(minutes)}
                        className="p-3 bg-gray-800/50 hover:bg-gray-800 rounded-xl text-center transition-all group"
                      >
                        <span className="text-lg font-bold text-white group-hover:text-purple-400 transition-colors">
                          {minutes}
                        </span>
                        <span className="block text-xs text-gray-500">min</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Custom Duration */}
                <div className="pt-2 border-t border-gray-700/50">
                  <p className="text-xs text-gray-500 mb-2 px-1">Custom duration</p>
                  <div className="flex items-center gap-2">
                    <input
                      type="range"
                      min="5"
                      max="120"
                      step="5"
                      value={customMinutes}
                      onChange={(e) => setCustomMinutes(parseInt(e.target.value))}
                      className="flex-1 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-purple-500"
                    />
                    <button
                      onClick={() => handleSetTimer(customMinutes)}
                      className="px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white text-sm font-medium rounded-lg transition-colors whitespace-nowrap"
                    >
                      {customMinutes} min
                    </button>
                  </div>
                </div>
              </div>

              {/* Footer tip */}
              <div className="px-4 py-3 bg-gray-800/30 border-t border-gray-700/50">
                <p className="text-xs text-gray-500 text-center">
                  💡 Tip: The timer remembers your last selection
                </p>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
