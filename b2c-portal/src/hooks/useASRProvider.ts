/**
 * Custom hook for managing ASR provider state and API calls
 *
 * Refactored to use centralized backend API with automatic billing and health monitoring.
 * All ASR requests now go through /api/asr/* endpoints instead of direct provider calls.
 */

import { useState, useCallback, useEffect } from 'react';
import { API_ENDPOINTS } from '../config/api-config';

interface TranscriptionRequest {
  audio: File | Blob;
  language?: string;
  task?: 'transcribe' | 'translate';
  responseFormat?: 'json' | 'text' | 'srt' | 'vtt';
  temperature?: number;
  timestampGranularities?: string[];
}

interface TranscriptionSegment {
  id: number;
  start: number;
  end: number;
  text: string;
  tokens?: number[];
  temperature?: number;
  avg_logprob?: number;
  compression_ratio?: number;
  no_speech_prob?: number;
}

interface TranscriptionResult {
  text: string;
  providerId: string;
  language?: string;
  duration?: number;
  segments?: TranscriptionSegment[];
  cost: number;
  transactionId?: string;
  processingTime: number;
  modelName?: string;
}

interface ASRProvider {
  id: string;
  name: string;
  endpoint: string;
  status: 'online' | 'offline' | 'degraded';
  last_check: string;
  response_time_ms: number | null;
  error_message: string | null;
  provider_type: 'asr';
}

interface ProvidersResponse {
  providers: Record<string, ASRProvider>;
  count: number;
  online_count: number;
  offline_count: number;
}

interface UseASRProviderReturn {
  selectedProvider: ASRProvider | null;
  providers: Record<string, ASRProvider>;
  setSelectedProvider: (providerId: string) => void;
  isLoading: boolean;
  error: string | null;
  transcribe: (request: TranscriptionRequest) => Promise<TranscriptionResult | null>;
  refreshProviders: (forceRefresh?: boolean) => Promise<void>;
  getLanguages: (providerId: string) => Promise<string[]>;
  estimateCost: (audio: File | Blob) => Promise<number | null>;
}

