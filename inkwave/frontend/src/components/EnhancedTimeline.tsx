/**
 * EnhancedTimeline Component
 * Libby-inspired timeline with chapter markers, bookmarks, and visual progress
 */

import { useState, useRef, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Bookmark, Play } from 'lucide-react';

interface Chapter {
  id: string;
  title: string;
  startTime: number;
  endTime: number;
  order: number;
}

interface BookmarkItem {
  id: string;
  position: number; // seconds
  note?: string;
  createdAt: string;
}

interface EnhancedTimelineProps {
  currentTime: number;
  duration: number;
  chapters: Chapter[];
  bookmarks: BookmarkItem[];
  onSeek: (time: number) => void;
  onBookmarkClick?: (bookmark: BookmarkItem) => void;
  onChapterClick?: (chapter: Chapter) => void;
}

export default function EnhancedTimeline({
  currentTime,
  duration,
  chapters,
  bookmarks,
  onSeek,
  onBookmarkClick,
  onChapterClick,
}: EnhancedTimelineProps) {
  const [hoveredTime, setHoveredTime] = useState<number | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const timelineRef = useRef<HTMLDivElement>(null);

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;
  const hoverProgress = hoveredTime !== null && duration > 0
    ? (hoveredTime / duration) * 100
    : null;

  const formatTime = (seconds: number): string => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hrs > 0) {
      return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getTimeFromPosition = useCallback((clientX: number): number => {
    if (!timelineRef.current || duration === 0) return 0;

    const rect = timelineRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(clientX - rect.left, rect.width));
    const percentage = x / rect.width;
    return percentage * duration;
  }, [duration]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    const time = getTimeFromPosition(e.clientX);
    setHoveredTime(time);

    if (isDragging) {
      onSeek(time);
    }
  }, [getTimeFromPosition, isDragging, onSeek]);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    setIsDragging(true);
    const time = getTimeFromPosition(e.clientX);
    onSeek(time);
  }, [getTimeFromPosition, onSeek]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleMouseLeave = useCallback(() => {
    setHoveredTime(null);
    setIsDragging(false);
  }, []);

  // Touch event handlers for mobile support
  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    if (e.touches.length === 1) {
      setIsDragging(true);
      const time = getTimeFromPosition(e.touches[0].clientX);
      onSeek(time);
    }
  }, [getTimeFromPosition, onSeek]);

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    if (e.touches.length === 1 && isDragging) {
      const time = getTimeFromPosition(e.touches[0].clientX);
      setHoveredTime(time);
      onSeek(time);
    }
  }, [getTimeFromPosition, isDragging, onSeek]);

  const handleTouchEnd = useCallback(() => {
    setIsDragging(false);
    setHoveredTime(null);
  }, []);

  // Find current chapter
  const currentChapter = chapters.find(
    (ch) => currentTime >= ch.startTime && currentTime < ch.endTime
  );

  // Get hovered chapter
  const hoveredChapter = hoveredTime !== null
    ? chapters.find((ch) => hoveredTime >= ch.startTime && hoveredTime < ch.endTime)
    : null;

  return (
    <div className="space-y-3">
      {/* Main Timeline Container */}
      <div
        ref={timelineRef}
        className="relative h-12 cursor-pointer group touch-none"
        onMouseMove={handleMouseMove}
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseLeave}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        {/* Background Track */}
        <div className="absolute inset-x-0 top-1/2 -translate-y-1/2 h-2 bg-gray-800/70 rounded-full overflow-hidden backdrop-blur-sm">
          {/* Chapter Segments */}
          {chapters.map((chapter, idx) => {
            const startPercent = (chapter.startTime / duration) * 100;
            const widthPercent = ((chapter.endTime - chapter.startTime) / duration) * 100;
            const isCurrentChapter = chapter.id === currentChapter?.id;

            return (
              <div
                key={chapter.id}
                className={`absolute h-full transition-colors ${
                  isCurrentChapter
                    ? 'bg-purple-900/50'
                    : idx % 2 === 0
                    ? 'bg-gray-700/30'
                    : 'bg-gray-800/30'
                }`}
                style={{
                  left: `${startPercent}%`,
                  width: `${widthPercent}%`,
                }}
                onClick={(e) => {
                  e.stopPropagation();
                  onChapterClick?.(chapter);
                }}
              />
            );
          })}

          {/* Progress Fill */}
          <motion.div
            className="absolute h-full bg-gradient-to-r from-purple-500 via-pink-500 to-purple-500 rounded-full"
            style={{ width: `${progress}%` }}
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
          />

          {/* Hover Preview */}
          {hoverProgress !== null && !isDragging && (
            <div
              className="absolute h-full bg-white/20 rounded-full transition-all"
              style={{ width: `${hoverProgress}%` }}
            />
          )}
        </div>

        {/* Chapter Markers */}
        {chapters.slice(1).map((chapter) => {
          const position = (chapter.startTime / duration) * 100;
          return (
            <div
              key={`marker-${chapter.id}`}
              className="absolute top-1/2 -translate-y-1/2 w-0.5 h-4 bg-gray-500/50 group-hover:bg-purple-400/70 transition-colors"
              style={{ left: `${position}%` }}
              title={chapter.title}
            />
          );
        })}

        {/* Bookmark Markers */}
        {bookmarks.map((bookmark) => {
          const position = (bookmark.position / duration) * 100;
          return (
            <button
              key={bookmark.id}
              className="absolute top-0 -translate-x-1/2 w-4 h-4 text-yellow-400 hover:text-yellow-300 transition-colors z-10"
              style={{ left: `${position}%` }}
              onClick={(e) => {
                e.stopPropagation();
                onBookmarkClick?.(bookmark);
              }}
              title={bookmark.note || 'Bookmark'}
            >
              <Bookmark className="h-4 w-4 fill-current" />
            </button>
          );
        })}

        {/* Progress Knob */}
        <motion.div
          className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-4 h-4 bg-white rounded-full shadow-lg shadow-purple-500/50 z-20 cursor-grab active:cursor-grabbing"
          style={{ left: `${progress}%` }}
          whileHover={{ scale: 1.2 }}
          whileTap={{ scale: 1.1 }}
        >
          <div className="absolute inset-0.5 bg-gradient-to-br from-purple-400 to-pink-400 rounded-full" />
        </motion.div>

        {/* Hover Tooltip */}
        {hoveredTime !== null && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="absolute bottom-full mb-2 -translate-x-1/2 pointer-events-none z-30"
            style={{ left: `${hoverProgress}%` }}
          >
            <div className="bg-gray-900/95 backdrop-blur-md px-3 py-2 rounded-lg border border-gray-700/50 shadow-xl">
              <p className="text-sm font-mono text-white whitespace-nowrap">
                {formatTime(hoveredTime)}
              </p>
              {hoveredChapter && (
                <p className="text-xs text-purple-400 truncate max-w-32">
                  {hoveredChapter.title}
                </p>
              )}
            </div>
            {/* Arrow */}
            <div className="absolute left-1/2 -translate-x-1/2 -bottom-1 w-2 h-2 bg-gray-900 rotate-45 border-r border-b border-gray-700/50" />
          </motion.div>
        )}
      </div>

      {/* Time Labels */}
      <div className="flex items-center justify-between text-xs text-gray-500 px-1">
        <span className="font-mono">{formatTime(currentTime)}</span>

        {/* Current Chapter Label */}
        {currentChapter && (
          <span className="text-purple-400 truncate max-w-48 px-2">
            {currentChapter.title}
          </span>
        )}

        <span className="font-mono">{formatTime(duration)}</span>
      </div>

      {/* Chapter Quick Navigation (collapsed by default, expandable) */}
      {chapters.length > 0 && (
        <div className="pt-2">
          <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-hide">
            {chapters.map((chapter, idx) => {
              const isActive = chapter.id === currentChapter?.id;
              const isCompleted = currentTime >= chapter.endTime;

              return (
                <button
                  key={chapter.id}
                  onClick={() => onChapterClick?.(chapter)}
                  className={`flex-shrink-0 flex items-center gap-2 px-3 py-1.5 rounded-full text-xs transition-all ${
                    isActive
                      ? 'bg-purple-500/30 text-purple-300 border border-purple-500/50'
                      : isCompleted
                      ? 'bg-gray-800/50 text-gray-400 border border-gray-700/50'
                      : 'bg-gray-800/30 text-gray-500 hover:bg-gray-800/50 hover:text-gray-300 border border-transparent'
                  }`}
                >
                  {isActive ? (
                    <Play className="h-3 w-3 fill-current" />
                  ) : isCompleted ? (
                    <span className="text-green-400">✓</span>
                  ) : (
                    <span className="text-gray-600">{idx + 1}</span>
                  )}
                  <span className="truncate max-w-24">{chapter.title}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
