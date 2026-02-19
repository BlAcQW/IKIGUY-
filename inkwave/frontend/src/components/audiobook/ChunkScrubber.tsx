/**
 * ChunkScrubber Component
 *
 * Visual chunk navigation inspired by Libby app.
 * Shows all chunks as segments, highlights current and listened chunks.
 */

import { useMemo } from 'react';
import { motion } from 'framer-motion';

interface ChunkScrubberProps {
  totalChunks: number;
  currentChunk: number;
  chunkDurations: number[];
  listenedChunks: number;
  onChunkSelect: (chunkIndex: number) => void;
}

export default function ChunkScrubber({
  totalChunks,
  currentChunk,
  chunkDurations,
  listenedChunks,
  onChunkSelect,
}: ChunkScrubberProps) {
  // Calculate relative widths based on duration
  const chunkWidths = useMemo(() => {
    if (chunkDurations.length === 0) {
      return Array(totalChunks).fill(100 / totalChunks);
    }

    const total = chunkDurations.reduce((a, b) => a + b, 0);
    return chunkDurations.map((d) => (d / total) * 100);
  }, [chunkDurations, totalChunks]);

  // Determine chunk status
  const getChunkStatus = (index: number): 'listened' | 'current' | 'upcoming' => {
    if (index < currentChunk || index < listenedChunks) return 'listened';
    if (index === currentChunk) return 'current';
    return 'upcoming';
  };

  // Status colors
  const statusColors = {
    listened: 'bg-gray-500',
    current: 'bg-gradient-to-r from-purple-500 to-pink-500',
    upcoming: 'bg-gray-700',
  };

  return (
    <div className="w-full mb-2">
      {/* Chunk Label */}
      <div className="flex justify-between text-xs text-gray-500 mb-1">
        <span>Chapter Progress</span>
        <span>
          {currentChunk + 1} / {totalChunks}
        </span>
      </div>

      {/* Chunk Segments */}
      <div className="flex gap-0.5 h-3 w-full rounded-full overflow-hidden bg-gray-800/50">
        {Array.from({ length: totalChunks }, (_, index) => {
          const status = getChunkStatus(index);
          const width = chunkWidths[index] || 100 / totalChunks;

          return (
            <motion.button
              key={index}
              onClick={() => onChunkSelect(index)}
              className={`h-full transition-all duration-200 hover:brightness-125 ${statusColors[status]} ${
                status === 'current' ? 'shadow-lg shadow-purple-500/30' : ''
              }`}
              style={{ width: `${width}%`, minWidth: 4 }}
              whileHover={{ scaleY: 1.2 }}
              whileTap={{ scale: 0.95 }}
              aria-label={`Go to chapter ${index + 1}`}
              title={`Chapter ${index + 1}${
                chunkDurations[index]
                  ? ` (${formatDuration(chunkDurations[index])})`
                  : ''
              }`}
            />
          );
        })}
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-4 mt-2 text-[10px] text-gray-500">
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-gray-500" />
          <span>Listened</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-gradient-to-r from-purple-500 to-pink-500" />
          <span>Current</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-gray-700" />
          <span>Upcoming</span>
        </div>
      </div>
    </div>
  );
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}
