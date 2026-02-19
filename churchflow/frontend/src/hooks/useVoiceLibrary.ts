/**
 * Voice Library Hook
 *
 * Custom hook for interacting with the centralized voice library API.
 * Provides CRUD operations for voices, favorites, and ratings.
 */

import { useState, useCallback } from 'react';
import { CORE_API_URL as API_BASE_URL } from '@/config/api-config';
import { getAuthHeaders } from '@/lib/auth-utils';

// Types matching the backend API
export interface VoiceCharacteristics {
  gender?: 'male' | 'female' | 'neutral' | 'unknown';
  language?: string;
  accent?: string;
  dialect?: string;
  tone?: string;
  pace?: string;
  age_range?: string;
}

export interface VoiceMetadata {
  tags?: string[];
  categories?: string[];
  use_cases?: string[];
  featured?: boolean;
  verified?: boolean;
}

export interface VoiceFile {
  path: string;
  url?: string;
  size: number;
  format: string;
  duration?: number;
  sample_rate?: number;
}

export interface VoiceLibraryItem {
  voice_id: string;
  name: string;
  description?: string;
  characteristics?: VoiceCharacteristics;
  metadata?: VoiceMetadata;
  files?: {
    reference?: VoiceFile;
    preview?: VoiceFile;
    full?: VoiceFile;
  };
  stats?: {
    views: number;
    uses: number;
    favorites: number;
    rating?: {
      average: number;
      count: number;
    };
  };
  status: string;
  created_at: string;
  updated_at: string;
}

export interface VoiceFilters {
  search?: string;
  gender?: string;
  language?: string;
  accent?: string;
  visibility?: string;
  tags?: string;
  categories?: string;
  use_cases?: string;
  featured?: boolean;
  verified?: boolean;
}

export interface VoiceListResponse {
  success: boolean;
  message: string;
  voices: VoiceLibraryItem[];
  total: number;
  skip: number;
  limit: number;
}

export interface VoiceResponse {
  success: boolean;
  message: string;
  voice?: VoiceLibraryItem;
}

