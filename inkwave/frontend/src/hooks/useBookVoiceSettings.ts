/**
 * Hook for managing book-level voice settings.
 *
 * Provides an interface to get, update, and clear voice settings for a specific book.
 * Settings persist across sessions and override user defaults.
 */

import { useState, useEffect, useCallback } from 'react';
import { INKWAVE_API_URL } from '../config/api-config';

export interface BookVoiceSettings {
  // TTS Settings
  tts_provider?: string;
  tts_voice?: string;
  tts_speed?: number;
  tts_pitch?: number;

  // ASR Settings
  asr_provider?: string;
  asr_language?: string;
  asr_task?: string;

  // LLM Settings
  llm_provider?: string;
  llm_model?: string;
  llm_temperature?: number;
  llm_max_tokens?: number;
  system_prompt?: string;

  // Metadata
  applied_at?: string;
  source?: string;
}

export interface BookVoiceSettingsResponse {
  book_id: string;
  voice_settings: BookVoiceSettings | null;
  has_settings: boolean;
}

export interface UseBookVoiceSettingsReturn {
  settings: BookVoiceSettings | null;
  hasSettings: boolean;
  loading: boolean;
  error: string | null;
  updateSettings: (updates: Partial<BookVoiceSettings>) => Promise<void>;
  clearSettings: () => Promise<void>;
  refreshSettings: () => Promise<void>;
}

/**
 * Hook to manage book-level voice settings.
 *
 * @param bookId - The book identifier
 * @returns Settings state and management functions
 */
export function useBookVoiceSettings(bookId: string): UseBookVoiceSettingsReturn {
  const [settings, setSettings] = useState<BookVoiceSettings | null>(null);
  const [hasSettings, setHasSettings] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Get the auth token from localStorage.
   */
  const getAuthToken = useCallback((): string | null => {
    return localStorage.getItem('access_token');
  }, []);

  /**
   * Fetch settings from the API.
   */
  const fetchSettings = useCallback(async () => {
    if (!bookId) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const token = getAuthToken();
      if (!token) {
        throw new Error('Authentication required');
      }

      const response = await fetch(
        `${INKWAVE_API_URL}/books/${bookId}/voice-settings`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch settings: ${response.statusText}`);
      }

      const data: BookVoiceSettingsResponse = await response.json();
      setSettings(data.voice_settings);
      setHasSettings(data.has_settings);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      console.error('Failed to fetch book voice settings:', err);
    } finally {
      setLoading(false);
    }
  }, [bookId, getAuthToken]);

  /**
   * Update settings via the API.
   */
  const updateSettings = useCallback(async (updates: Partial<BookVoiceSettings>) => {
    if (!bookId) {
      throw new Error('Book ID is required');
    }

    setLoading(true);
    setError(null);

    try {
      const token = getAuthToken();
      if (!token) {
        throw new Error('Authentication required');
      }

      const response = await fetch(
        `${INKWAVE_API_URL}/books/${bookId}/voice-settings`,
        {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(updates),
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to update settings: ${response.statusText}`);
      }

      const data = await response.json();
      setSettings(data.voice_settings);
      setHasSettings(true);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      console.error('Failed to update book voice settings:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [bookId, getAuthToken]);

  /**
   * Clear settings via the API (revert to user defaults).
   */
  const clearSettings = useCallback(async () => {
    if (!bookId) {
      throw new Error('Book ID is required');
    }

    setLoading(true);
    setError(null);

    try {
      const token = getAuthToken();
      if (!token) {
        throw new Error('Authentication required');
      }

      const response = await fetch(
        `${INKWAVE_API_URL}/books/${bookId}/voice-settings`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to clear settings: ${response.statusText}`);
      }

      setSettings(null);
      setHasSettings(false);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      console.error('Failed to clear book voice settings:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [bookId, getAuthToken]);

  /**
   * Refresh settings (alias for fetchSettings).
   */
  const refreshSettings = useCallback(async () => {
    await fetchSettings();
  }, [fetchSettings]);

  // Load settings on mount and when bookId changes
  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  return {
    settings,
    hasSettings,
    loading,
    error,
    updateSettings,
    clearSettings,
    refreshSettings,
  };
}