export const useASRProvider = (): UseASRProviderReturn => {
  const [providers, setProviders] = useState<Record<string, ASRProvider>>({});
  const [selectedProvider, setSelectedProviderState] = useState<ASRProvider | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch providers on mount and set up auto-refresh
  useEffect(() => {
    refreshProviders(false);

    // Auto-refresh every 3 hours
    const interval = setInterval(() => {
      refreshProviders(false);
    }, 10800000); // 3 hours in milliseconds

    return () => clearInterval(interval);
  }, []);

  // Auto-select first online provider when providers load
  useEffect(() => {
    if (Object.keys(providers).length > 0 && !selectedProvider) {
      // Find first online provider
      const onlineProvider = Object.values(providers).find(p => p.status === 'online');
      if (onlineProvider) {
        setSelectedProviderState(onlineProvider);
      }
    }
  }, [providers, selectedProvider]);

  const refreshProviders = useCallback(async (forceRefresh: boolean = false) => {
    try {
      const url = `${API_ENDPOINTS.asr.providers}${forceRefresh ? '?force_refresh=true' : ''}`;
      const response = await fetch(url, {
        credentials: 'include', // Include auth cookies
      });

      if (!response.ok) {
        throw new Error('Failed to fetch ASR providers');
      }

      const data: ProvidersResponse = await response.json();

      // Map backend providers to frontend structure
      // Consolidate all Whisper-based providers under single 'whisper' provider
      const mappedProviders: Record<string, ASRProvider> = {};
      let whisperProvider: ASRProvider | null = null;

      for (const [key, provider] of Object.entries(data.providers)) {
        // Check if this is a Whisper-based provider
        if (key.includes('whisper') || key.includes('akan') || key.includes('faster')) {
          // Use the first Whisper provider as the base, or create a consolidated one
          if (!whisperProvider) {
            whisperProvider = {
              ...provider,
              id: 'whisper',
              name: 'OpenAI Whisper',
              endpoint: provider.endpoint || 'https://flow-api.ailabsafrica.com/api/voice-lab/transcribe'
            };
          }
          // Update status to online if any Whisper variant is online
          if (provider.status === 'online') {
            whisperProvider.status = 'online';
          }
        } else {
          // Keep non-Whisper providers as-is
          mappedProviders[key] = provider;
        }
      }

      // Add the consolidated Whisper provider
      if (whisperProvider) {
        mappedProviders['whisper'] = whisperProvider;
      }

      setProviders(mappedProviders);

    } catch (err: any) {
      console.error('Failed to fetch providers:', err);
      setError(err.message || 'Failed to load providers');
    }
  }, []);

  const setSelectedProvider = useCallback((providerId: string) => {
    const provider = providers[providerId];
    if (provider) {
      setSelectedProviderState(provider);
      setError(null);
    } else {
      setError(`Provider ${providerId} not found`);
    }
  }, [providers]);

  const getLanguages = useCallback(async (providerId: string): Promise<string[]> => {
    try {
      const response = await fetch(API_ENDPOINTS.asr.languages(providerId), {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to fetch languages');
      }

      const data = await response.json();
      return data.languages || [];
    } catch (err: any) {
      console.error('Failed to fetch languages:', err);
      return [];
    }
  }, []);

  const estimateCost = useCallback(
    async (audio: File | Blob): Promise<number | null> => {
      if (!selectedProvider) {
        setError('No provider selected');
        return null;
      }

      try {
        // Convert audio to base64
        const arrayBuffer = await audio.arrayBuffer();
        const base64Audio = btoa(
          new Uint8Array(arrayBuffer).reduce(
            (data, byte) => data + String.fromCharCode(byte),
            ''
          )
        );

        const response = await fetch(API_ENDPOINTS.asr.estimateCost, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({
            provider_id: selectedProvider.id,
            audio_base64: base64Audio,
          }),
        });

        if (!response.ok) {
          throw new Error('Failed to estimate cost');
        }

        const data = await response.json();
        return data.estimated_cost;
      } catch (err: any) {
        console.error('Cost estimation error:', err);
        return null;
      }
    },
    [selectedProvider]
  );

  const transcribe = useCallback(
    async (request: TranscriptionRequest): Promise<TranscriptionResult | null> => {
      if (!selectedProvider) {
        setError('No provider selected');
        return null;
      }

      setIsLoading(true);
      setError(null);

      try {
        // Use multipart form upload endpoint
        const formData = new FormData();
        formData.append('audio_file', request.audio);
        formData.append('provider_id', selectedProvider.id);

        if (request.language) {
          formData.append('language', request.language);
        }

        if (request.task) {
          formData.append('task', request.task);
        }

        if (request.responseFormat) {
          formData.append('response_format', request.responseFormat);
        }

        if (request.temperature !== undefined) {
          formData.append('temperature', request.temperature.toString());
        }

        // Call centralized backend API
        const response = await fetch(API_ENDPOINTS.asr.transcribeUpload, {
          method: 'POST',
          credentials: 'include', // Include auth cookies for billing
          body: formData,
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: 'Transcription failed' }));
          throw new Error(errorData.detail || 'Transcription failed');
        }

        const result: TranscriptionResult = await response.json();

        // Log cost information
        console.info(
          `💰 ASR Transcription Cost: $${result.cost.toFixed(4)} | ` +
          `Duration: ${result.duration?.toFixed(2)}s | ` +
          `Provider: ${result.providerId} | ` +
          `Time: ${result.processingTime.toFixed(2)}s`
        );

        return result;
      } catch (err: any) {
        const errorMessage = err.message || 'Failed to transcribe audio';
        setError(errorMessage);
        console.error('Transcription error:', err);
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [selectedProvider]
  );

  return {
    selectedProvider,
    providers,
    setSelectedProvider,
    isLoading,
    error,
    transcribe,
    refreshProviders,
    getLanguages,
    estimateCost,
  };
};
