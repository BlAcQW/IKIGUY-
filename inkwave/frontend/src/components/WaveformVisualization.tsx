/**
 * Waveform Visualization Component
 *
 * Displays an animated audio waveform visualization during playback.
 * Shows frequency bars with purple/pink gradient styling.
 */

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

interface WaveformVisualizationProps {
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  barCount?: number;
  height?: number;
}

export default function WaveformVisualization({
  isPlaying,
  currentTime,
  duration,
  barCount = 50,
  height = 60
}: WaveformVisualizationProps) {
  const [bars, setBars] = useState<number[]>([]);

  // Generate random bar heights for visualization
  useEffect(() => {
    const generateBars = () => {
      const newBars = Array.from({ length: barCount }, () =>
        Math.random() * 0.6 + 0.2 // Random height between 0.2 and 0.8
      );
      setBars(newBars);
    };

    generateBars();

    // Update bars during playback for animation effect
    if (isPlaying) {
      const interval = setInterval(generateBars, 150);
      return () => clearInterval(interval);
    }
  }, [isPlaying, barCount]);

  // Calculate which bars should be filled based on progress
  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;
  const filledBarCount = Math.floor((progress / 100) * barCount);

  return (
    <div className="w-full flex items-center justify-center gap-[2px] py-2" style={{ height: `${height}px` }}>
      {bars.map((heightRatio, index) => {
        const isFilled = index < filledBarCount;
        const barHeight = `${heightRatio * 100}%`;

        return (
          <motion.div
            key={index}
            className={`flex-1 rounded-full transition-all duration-150 ${
              isFilled
                ? 'bg-gradient-to-t from-purple-500 to-pink-500'
                : 'bg-gray-700'
            }`}
            style={{
              height: barHeight,
              minHeight: '4px',
              maxHeight: '100%'
            }}
            animate={{
              height: isPlaying ? barHeight : '20%',
              opacity: isPlaying ? (isFilled ? 1 : 0.4) : (isFilled ? 0.8 : 0.3)
            }}
            transition={{
              duration: 0.15,
              ease: 'easeOut'
            }}
          />
        );
      })}
    </div>
  );
}
