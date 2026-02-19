/**
 * Synthesis Progress Component
 *
 * Displays a progress bar with stage information during TTS synthesis.
 * Created: 2025-10-27
 * Sprint 3: Performance Optimization (Phase 8)
 */

import React from 'react';

interface SynthesisProgressProps {
  progress: number;
  stage: string;
}

export const SynthesisProgress: React.FC<SynthesisProgressProps> = ({ progress, stage }) => {
  return (
    <div className="w-full space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span className="text-gray-700 font-medium">{stage}</span>
        <span className="text-gray-600">{progress}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2.5 overflow-hidden">
        <div
          className="bg-indigo-600 h-2.5 rounded-full transition-all duration-300 ease-out"
          style={{ width: `${progress}%` }}
        >
          {progress > 0 && (
            <div className="w-full h-full bg-gradient-to-r from-transparent to-indigo-400 animate-pulse" />
          )}
        </div>
      </div>
    </div>
  );
};
