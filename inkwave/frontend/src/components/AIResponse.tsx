/**
 * AIResponse Component
 * Display AI-generated answer with audio playback
 */

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Volume2, VolumeX, Sparkles, Copy, Check } from 'lucide-react';
import { useAudioPlayer } from '../hooks/useAudioPlayer';

interface AIResponseProps {
  question: string;
  answer: string;
  audioUrl?: string;
  timestamp: Date;
  onClose?: () => void;
}

export default function AIResponse({
  question,
  answer,
  audioUrl,
  timestamp,
  onClose,
}: AIResponseProps) {
  const [copied, setCopied] = useState(false);
  const [isAudioEnabled, setIsAudioEnabled] = useState(true);

  // Audio player for AI response
  const {
    isPlaying,
    togglePlay,
    error: audioError,
  } = useAudioPlayer({
    src: audioUrl,
  });

  // Auto-play audio when response appears (if available)
  useEffect(() => {
    if (audioUrl && isAudioEnabled) {
      // Small delay to let component mount
      setTimeout(() => {
        togglePlay();
      }, 300);
    }
  }, [audioUrl, isAudioEnabled]);

  const handleCopy = () => {
    navigator.clipboard.writeText(answer);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const toggleAudio = () => {
    setIsAudioEnabled(!isAudioEnabled);
    if (isPlaying) {
      togglePlay();
    }
  };

  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    }).format(date);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="bg-gradient-to-br from-purple-900/30 to-pink-900/30 border border-purple-500/30 rounded-2xl p-6 space-y-4"
    >
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-2">
          <div className="p-2 bg-purple-500/20 rounded-lg">
            <Sparkles className="h-5 w-5 text-purple-400" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-purple-300">
              AI Assistant
            </h3>
            <p className="text-xs text-gray-500">{formatTime(timestamp)}</p>
          </div>
        </div>

        {/* Audio Controls */}
        <div className="flex items-center space-x-2">
          {audioUrl && (
            <button
              onClick={toggleAudio}
              className={`p-2 rounded-lg transition ${
                isAudioEnabled
                  ? 'bg-purple-500/20 text-purple-400'
                  : 'bg-gray-800 text-gray-500'
              }`}
              title={isAudioEnabled ? 'Mute audio' : 'Enable audio'}
            >
              {isAudioEnabled ? (
                <Volume2 className="h-4 w-4" />
              ) : (
                <VolumeX className="h-4 w-4" />
              )}
            </button>
          )}

          <button
            onClick={handleCopy}
            className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition"
            title="Copy answer"
          >
            {copied ? (
              <Check className="h-4 w-4 text-green-400" />
            ) : (
              <Copy className="h-4 w-4 text-gray-400" />
            )}
          </button>
        </div>
      </div>

      {/* Question */}
      <div className="space-y-2">
        <p className="text-xs font-semibold text-gray-400 uppercase">
          Your Question:
        </p>
        <p className="text-sm text-gray-300 italic">"{question}"</p>
      </div>

      {/* Answer */}
      <div className="space-y-2">
        <p className="text-xs font-semibold text-gray-400 uppercase">Answer:</p>
        <div className="prose prose-invert prose-sm max-w-none">
          <p className="text-white leading-relaxed whitespace-pre-wrap">
            {answer}
          </p>
        </div>
      </div>

      {/* Audio Status */}
      {audioUrl && isAudioEnabled && (
        <div className="flex items-center space-x-2 text-xs text-gray-500">
          {isPlaying && (
            <>
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 1, repeat: Infinity }}
                className="w-2 h-2 bg-purple-500 rounded-full"
              />
              <span>Playing audio response...</span>
            </>
          )}
          {audioError && <span className="text-red-400">{audioError}</span>}
        </div>
      )}

      {/* Disclaimer */}
      <div className="pt-4 border-t border-gray-700">
        <p className="text-xs text-gray-500">
          💡 AI-generated answers are based on the book content. Always verify
          important information.
        </p>
      </div>
    </motion.div>
  );
}
