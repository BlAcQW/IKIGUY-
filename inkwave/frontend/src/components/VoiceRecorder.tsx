/**
 * VoiceRecorder Component
 * Voice recording UI with waveform animation and live transcription
 */

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, Square, X, Send } from 'lucide-react';
import { useVoiceRecorder } from '../hooks/useVoiceRecorder';
import { useSpeechRecognition } from '../hooks/useSpeechRecognition';

interface VoiceRecorderProps {
  onComplete: (audioBlob: Blob, transcript: string) => void;
  onCancel: () => void;
  maxDuration?: number;
}

export default function VoiceRecorder({
  onComplete,
  onCancel,
  maxDuration = 60,
}: VoiceRecorderProps) {
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);

  // Voice recording hook
  const {
    isRecording,
    duration,
    audioLevel,
    startRecording,
    stopRecording,
    cancelRecording,
  } = useVoiceRecorder({
    onRecordingComplete: (blob) => {
      setAudioBlob(blob);
      speechStopListening();
    },
    onError: (error) => {
      console.error('Recording error:', error);
      alert(error);
    },
    maxDuration,
  });

  // Speech recognition hook
  const {
    isListening,
    transcript,
    interimTranscript,
    isSupported: isSpeechSupported,
    startListening: speechStartListening,
    stopListening: speechStopListening,
  } = useSpeechRecognition({
    onError: (error) => {
      console.error('Speech recognition error:', error);
    },
  });

  // Auto-start recording on mount
  useEffect(() => {
    startRecording();
    if (isSpeechSupported) {
      speechStartListening();
    }
  }, []);

  const handleStop = () => {
    stopRecording();
  };

  const handleCancel = () => {
    cancelRecording();
    speechStopListening();
    onCancel();
  };

  const handleSend = () => {
    if (audioBlob) {
      onComplete(audioBlob, transcript);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const fullTranscript = transcript + interimTranscript;

  // Generate waveform bars based on audio level
  const waveformBars = Array.from({ length: 40 }, (_, i) => {
    // Create wave pattern with some randomness
    const baseHeight = isRecording
      ? Math.sin(i * 0.5 + Date.now() * 0.01) * 0.5 + 0.5
      : 0.1;
    const audioInfluence = isRecording ? audioLevel : 0;
    const height = Math.max(0.1, baseHeight * 0.3 + audioInfluence * 0.7);

    return height;
  });

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm"
    >
      <div className="max-w-2xl w-full mx-4 bg-gray-900 rounded-2xl p-8 space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-white">
            {isRecording ? 'Listening...' : 'Recording Complete'}
          </h2>
          <button
            onClick={handleCancel}
            className="p-2 hover:bg-gray-800 rounded-lg transition"
          >
            <X className="h-6 w-6 text-gray-400" />
          </button>
        </div>

        {/* Waveform Visualization */}
        <div className="flex items-center justify-center space-x-1 h-32">
          {waveformBars.map((height, i) => (
            <motion.div
              key={i}
              className="w-2 bg-gradient-to-t from-purple-500 to-pink-500 rounded-full"
              animate={{
                height: `${height * 100}%`,
              }}
              transition={{
                duration: 0.1,
                ease: 'linear',
              }}
            />
          ))}
        </div>

        {/* Recording Status */}
        <div className="text-center space-y-2">
          {isRecording && (
            <motion.div
              animate={{ opacity: [1, 0.5, 1] }}
              transition={{ duration: 1.5, repeat: Infinity }}
              className="flex items-center justify-center space-x-2"
            >
              <div className="w-3 h-3 bg-red-500 rounded-full" />
              <span className="text-red-400 font-semibold">Recording</span>
            </motion.div>
          )}
          <p className="text-3xl font-mono text-white">{formatTime(duration)}</p>
          <p className="text-sm text-gray-500">
            Max duration: {formatTime(maxDuration)}
          </p>
        </div>

        {/* Live Transcript */}
        {fullTranscript && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gray-800 rounded-lg p-4"
          >
            <p className="text-sm text-gray-400 mb-2">Live Transcription:</p>
            <p className="text-white">
              {transcript}
              <span className="text-gray-500">{interimTranscript}</span>
            </p>
          </motion.div>
        )}

        {!isSpeechSupported && (
          <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3">
            <p className="text-sm text-yellow-400">
              Live transcription not available in this browser. Your recording
              will still be processed.
            </p>
          </div>
        )}

        {/* Controls */}
        <div className="flex items-center justify-center space-x-4">
          {isRecording ? (
            <>
              {/* Cancel */}
              <button
                onClick={handleCancel}
                className="px-6 py-3 bg-gray-800 hover:bg-gray-700 rounded-full text-gray-300 hover:text-white transition"
              >
                Cancel
              </button>

              {/* Stop */}
              <button
                onClick={handleStop}
                className="flex items-center space-x-2 px-8 py-4 bg-red-500 hover:bg-red-600 rounded-full text-white font-semibold transition"
              >
                <Square className="h-5 w-5 fill-white" />
                <span>Stop Recording</span>
              </button>
            </>
          ) : (
            <>
              {/* Cancel */}
              <button
                onClick={handleCancel}
                className="px-6 py-3 bg-gray-800 hover:bg-gray-700 rounded-full text-gray-300 hover:text-white transition"
              >
                Cancel
              </button>

              {/* Send */}
              <button
                onClick={handleSend}
                disabled={!audioBlob}
                className="flex items-center space-x-2 px-8 py-4 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 rounded-full text-white font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send className="h-5 w-5" />
                <span>Send Question</span>
              </button>
            </>
          )}
        </div>

        {/* Tips */}
        {isRecording && (
          <div className="text-center">
            <p className="text-xs text-gray-500">
              💡 Tip: Speak clearly and ask your question about the book
            </p>
          </div>
        )}
      </div>
    </motion.div>
  );
}
