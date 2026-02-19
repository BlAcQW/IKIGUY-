/**
 * Custom hook for managing cloned voices
 *
 * Provides functions to:
 * - List cloned voices
 * - Get voice details
 * - Batch clone voices
 * - Delete cloned voices
 */

import { useState, useCallback, useEffect } from 'react';
import { API_BASE_URL } from '../config/api-config';

export interface ClonedVoice {
  voice_id: string;
  name: string;
  provider: string;
  reference_audio_path: string;
  reference_audio_size: number;
  cloned_at: string;
  language: string;
  gender: 'male' | 'female' | 'neutral';
  accent: string;
  description: string;
  capabilities: string[];
  status: 'pending' | 'processing' | 'completed' | 'failed';
  error_message?: string;
}

export interface ClonedVoicesResponse {
  voices: ClonedVoice[];
  total: number;
  filter: {
    provider?: string;
    status?: string;
  };
}

export interface BatchCloneResult {
  status: string;
  total_voices: number;
  providers: {
    [provider: string]: {
      count: number;
      voices: ClonedVoice[];
    };
  };
  started_at: string;
}

export interface UseClonedVoicesReturn {
  voices: ClonedVoice[];
  isLoading: boolean;
  error: string | null;
  fetchClonedVoices: (provider?: string, status?: string) => Promise<void>;
  getVoiceDetails: (voiceId: string, includeAudio?: boolean) => Promise<ClonedVoice | null>;
  batchCloneVoices: (providers?: string[], testText?: string) => Promise<BatchCloneResult | null>;
  deleteVoice: (voiceId: string) => Promise<boolean>;
  refreshVoices: () => Promise<void>;
}

export const useClonedVoices = (): UseClonedVoicesReturn => {
  const [voices, setVoices] = useState<ClonedVoice[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Fetch list of cloned voices
   */
  const fetchClonedVoices = useCallback(async (provider?: string, status?: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (provider) params.append('provider', provider);
      if (status) params.append('status', status);

      const url = `${API_BASE_URL}/api/voice-lab/voices/cloned${params.toString() ? `?${params.toString()}` : ''}`;

      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Failed to fetch voices: ${response.statusText}`);
      }

      const data: ClonedVoicesResponse = await response.json();
      setVoices(data.voices);

      return;
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to fetch cloned voices';
      setError(errorMessage);
      console.error('Error fetching cloned voices:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Get details for a specific voice
   */
  const getVoiceDetails = useCallback(async (
    voiceId: string,
    includeAudio: boolean = false
  ): Promise<ClonedVoice | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const url = `${API_BASE_URL}/api/voice-lab/voices/cloned/${voiceId}?include_audio=${includeAudio}`;

      const response = await fetch(url);

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Voice not found');
        }
        throw new Error(`Failed to fetch voice details: ${response.statusText}`);
      }

      const data: ClonedVoice = await response.json();
      return data;
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to fetch voice details';
      setError(errorMessage);
      console.error('Error fetching voice details:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Batch clone all Ghanaian voices
   */
  const batchCloneVoices = useCallback(async (
    providers?: string[],
    testText: string = 'Hello, this is a test of the cloned voice.'
  ): Promise<BatchCloneResult | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const url = `${API_BASE_URL}/api/voice-lab/voices/batch-clone`;

      const body: any = {
        test_text: testText
      };

      if (providers && providers.length > 0) {
        body.providers = providers;
      }

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Batch cloning failed');
      }

      const result: BatchCloneResult = await response.json();

      // Refresh voices list after cloning
      await fetchClonedVoices();

      return result;
    } catch (err: any) {
      const errorMessage = err.message || 'Batch cloning failed';
      setError(errorMessage);
      console.error('Error batch cloning voices:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [fetchClonedVoices]);

  /**
   * Delete a cloned voice
   */
  const deleteVoice = useCallback(async (voiceId: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      const url = `${API_BASE_URL}/api/voice-lab/voices/cloned/${voiceId}`;

      const response = await fetch(url, {
        method: 'DELETE',
      });

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Voice not found');
        }
        throw new Error(`Failed to delete voice: ${response.statusText}`);
      }

      // Refresh voices list after deletion
      await fetchClonedVoices();

      return true;
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to delete voice';
      setError(errorMessage);
      console.error('Error deleting voice:', err);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [fetchClonedVoices]);

  /**
   * Refresh voices list
   */
  const refreshVoices = useCallback(async () => {
    await fetchClonedVoices();
  }, [fetchClonedVoices]);

  // Load voices on mount
  useEffect(() => {
    fetchClonedVoices();
  }, [fetchClonedVoices]);

  return {
    voices,
    isLoading,
    error,
    fetchClonedVoices,
    getVoiceDetails,
    batchCloneVoices,
    deleteVoice,
    refreshVoices,
  };
};
