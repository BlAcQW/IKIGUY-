import { useState, useRef, useCallback } from 'react';
import { synthesizeSpeech } from '@/services/voice-api';
import { playAudioBase64 } from '@/lib/audio-utils';
import type { SynthesisOptions as ApiSynthesisOptions, SynthesisResult as ApiSynthesisResult } from '@/types/voice-lab';

// Re-export types for convenience
export type SynthesisOptions = ApiSynthesisOptions;
export type SynthesisResult = ApiSynthesisResult;

interface UseVoiceSynthesisReturn {
  synthesize: (text: string, options?: SynthesisOptions) => Promise<SynthesisResult>;
  play: (audioBase64: string) => Promise<void>;
  stop: () => void;
  isSynthesizing: boolean;
  isPlaying: boolean;
  result: SynthesisResult | null;
  error: Error | null;
  clearResult: () => void;
}

/**
 * Reusable hook for voice synthesis (Text-to-Speech)
 *
 * @example
 * const { synthesize, play, isPlaying, result } = useVoiceSynthesis();
 *
 * const handleSpeak = async () => {
 *   const result = await synthesize('Akwaaba', {
 *     model: 'akan-mms',
 *     language: 'tw',
 *     speed: 1.0
 *   });
 *   await play(result.audioBase64);
 * };
 */
export const useVoiceSynthesis = (): UseVoiceSynthesisReturn => {
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [result, setResult] = useState<SynthesisResult | null>(null);
  const [error, setError] = useState<Error | null>(null);

  const audioRef = useRef<HTMLAudioElement | null>(null);

  /**
   * Synthesize text to speech using voice-api service
   */
  const synthesize = useCallback(async (text: string, options: SynthesisOptions = {}) => {
    console.log('[Synthesis] 🔊 Starting synthesis...');
    console.log('[Synthesis] 📝 Text:', text);
    console.log('[Synthesis] ⚙️  Options:', options);

    setIsSynthesizing(true);
    setError(null);

    try {
      // Use voice-api service for synthesis
      const synthesisResult = await synthesizeSpeech(text, options);

      setResult(synthesisResult);
      setIsSynthesizing(false);

      return synthesisResult;
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      console.error('[Synthesis] ❌ Synthesis failed:', error);

      setError(error);
      setIsSynthesizing(false);

      throw error;
    }
  }, []);

  /**
   * Play audio from base64 string using voice-api service
   */
  const play = useCallback(async (audioBase64: string) => {
    console.log('[Synthesis] ▶️  Playing audio...');

    if (!audioBase64) {
      console.warn('[Synthesis] ⚠️  No audio data to play');
      return;
    }

    try {
      // Stop any currently playing audio
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      }

      setIsPlaying(true);

      // Use voice-api service for playback
      await playAudioBase64(audioBase64);

      setIsPlaying(false);
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      console.error('[Synthesis] ❌ Play failed:', error);
      setIsPlaying(false);
      setError(error);
      throw error;
    }
  }, []);

  /**
   * Stop playing audio
   */
  const stop = useCallback(() => {
    console.log('[Synthesis] ⏹️  Stopping playback');
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsPlaying(false);
    }
  }, []);

  /**
   * Clear current result
   */
  const clearResult = useCallback(() => {
    console.log('[Synthesis] 🗑️  Clearing result');
    setResult(null);
    setError(null);
  }, []);

  return {
    synthesize,
    play,
    stop,
    isSynthesizing,
    isPlaying,
    result,
    error,
    clearResult,
  };
};