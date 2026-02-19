/**
 * AudioPlayer Component
 * Simplified 3-button circular audio player controls
 */

import { Play, Pause, RotateCcw, RotateCw } from 'lucide-react';
import { motion } from 'framer-motion';

interface AudioPlayerProps {
  isPlaying: boolean;
  isLoading: boolean;
  onTogglePlay: () => void;
  onSkipForward: () => void;
  onSkipBackward: () => void;
  playbackRate?: number;
  onChangePlaybackRate?: (rate: number) => void;
}

const PLAYBACK_RATES = [0.5, 0.75, 1, 1.25, 1.5, 1.75, 2];

export default function AudioPlayer({
  isPlaying,
  isLoading,
  onTogglePlay,
  onSkipForward,
  onSkipBackward,
  playbackRate = 1,
  onChangePlaybackRate,
}: AudioPlayerProps) {
  const cyclePlaybackRate = () => {
    if (onChangePlaybackRate) {
      const currentIndex = PLAYBACK_RATES.indexOf(playbackRate);
      const nextIndex = (currentIndex + 1) % PLAYBACK_RATES.length;
      onChangePlaybackRate(PLAYBACK_RATES[nextIndex]);
    }
  };

  return (
    <div className="w-full flex flex-col items-center gap-6">
      {/* Main Playback Controls - 3 Button Layout */}
      <div className="flex items-center justify-center gap-4">
        {/* Skip Backward 15s */}
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={onSkipBackward}
          disabled={isLoading}
          className="relative w-16 h-16 rounded-full bg-gray-800/80 hover:bg-gray-700 border border-gray-700 text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center group"
          aria-label="Skip backward 15 seconds"
        >
          <div className="flex flex-col items-center justify-center">
            <RotateCcw className="h-5 w-5 mb-[-2px]" />
            <span className="text-[10px] font-bold">15</span>
          </div>
        </motion.button>

        {/* Play/Pause - Large Central Button */}
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={onTogglePlay}
          disabled={isLoading}
          className="relative w-20 h-20 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white shadow-2xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          aria-label={isPlaying ? 'Pause' : 'Play'}
        >
          {isLoading ? (
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-white border-t-transparent"></div>
          ) : isPlaying ? (
            <Pause className="h-8 w-8 fill-white" />
          ) : (
            <Play className="h-8 w-8 fill-white ml-1" />
          )}
        </motion.button>

        {/* Skip Forward 15s */}
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={onSkipForward}
          disabled={isLoading}
          className="relative w-16 h-16 rounded-full bg-gray-800/80 hover:bg-gray-700 border border-gray-700 text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center group"
          aria-label="Skip forward 15 seconds"
        >
          <div className="flex flex-col items-center justify-center">
            <RotateCw className="h-5 w-5 mb-[-2px]" />
            <span className="text-[10px] font-bold">15</span>
          </div>
        </motion.button>
      </div>

      {/* Secondary Controls - Playback Speed */}
      {onChangePlaybackRate && (
        <button
          onClick={cyclePlaybackRate}
          className="px-4 py-2 bg-gray-800/60 hover:bg-gray-700/80 rounded-full text-gray-300 hover:text-white transition text-sm font-semibold border border-gray-700"
          aria-label={`Playback speed: ${playbackRate}x`}
        >
          {playbackRate}x Speed
        </button>
      )}
    </div>
  );
}
