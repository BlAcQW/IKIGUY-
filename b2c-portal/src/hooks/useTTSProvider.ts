/**
 * Custom hook for managing TTS provider state and API calls
 */

import { useState, useCallback, useEffect } from 'react';
import { TTSProvider } from '../config/tts-providers';
import { API_ENDPOINTS } from '../config/api-config';
import { useAudioWorker } from './useAudioWorker';

interface SynthesisRequest {
  text: string;
  language?: string;
  speaker?: string | number;
  speed?: number;
  pitch?: number;
  onProgress?: (progress: number, stage: string) => void;
}

interface VoiceCloningRequest {
  text: string;
  referenceAudio: File;
  language?: string;
  // StyleTTS2 specific parameters
  alpha?: number;  // Timbre control (0-1)
  beta?: number;   // Prosody control (0-1)
  diffusion_steps?: number;
  embedding_scale?: number;
  onProgress?: (progress: number, stage: string) => void;
}

interface CostEstimate {
  estimated_cost: number;
  character_count: number;
  provider_id: string;
}

interface UseTTSProviderReturn {
  selectedProvider: TTSProvider | null;
  setSelectedProvider: (providerId: string) => void;
  providers: Record<string, TTSProvider>;
  isLoading: boolean;
  error: string | null;
  isLoadingProviders: boolean;
  refreshProviders: (forceRefresh?: boolean) => Promise<void>;
  synthesize: (request: SynthesisRequest) => Promise<Blob | null>;
  synthesizeWithVoiceCloning: (request: VoiceCloningRequest) => Promise<Blob | null>;
  estimateCost: (text: string, voiceCloning?: boolean) => Promise<CostEstimate | null>;
  getLanguages: () => Promise<string[]>;
  getSpeakers: (language?: string) => Promise<string[]>;
  checkHealth: () => Promise<boolean>;
}

