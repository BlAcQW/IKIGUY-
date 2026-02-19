import { useState, useCallback } from 'react';
import { transcribeAudio } from '@/services/voice-api';
import type { TranscriptionOptions as ApiTranscriptionOptions, TranscriptionResult as ApiTranscriptionResult } from '@/types/voice-lab';

// Re-export types for convenience
export type TranscriptionOptions = ApiTranscriptionOptions;
export type TranscriptionResult = ApiTranscriptionResult;

interface UseVoiceTranscriptionReturn {
  transcribe: (audioBlob: Blob, options?: TranscriptionOptions) => Promise<TranscriptionResult>;
  isTranscribing: boolean;
  result: TranscriptionResult | null;
  error: Error | null;
  clearResult: () => void;
}

/**
 * Reusable hook for voice transcription (Speech-to-Text)
 *
 * @example
 * const { transcribe, isTranscribing, result, error } = useVoiceTranscription();
 *
 * const handleTranscribe = async (audioBlob) => {
 *   const result = await transcribe(audioBlob, {
 *     language: 'tw',
 *     dialect: 'asante',
 *     model: 'akan-whisper'
 *   });
 *   console.log('Transcription:', result.text);
 * };
 */
export const useVoiceTranscription = (): UseVoiceTranscriptionReturn => {
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [result, setResult] = useState<TranscriptionResult | null>(null);
  const [error, setError] = useState<Error | null>(null);

  /**
   * Transcribe audio blob to text using voice-api service
   */
  const transcribe = useCallback(async (audioBlob: Blob, options: TranscriptionOptions = {}) => {
    console.log('[Transcription] 🎤 Starting transcription...');
    console.log('[Transcription] 📦 Audio blob size:', audioBlob.size, 'bytes');
    console.log('[Transcription] 🎵 Audio type:', audioBlob.type);
    console.log('[Transcription] ⚙️  Options:', options);

    setIsTranscribing(true);
    setError(null);

    try {
      // Use voice-api service for transcription
      const transcriptionResult = await transcribeAudio(audioBlob, options);

      setResult(transcriptionResult);
      setIsTranscribing(false);

      return transcriptionResult;
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      console.error('[Transcription] ❌ Transcription failed:', error);

      setError(error);
      setIsTranscribing(false);

      throw error;
    }
  }, []);

  /**
   * Clear current result
   */
  const clearResult = useCallback(() => {
    console.log('[Transcription] 🗑️  Clearing result');
    setResult(null);
    setError(null);
  }, []);

  return {
    transcribe,
    isTranscribing,
    result,
    error,
    clearResult,
  };
};