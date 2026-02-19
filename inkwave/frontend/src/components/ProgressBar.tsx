/**
 * ProgressBar Component
 * Custom audio progress bar with seek functionality
 */

import { useRef, useState } from 'react';
import { motion } from 'framer-motion';

interface ProgressBarProps {
  currentTime: number;
  duration: number;
  onSeek: (time: number) => void;
  className?: string;
}

export default function ProgressBar({
  currentTime,
  duration,
  onSeek,
  className = '',
}: ProgressBarProps) {
  const progressRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [hoverTime, setHoverTime] = useState<number | null>(null);

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

  const formatTime = (seconds: number) => {
    if (isNaN(seconds) || !isFinite(seconds)) return '0:00';
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hours > 0) {
      return `${hours}:${mins.toString().padStart(2, '0')}:${secs
        .toString()
        .padStart(2, '0')}`;
    }
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleSeek = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!progressRef.current || duration === 0) return;

    const rect = progressRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = Math.max(0, Math.min(1, x / rect.width));
    const time = percentage * duration;

    onSeek(time);
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!progressRef.current || duration === 0) return;

    const rect = progressRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = Math.max(0, Math.min(1, x / rect.width));
    const time = percentage * duration;

    setHoverTime(time);
  };

  const handleMouseLeave = () => {
    setHoverTime(null);
  };

  // Calculate remaining time
  const remainingTime = duration - currentTime;
  const percentProgress = Math.round(progress);

  return (
    <div className={`space-y-3 ${className}`}>
      {/* Time Display - Top */}
      <div className="flex items-center justify-between text-sm font-medium">
        <span className="text-white">{formatTime(currentTime)}</span>
        <span className="text-purple-400 font-semibold">{percentProgress}%</span>
        <span className="text-white">-{formatTime(remainingTime)}</span>
      </div>

      {/* Progress Bar */}
      <div
        ref={progressRef}
        className="relative h-2 bg-gray-700 rounded-full cursor-pointer group"
        onClick={handleSeek}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        onMouseDown={() => setIsDragging(true)}
        onMouseUp={() => setIsDragging(false)}
      >
        {/* Filled Progress */}
        <motion.div
          className="absolute top-0 left-0 h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"
          style={{ width: `${progress}%` }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.1 }}
        />

        {/* Playhead */}
        <motion.div
          className="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-white rounded-full shadow-lg opacity-0 group-hover:opacity-100 transition-opacity"
          style={{ left: `${progress}%` }}
          animate={{ left: `${progress}%` }}
          transition={{ duration: 0.1 }}
        />

        {/* Hover Time Tooltip */}
        {hoverTime !== null && (
          <div
            className="absolute bottom-full mb-2 px-2 py-1 bg-gray-800 text-white text-xs rounded shadow-lg pointer-events-none"
            style={{
              left: `${(hoverTime / duration) * 100}%`,
              transform: 'translateX(-50%)',
            }}
          >
            {formatTime(hoverTime)}
          </div>
        )}
      </div>
    </div>
  );
}