export const useVoiceLibrary = () => {
  const [voices, setVoices] = useState<VoiceLibraryItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  /**
   * Fetch voices from the library with optional filters
   */
  const fetchVoices = useCallback(async (filters?: VoiceFilters, skip = 0, limit = 100) => {
    setIsLoading(true);
    setError(null);

    try {
      // Build query parameters
      const params = new URLSearchParams();
      if (skip) params.append('skip', skip.toString());
      if (limit) params.append('limit', limit.toString());

      if (filters) {
        if (filters.search) params.append('search', filters.search);
        if (filters.gender) params.append('gender', filters.gender);
        if (filters.language) params.append('language', filters.language);
        if (filters.accent) params.append('accent', filters.accent);
        if (filters.visibility) params.append('visibility', filters.visibility);
        if (filters.tags) params.append('tags', filters.tags);
        if (filters.categories) params.append('categories', filters.categories);
        if (filters.use_cases) params.append('use_cases', filters.use_cases);
        if (filters.featured !== undefined) params.append('featured', filters.featured.toString());
        if (filters.verified !== undefined) params.append('verified', filters.verified.toString());
      }

      const authHeaders = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/api/voice-library/?${params}`, {
        headers: authHeaders,
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch voices: ${response.statusText}`);
      }

      const data: VoiceListResponse = await response.json();

      setVoices(data.voices);
      setTotal(data.total);

      return data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch voices';
      setError(errorMessage);
      console.error('Error fetching voices:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Get a single voice by ID
   */
  const getVoice = useCallback(async (voiceId: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const authHeaders = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/api/voice-library/${voiceId}`, {
        headers: authHeaders,
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch voice: ${response.statusText}`);
      }

      const data: VoiceResponse = await response.json();
      return data.voice;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch voice';
      setError(errorMessage);
      console.error('Error fetching voice:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Create a new voice with audio upload
   */
  const createVoice = useCallback(async (
    voiceData: {
      name: string;
      description?: string;
      gender?: string;
      language?: string;
      accent?: string;
      dialect?: string;
      tone?: string;
      pace?: string;
      age_range?: string;
      visibility?: string;
      tags?: string[];
      categories?: string[];
      use_cases?: string[];
    },
    audioFile: File
  ) => {
    setIsLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('audio_file', audioFile);
      formData.append('name', voiceData.name);

      if (voiceData.description) formData.append('description', voiceData.description);
      if (voiceData.gender) formData.append('gender', voiceData.gender);
      if (voiceData.language) formData.append('language', voiceData.language);
      if (voiceData.accent) formData.append('accent', voiceData.accent);
      if (voiceData.dialect) formData.append('dialect', voiceData.dialect);
      if (voiceData.tone) formData.append('tone', voiceData.tone);
      if (voiceData.pace) formData.append('pace', voiceData.pace);
      if (voiceData.age_range) formData.append('age_range', voiceData.age_range);
      if (voiceData.visibility) formData.append('visibility', voiceData.visibility);
      if (voiceData.tags) formData.append('tags', voiceData.tags.join(','));
      if (voiceData.categories) formData.append('categories', voiceData.categories.join(','));
      if (voiceData.use_cases) formData.append('use_cases', voiceData.use_cases.join(','));

      const authHeaders = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/api/voice-library/`, {
        method: 'POST',
        headers: authHeaders,
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Failed to create voice: ${response.statusText}`);
      }

      const data: VoiceResponse = await response.json();

      // Refresh voices list
      await fetchVoices();

      return data.voice;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create voice';
      setError(errorMessage);
      console.error('Error creating voice:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [user, fetchVoices]);

  /**
   * Update voice metadata
   */
  const updateVoice = useCallback(async (voiceId: string, updates: Partial<VoiceLibraryItem>) => {
    setIsLoading(true);
    setError(null);

    try {
      const authHeaders = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/api/voice-library/${voiceId}`, {
        method: 'PATCH',
        headers: {
          ...authHeaders,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates),
      });

      if (!response.ok) {
        throw new Error(`Failed to update voice: ${response.statusText}`);
      }

      const data: VoiceResponse = await response.json();

      // Update local state
      setVoices(prev => prev.map(v => v.voice_id === voiceId ? data.voice! : v));

      return data.voice;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update voice';
      setError(errorMessage);
      console.error('Error updating voice:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Delete a voice
   */
  const deleteVoice = useCallback(async (voiceId: string, hardDelete = false) => {
    setIsLoading(true);
    setError(null);

    try {
      const authHeaders = await getAuthHeaders();
      const response = await fetch(
        `${API_BASE_URL}/api/voice-library/${voiceId}?soft_delete=${!hardDelete}`,
        {
          method: 'DELETE',
          headers: authHeaders,
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to delete voice: ${response.statusText}`);
      }

      // Remove from local state
      setVoices(prev => prev.filter(v => v.voice_id !== voiceId));

      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete voice';
      setError(errorMessage);
      console.error('Error deleting voice:', err);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Add voice to favorites
   */
  const addToFavorites = useCallback(async (voiceId: string) => {
    try {
      const authHeaders = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/api/voice-library/favorites/add`, {
        method: 'POST',
        headers: {
          ...authHeaders,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ voice_id: voiceId }),
      });

      if (!response.ok) {
        throw new Error(`Failed to add to favorites: ${response.statusText}`);
      }

      return true;
    } catch (err) {
      console.error('Error adding to favorites:', err);
      return false;
    }
  }, []);

  /**
   * Remove voice from favorites
   */
  const removeFromFavorites = useCallback(async (voiceId: string) => {
    try {
      const authHeaders = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/api/voice-library/favorites/remove`, {
        method: 'POST',
        headers: {
          ...authHeaders,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ voice_id: voiceId }),
      });

      if (!response.ok) {
        throw new Error(`Failed to remove from favorites: ${response.statusText}`);
      }

      return true;
    } catch (err) {
      console.error('Error removing from favorites:', err);
      return false;
    }
  }, []);

  /**
   * Get user's favorite voices
   */
  const getFavorites = useCallback(async (skip = 0, limit = 100) => {
    try {
      const authHeaders = await getAuthHeaders();
      const response = await fetch(
        `${API_BASE_URL}/api/voice-library/favorites/list?skip=${skip}&limit=${limit}`,
        {
          headers: authHeaders,
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch favorites: ${response.statusText}`);
      }

      const data: VoiceListResponse = await response.json();
      return data.voices;
    } catch (err) {
      console.error('Error fetching favorites:', err);
      return [];
    }
  }, []);

  /**
   * Rate a voice
   */
  const rateVoice = useCallback(async (voiceId: string, rating: number, review?: string) => {
    try {
      const authHeaders = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/api/voice-library/ratings/add`, {
        method: 'POST',
        headers: {
          ...authHeaders,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ voice_id: voiceId, rating, review }),
      });

      if (!response.ok) {
        throw new Error(`Failed to rate voice: ${response.statusText}`);
      }

      return true;
    } catch (err) {
      console.error('Error rating voice:', err);
      return false;
    }
  }, []);

  /**
   * Record voice usage for analytics
   */
  const recordUsage = useCallback(async (voiceId: string) => {
    try {
      const authHeaders = await getAuthHeaders();
      await fetch(`${API_BASE_URL}/api/voice-library/${voiceId}/use`, {
        method: 'POST',
        headers: authHeaders,
      });
    } catch (err) {
      console.error('Error recording usage:', err);
    }
  }, []);

  return {
    voices,
    isLoading,
    error,
    total,
    fetchVoices,
    getVoice,
    createVoice,
    updateVoice,
    deleteVoice,
    addToFavorites,
    removeFromFavorites,
    getFavorites,
    rateVoice,
    recordUsage,
  };
};
