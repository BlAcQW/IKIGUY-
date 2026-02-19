/**
 * Custom hook for managing user voice preferences
 *
 * This hook handles loading, updating, and persisting voice settings
 * for TTS, ASR, and LLM services.
 *
 * @author KasaAI
 * @date 2025-11-03
 */

import { useState, useCallback, useEffect } from 'react';
import type {
  VoiceSettings,
  VoiceSettingsUpdateRequest,
  TTSSettings,
  ASRSettings,
  LLMSettings,
  VoicePreferences
} from '../types';

interface UseVoiceSettingsOptions {
  /**
   * API base URL. Defaults to env variable or localhost
   */
  apiBaseUrl?: string;

  /**
   * Auto-load settings on mount
   */
  autoLoad?: boolean;

  /**
   * Enable optimistic updates (update UI before server confirms)
   */
  optimisticUpdates?: boolean;
}

interface UseVoiceSettingsReturn {
  /** Current voice settings */
  settings: VoiceSettings | null;

  /** Loading state */
  isLoading: boolean;

  /** Error message if any */
  error: string | null;

  /** Whether settings have unsaved changes */
  isDirty: boolean;

  /** Load settings from server */
  loadSettings: () => Promise<void>;

  /** Update settings (partial update) */
  updateSettings: (updates: VoiceSettingsUpdateRequest) => Promise<void>;

  /** Save all settings to server */
  saveSettings: (settings: VoiceSettings) => Promise<void>;

  /** Reset to default settings */
  resetToDefaults: () => Promise<void>;

  /** Reset to organization defaults */
  resetToOrgDefaults: () => Promise<void>;

  /** Update TTS settings */
  updateTTSSettings: (tts: Partial<TTSSettings>) => void;

  /** Update ASR settings */
  updateASRSettings: (asr: Partial<ASRSettings>) => void;

  /** Update LLM settings */
  updateLLMSettings: (llm: Partial<LLMSettings>) => void;

  /** Update voice preferences */
  updateVoicePreferences: (voices: Partial<VoicePreferences>) => void;
}

/**
 * Default settings fallback
 */
const DEFAULT_SETTINGS: Omit<VoiceSettings, 'user_id' | 'organization_id'> = {
  tts: {
    default_provider: 'kokoro',
    default_voice: null,
    speed: 1.0,
    pitch: 0.0,
  },
  asr: {
    default_provider: 'faster_whisper_large',
    language: 'en',
    task: 'transcribe',
  },
  llm: {
    default_model: 'gemini-2.5-flash',
    temperature: 0.7,
    max_tokens: 2000,
  },
  voices: {
    favorite_voices: [],
    custom_voices: [],
  },
};

/**
 * Hook for managing voice settings
 *
 * @param userId - Current user ID
 * @param organizationId - Current organization ID
 * @param options - Configuration options
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { settings, updateTTSSettings, saveSettings } = useVoiceSettings(
 *     user.id,
 *     user.organization_id
 *   );
 *
 *   const handleProviderChange = (provider: string) => {
 *     updateTTSSettings({ default_provider: provider });
 *     saveSettings({ ...settings, tts: { ...settings.tts, default_provider: provider } });
 *   };
 * }
 * ```
 */