export const useTTSProvider = (): UseTTSProviderReturn => {
  const [selectedProvider, setSelectedProviderState] = useState<TTSProvider | null>(null);
  const [providers, setProviders] = useState<Record<string, TTSProvider>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingProviders, setIsLoadingProviders] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Web Worker for audio decoding (performance optimization)
  const { decodeAudio } = useAudioWorker();

  // Fetch providers from backend API
  const fetchProviders = useCallback(async (forceRefresh: boolean = false) => {
    setIsLoadingProviders(true);
    try {
      const url = `${API_ENDPOINTS.tts.providers}${forceRefresh ? '?force_refresh=true' : ''}`;
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Failed to fetch providers: ${response.statusText}`);
      }

      const data = await response.json();

      if (data.providers) {
        setProviders(data.providers);

        // If no provider is selected, select the first online provider
        if (!selectedProvider && Object.keys(data.providers).length > 0) {
          const firstOnline = Object.values(data.providers).find(
            (p: any) => p.status === 'online'
          ) as TTSProvider | undefined;

          if (firstOnline) {
            setSelectedProviderState(firstOnline);
          } else {
            // If no online providers, just select the first one
            setSelectedProviderState(Object.values(data.providers)[0] as TTSProvider);
          }
        } else if (selectedProvider && data.providers[selectedProvider.id]) {
          // Update the selected provider with fresh data
          setSelectedProviderState(data.providers[selectedProvider.id]);
        }
      }
    } catch (err) {
      console.error('Error fetching providers:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch providers');
    } finally {
      setIsLoadingProviders(false);
    }
  }, [selectedProvider]);

  // Fetch providers on mount
  useEffect(() => {
    fetchProviders();
  }, []);

  // Auto-refresh provider status every 2 minutes (configurable)
  useEffect(() => {
    // Configurable refresh interval: default 2 minutes for real-time status updates
    const REFRESH_INTERVAL_MS = process.env.REACT_APP_TTS_REFRESH_INTERVAL
      ? parseInt(process.env.REACT_APP_TTS_REFRESH_INTERVAL)
      : 120000; // 2 minutes in milliseconds

    const interval = setInterval(() => {
      fetchProviders(false); // Don't force refresh, use cache if available
    }, REFRESH_INTERVAL_MS);

    return () => clearInterval(interval);
  }, [fetchProviders]);

  const setSelectedProvider = useCallback((providerId: string) => {
    console.log('[useTTSProvider] setSelectedProvider called with:', providerId);
    console.log('[useTTSProvider] Available providers:', Object.keys(providers));
    const provider = providers[providerId];
    if (provider) {
      console.log('[useTTSProvider] Setting provider:', provider.name);
      setSelectedProviderState(provider);
      setError(null);
    } else {
      console.warn('[useTTSProvider] Provider not found:', providerId);
    }
  }, [providers]);

  const checkHealth = useCallback(async (): Promise<boolean> => {
    if (!selectedProvider) return false;

    try {
      const response = await fetch(`${selectedProvider.endpoint}/health`);
      if (response.ok) {
        const data = await response.json();
        return data.status === 'healthy' || response.status === 200;
      }
      return false;
    } catch (err) {
      console.error('Health check failed:', err);
      return false;
    }
  }, [selectedProvider]);

  const getLanguages = useCallback(async (): Promise<string[]> => {
    if (!selectedProvider) return [];

    try {
      // Call backend proxy endpoint to avoid CORS issues
      const url = `${API_ENDPOINTS.tts.provider(selectedProvider.id)}/languages`;
      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        return data.languages || [];
      }
      return selectedProvider.languageList || [];
    } catch (err) {
      console.error('Failed to fetch languages:', err);
      return selectedProvider.languageList || [];
    }
  }, [selectedProvider]);

  const getSpeakers = useCallback(async (language?: string): Promise<string[]> => {
    if (!selectedProvider || !selectedProvider.capabilities.multiSpeaker) return [];

    try {
      // Call backend proxy endpoint to avoid CORS issues
      const endpoint = language
        ? `${API_ENDPOINTS.tts.provider(selectedProvider.id)}/speakers?language=${language}`
        : `${API_ENDPOINTS.tts.provider(selectedProvider.id)}/speakers`;
      const response = await fetch(endpoint);
      if (response.ok) {
        const data = await response.json();
        return data.speakers || [];
      }
      return [];
    } catch (err) {
      console.error('Failed to fetch speakers:', err);
      return [];
    }
  }, [selectedProvider]);

  const synthesize = useCallback(
    async (request: SynthesisRequest): Promise<Blob | null> => {
      if (!selectedProvider) {
        setError('No provider selected');
        return null;
      }

      setIsLoading(true);
      setError(null);

      try {
        // Report progress: Connecting
        if (request.onProgress) {
          request.onProgress(10, 'Connecting to TTS service...');
        }

        // Call backend API for synthesis (with automatic billing and default voice handling)
        const response = await fetch(API_ENDPOINTS.tts.synthesize, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            provider_id: selectedProvider.id,
            text: request.text,
            language: request.language || 'en',
            voice_id: request.speaker,
            speed: request.speed || 1.0,
            pitch: request.pitch || 0.0,
            remove_silence: false,
            output_format: 'wav',
          }),
        });

        // Report progress: Sent request
        if (request.onProgress) {
          request.onProgress(40, 'Processing your text...');
        }

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || 'Synthesis failed');
        }

        // Report progress: Receiving response
        if (request.onProgress) {
          request.onProgress(70, 'Receiving audio data...');
        }

        const result = await response.json();

        // Report progress: Decoding audio
        if (request.onProgress) {
          request.onProgress(85, 'Decoding audio...');
        }

        // Decode base64 audio to blob using Web Worker (prevents UI blocking)
        return new Promise<Blob | null>((resolve) => {
          decodeAudio(result.audio_base64, (blob, error) => {
            if (error) {
              console.error('Audio decode error:', error);
              setError(error);
              resolve(null);
            } else {
              // Report progress: Complete
              if (request.onProgress) {
                request.onProgress(100, 'Complete!');
              }
              resolve(blob);
            }
          });
        });
      } catch (err: any) {
        const errorMessage = err.message || 'Synthesis failed';
        setError(errorMessage);
        console.error('Synthesis error:', err);
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [selectedProvider, decodeAudio]
  );

  const synthesizeWithVoiceCloning = useCallback(
    async (request: VoiceCloningRequest): Promise<Blob | null> => {
      if (!selectedProvider) {
        setError('No provider selected');
        return null;
      }

      if (!selectedProvider.capabilities.voiceCloning) {
        setError('Selected provider does not support voice cloning');
        return null;
      }

      setIsLoading(true);
      setError(null);

      try {
        // Report progress: Preparing
        if (request.onProgress) {
          request.onProgress(10, 'Preparing voice cloning...');
        }

        const formData = new FormData();
        formData.append('text', request.text);
        formData.append('language', request.language || 'en');

        // F5-TTS and StyleTTS2 use /clone endpoint with reference_audio parameter
        if (selectedProvider.id === 'f5tts') {
          formData.append('ref_audio', request.referenceAudio);
          formData.append('speed', '1.0');
          formData.append('remove_silence', 'true');
        } else if (selectedProvider.id === 'styletts2') {
          formData.append('reference_audio', request.referenceAudio);
          // StyleTTS2 specific parameters
          formData.append('alpha', (request.alpha ?? 0.3).toString());
          formData.append('beta', (request.beta ?? 0.7).toString());
          formData.append('diffusion_steps', (request.diffusion_steps ?? 5).toString());
          formData.append('embedding_scale', (request.embedding_scale ?? 1.0).toString());
        } else {
          formData.append('reference_audio', request.referenceAudio);
        }

        // F5-TTS and StyleTTS2 use /clone endpoint, others use /synthesize_with_reference
        const endpoint = ['f5tts', 'styletts2'].includes(selectedProvider.id)
          ? `${selectedProvider.endpoint}/clone`
          : `${selectedProvider.endpoint}/synthesize_with_reference`;

        // Report progress: Sending
        if (request.onProgress) {
          request.onProgress(30, 'Uploading reference audio...');
        }

        const response = await fetch(endpoint, {
          method: 'POST',
          body: formData,
        });

        // Report progress: Processing
        if (request.onProgress) {
          request.onProgress(60, 'Cloning voice...');
        }

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || 'Voice cloning failed');
        }

        // Report progress: Receiving
        if (request.onProgress) {
          request.onProgress(90, 'Receiving audio...');
        }

        const blob = await response.blob();

        // Report progress: Complete
        if (request.onProgress) {
          request.onProgress(100, 'Complete!');
        }

        return blob;
      } catch (err: any) {
        const errorMessage = err.message || 'Voice cloning failed';
        setError(errorMessage);
        console.error('Voice cloning error:', err);
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [selectedProvider]
  );

  const estimateCost = useCallback(
    async (text: string, voiceCloning: boolean = false): Promise<CostEstimate | null> => {
      if (!selectedProvider) {
        return null;
      }

      if (!text || text.trim().length === 0) {
        return null;
      }

      try {
        const response = await fetch(API_ENDPOINTS.tts.estimateCost, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            provider_id: selectedProvider.id,
            text: text,
            voice_cloning: voiceCloning,
          }),
        });

        if (!response.ok) {
          console.error('Cost estimation failed:', response.statusText);
          return null;
        }

        const data = await response.json();
        return data as CostEstimate;
      } catch (err) {
        console.error('Cost estimation error:', err);
        return null;
      }
    },
    [selectedProvider]
  );

  return {
    selectedProvider,
    setSelectedProvider,
    providers,
    isLoading,
    error,
    isLoadingProviders,
    refreshProviders: fetchProviders,
    synthesize,
    synthesizeWithVoiceCloning,
    estimateCost,
    getLanguages,
    getSpeakers,
    checkHealth,
  };
};
