/**
 * BookProgressBar Component
 *
 * Book-level progress bar showing overall reading progress.
 * Allows seeking across the entire audiobook.
 */

import { useState, useRef } from 'react';
import { motion } from 'framer-motion';

interface BookProgressBarProps {
  progress: number; // 0.0 to 1.0
  totalDuration: number; // seconds
  currentTime: number; // seconds
  onSeek: (progress: number) => void;
}

export default function BookProgressBar({
  progress,
  totalDuration,
  currentTime,
  onSeek,
}: BookProgressBarProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [hoverProgress, setHoverProgress] = useState<number | null>(null);
  const barRef = useRef<HTMLDivElement>(null);

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    updateProgress(e);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!barRef.current) return;

    const rect = barRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = Math.max(0, Math.min(1, x / rect.width));
    setHoverProgress(percentage);

    if (isDragging) {
      updateProgress(e);
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleMouseLeave = () => {
    setIsDragging(false);
    setHoverProgress(null);
  };

  const updateProgress = (e: React.MouseEvent) => {
    if (!barRef.current) return;

    const rect = barRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = Math.max(0, Math.min(1, x / rect.width));
    onSeek(percentage);
  };

  const formatTime = (seconds: number): string => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hrs > 0) {
      return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const remainingTime = totalDuration - currentTime;
  const progressPercentage = Math.round(progress * 100);

  return (
    <div className="w-full mb-4">
      {/* Time Display */}
      <div className="flex justify-between items-center mb-2 text-sm">
        <span className="text-white font-medium">
          {formatTime(currentTime)}
        </span>
        <span className="text-purple-400 font-semibold">
          {progressPercentage}% complete
        </span>
        <span className="text-gray-400">
          -{formatTime(remainingTime)}
        </span>
      </div>

      {/* Progress Bar */}
      <div
        ref={barRef}
        className="relative h-3 bg-gray-700 rounded-full cursor-pointer overflow-hidden"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseLeave}
      >
        {/* Progress Fill */}
        <motion.div
          className="absolute h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"
          style={{ width: `${progress * 100}%` }}
          animate={{ width: `${progress * 100}%` }}
          transition={{ duration: 0.1 }}
        />

        {/* Hover Preview */}
        {hoverProgress !== null && hoverProgress !== progress && (
          <div
            className="absolute h-full bg-white/20 rounded-full pointer-events-none"
            style={{
              left: `${Math.min(progress, hoverProgress) * 100}%`,
              width: `${Math.abs(hoverProgress - progress) * 100}%`,
            }}
          />
        )}

        {/* Seek Handle */}
        <motion.div
          className="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-white rounded-full shadow-lg border-2 border-purple-500"
          style={{ left: `calc(${progress * 100}% - 8px)` }}
          whileHover={{ scale: 1.2 }}
          whileDrag={{ scale: 1.3 }}
        />

        {/* Hover Time Tooltip */}
        {hoverProgress !== null && (
          <div
            className="absolute -top-8 transform -translate-x-1/2 bg-gray-800 text-white text-xs px-2 py-1 rounded pointer-events-none whitespace-nowrap"
            style={{ left: `${hoverProgress * 100}%` }}
          >
            {formatTime(hoverProgress * totalDuration)}
          </div>
        )}
      </div>

      {/* Total Duration Label */}
      <div className="flex justify-center mt-1">
        <span className="text-[10px] text-gray-500">
          Total: {formatTime(totalDuration)}
        </span>
      </div>
    </div>
  );
}