export const useVoiceSettings = (
  userId: string,
  organizationId: string,
  options: UseVoiceSettingsOptions = {}
): UseVoiceSettingsReturn => {
  const {
    apiBaseUrl = import.meta?.env?.VITE_API_URL || 'http://localhost:30027',
    autoLoad = true,
    optimisticUpdates = true,
  } = options;

  const [settings, setSettings] = useState<VoiceSettings | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDirty, setIsDirty] = useState(false);

  /**
   * Load settings from server
   */
  const loadSettings = useCallback(async () => {
    if (!userId || !organizationId) {
      setError('User ID and Organization ID are required');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiBaseUrl}/api/voice-settings/my-settings`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 404) {
          // No settings found, create defaults
          const defaultSettings: VoiceSettings = {
            ...DEFAULT_SETTINGS,
            user_id: userId,
            organization_id: organizationId,
          };
          setSettings(defaultSettings);
          return;
        }
        throw new Error(`Failed to load settings: ${response.statusText}`);
      }

      const data = await response.json();
      setSettings(data);
      setIsDirty(false);
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to load voice settings';
      setError(errorMessage);
      console.error('Error loading voice settings:', err);

      // Fallback to defaults on error
      setSettings({
        ...DEFAULT_SETTINGS,
        user_id: userId,
        organization_id: organizationId,
      });
    } finally {
      setIsLoading(false);
    }
  }, [userId, organizationId, apiBaseUrl]);

  /**
   * Update settings (partial update)
   */
  const updateSettings = useCallback(
    async (updates: VoiceSettingsUpdateRequest) => {
      if (!settings) {
        setError('No settings loaded');
        return;
      }

      setIsLoading(true);
      setError(null);

      // Optimistic update
      if (optimisticUpdates) {
        const optimisticSettings = {
          ...settings,
          ...updates,
          tts: updates.tts ? { ...settings.tts, ...updates.tts } : settings.tts,
          asr: updates.asr ? { ...settings.asr, ...updates.asr } : settings.asr,
          llm: updates.llm ? { ...settings.llm, ...updates.llm } : settings.llm,
          voices: updates.voices ? { ...settings.voices, ...updates.voices } : settings.voices,
        };
        setSettings(optimisticSettings);
      }

      try {
        const response = await fetch(`${apiBaseUrl}/api/voice-settings/my-settings`, {
          method: 'PUT',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(updates),
        });

        if (!response.ok) {
          throw new Error(`Failed to update settings: ${response.statusText}`);
        }

        const updatedSettings = await response.json();
        setSettings(updatedSettings);
        setIsDirty(false);
      } catch (err: any) {
        const errorMessage = err.message || 'Failed to update voice settings';
        setError(errorMessage);
        console.error('Error updating voice settings:', err);

        // Revert optimistic update
        await loadSettings();
      } finally {
        setIsLoading(false);
      }
    },
    [settings, apiBaseUrl, optimisticUpdates, loadSettings]
  );

  /**
   * Save complete settings
   */
  const saveSettings = useCallback(
    async (newSettings: VoiceSettings) => {
      await updateSettings({
        tts: newSettings.tts,
        asr: newSettings.asr,
        llm: newSettings.llm,
        voices: newSettings.voices,
      });
    },
    [updateSettings]
  );

  /**
   * Reset to default settings
   */
  const resetToDefaults = useCallback(async () => {
    if (!userId || !organizationId) return;

    const defaultSettings: VoiceSettings = {
      ...DEFAULT_SETTINGS,
      user_id: userId,
      organization_id: organizationId,
    };

    await saveSettings(defaultSettings);
  }, [userId, organizationId, saveSettings]);

  /**
   * Reset to organization defaults
   */
  const resetToOrgDefaults = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiBaseUrl}/api/voice-settings/org-defaults`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to load org defaults: ${response.statusText}`);
      }

      const orgDefaults = await response.json();
      await saveSettings({
        ...orgDefaults,
        user_id: userId,
        organization_id: organizationId,
      });
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to load organization defaults';
      setError(errorMessage);
      console.error('Error loading organization defaults:', err);
    } finally {
      setIsLoading(false);
    }
  }, [apiBaseUrl, userId, organizationId, saveSettings]);

  /**
   * Update TTS settings locally (marks as dirty)
   */
  const updateTTSSettings = useCallback(
    (tts: Partial<TTSSettings>) => {
      if (!settings) return;

      setSettings({
        ...settings,
        tts: { ...settings.tts, ...tts },
      });
      setIsDirty(true);
    },
    [settings]
  );

  /**
   * Update ASR settings locally (marks as dirty)
   */
  const updateASRSettings = useCallback(
    (asr: Partial<ASRSettings>) => {
      if (!settings) return;

      setSettings({
        ...settings,
        asr: { ...settings.asr, ...asr },
      });
      setIsDirty(true);
    },
    [settings]
  );

  /**
   * Update LLM settings locally (marks as dirty)
   */
  const updateLLMSettings = useCallback(
    (llm: Partial<LLMSettings>) => {
      if (!settings) return;

      setSettings({
        ...settings,
        llm: { ...settings.llm, ...llm },
      });
      setIsDirty(true);
    },
    [settings]
  );

  /**
   * Update voice preferences locally (marks as dirty)
   */
  const updateVoicePreferences = useCallback(
    (voices: Partial<VoicePreferences>) => {
      if (!settings) return;

      setSettings({
        ...settings,
        voices: { ...settings.voices, ...voices },
      });
      setIsDirty(true);
    },
    [settings]
  );

  /**
   * Auto-load settings on mount
   */
  useEffect(() => {
    if (autoLoad && userId && organizationId) {
      loadSettings();
    }
  }, [autoLoad, userId, organizationId, loadSettings]);

  return {
    settings,
    isLoading,
    error,
    isDirty,
    loadSettings,
    updateSettings,
    saveSettings,
    resetToDefaults,
    resetToOrgDefaults,
    updateTTSSettings,
    updateASRSettings,
    updateLLMSettings,
    updateVoicePreferences,
  };
};
