/**
 * Unit Tests for useVoiceSettings Hook
 *
 * Tests voice settings management including:
 * - Loading settings
 * - Updating settings
 * - Saving settings
 * - Resetting to defaults
 * - Dirty state tracking
 * - Optimistic updates
 * - Error handling
 *
 * @author KasaAI
 * @date 2025-11-03
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useVoiceSettings } from '../../hooks/useVoiceSettings';
import type { VoiceSettings } from '../../types';

// Mock settings data
const mockSettings: VoiceSettings = {
  user_id: 'user_001',
  organization_id: 'org_001',
  tts: {
    default_provider: 'coqui_xtts',
    default_voice: null,
    speed: 1.0,
    pitch: 0.0,
  },
  asr: {
    default_provider: 'whisper_local',
    language: 'en',
    task: 'transcribe',
  },
  llm: {
    default_model: 'llama3.2',
    temperature: 0.7,
    max_tokens: 2000,
  },
  voices: {
    favorite_voices: [],
    custom_voices: [],
  },
};

const mockUpdatedSettings: VoiceSettings = {
  ...mockSettings,
  tts: {
    ...mockSettings.tts,
    speed: 1.5,
  },
};

describe('useVoiceSettings', () => {
  beforeEach(() => {
    // Reset fetch mock before each test
    vi.resetAllMocks();
    global.fetch = vi.fn();
  });

  describe('Initial Loading', () => {
    it('should load settings on mount when autoLoad is true', async () => {
      // Mock successful fetch
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockSettings,
      } as Response);

      const { result } = renderHook(() =>
        useVoiceSettings('user_001', 'org_001', { autoLoad: true })
      );

      // Initially loading
      expect(result.current.isLoading).toBe(false);

      // Wait for settings to load
      await waitFor(() => {
        expect(result.current.settings).toEqual(mockSettings);
      });

      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(result.current.isDirty).toBe(false);
    });

    it('should not auto-load settings when autoLoad is false', async () => {
      const { result } = renderHook(() =>
        useVoiceSettings('user_001', 'org_001', { autoLoad: false })
      );

      expect(result.current.settings).toBeNull();
      expect(result.current.isLoading).toBe(false);
      expect(global.fetch).not.toHaveBeenCalled();
    });

    it('should handle 404 by creating default settings', async () => {
      // Mock 404 response
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
      } as Response);

      const { result } = renderHook(() =>
        useVoiceSettings('user_001', 'org_001')
      );

      await waitFor(() => {
        expect(result.current.settings).toBeTruthy();
      });

      expect(result.current.settings?.user_id).toBe('user_001');
      expect(result.current.settings?.organization_id).toBe('org_001');
      expect(result.current.settings?.tts.default_provider).toBe('coqui_xtts');
    });

    it('should handle fetch errors gracefully', async () => {
      // Mock network error
      global.fetch = vi.fn().mockRejectedValueOnce(new Error('Network error'));

      const { result } = renderHook(() =>
        useVoiceSettings('user_001', 'org_001')
      );

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
      });

      expect(result.current.error).toContain('Network error');
      // Should still provide default settings as fallback
      expect(result.current.settings).toBeTruthy();
    });
  });

  describe('Manual Loading', () => {
    it('should load settings manually via loadSettings', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockSettings,
      } as Response);

      const { result } = renderHook(() =>
        useVoiceSettings('user_001', 'org_001', { autoLoad: false })
      );

      expect(result.current.settings).toBeNull();

      // Manually load settings
      await act(async () => {
        await result.current.loadSettings();
      });

      expect(result.current.settings).toEqual(mockSettings);
      expect(result.current.isLoading).toBe(false);
    });

    it('should handle missing user ID gracefully', async () => {
      const { result } = renderHook(() =>
        useVoiceSettings('', '', { autoLoad: false })
      );

      await act(async () => {
        await result.current.loadSettings();
      });

      expect(result.current.error).toBeTruthy();
      expect(result.current.error).toContain('User ID and Organization ID are required');
    });
  });

  describe('Updating Settings', () => {
    it('should update TTS settings locally and mark as dirty', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockSettings,
      } as Response);

      const { result } = renderHook(() =>
        useVoiceSettings('user_001', 'org_001')
      );

      await waitFor(() => {
        expect(result.current.settings).toEqual(mockSettings);
      });

      // Update TTS settings
      act(() => {
        result.current.updateTTSSettings({ speed: 1.5 });
      });

      expect(result.current.settings?.tts.speed).toBe(1.5);
      expect(result.current.isDirty).toBe(true);
    });

    it('should update ASR settings locally and mark as dirty', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockSettings,
      } as Response);

      const { result } = renderHook(() =>
        useVoiceSettings('user_001', 'org_001')
      );

      await waitFor(() => {
        expect(result.current.settings).toEqual(mockSettings);
      });

      // Update ASR settings
      act(() => {
        result.current.updateASRSettings({ language: 'es' });
      });

      expect(result.current.settings?.asr.language).toBe('es');
      expect(result.current.isDirty).toBe(true);
    });

    it('should update LLM settings locally and mark as dirty', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockSettings,
      } as Response);

      const { result } = renderHook(() =>
        useVoiceSettings('user_001', 'org_001')
      );

      await waitFor(() => {
        expect(result.current.settings).toEqual(mockSettings);
      });

      // Update LLM settings
      act(() => {
        result.current.updateLLMSettings({ temperature: 0.9 });
      });

      expect(result.current.settings?.llm.temperature).toBe(0.9);
      expect(result.current.isDirty).toBe(true);
    });

    it('should update voice preferences locally and mark as dirty', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockSettings,
      } as Response);

      const { result } = renderHook(() =>
        useVoiceSettings('user_001', 'org_001')
      );

      await waitFor(() => {
        expect(result.current.settings).toEqual(mockSettings);
      });

      // Update voice preferences
      act(() => {
        result.current.updateVoicePreferences({
          favorite_voices: ['voice_001', 'voice_002'],
        });
      });

      expect(result.current.settings?.voices.favorite_voices).toEqual([
        'voice_001',
        'voice_002',
      ]);
      expect(result.current.isDirty).toBe(true);
    });
  });

  describe('Saving Settings', () => {
    it('should save settings to server and clear dirty flag', async () => {
      // Mock initial load
      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockSettings,
        } as Response)
        // Mock update
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockUpdatedSettings,
        } as Response);

      const { result } = renderHook(() =>
        useVoiceSettings('user_001', 'org_001')
      );

      await waitFor(() => {
        expect(result.current.settings).toEqual(mockSettings);
      });

      // Update settings
      await act(async () => {
        await result.current.updateSettings({ tts: { speed: 1.5 } });
      });

      expect(result.current.settings?.tts.speed).toBe(1.5);
      expect(result.current.isDirty).toBe(false); // Should be cleared after save
    });

    it('should perform optimistic updates when enabled', async () => {
      // Mock initial load
      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockSettings,
        } as Response)
        // Mock delayed update to test optimistic update
        .mockImplementationOnce(
          () =>
            new Promise((resolve) =>
              setTimeout(
                () =>
                  resolve({
                    ok: true,
                    json: async () => mockUpdatedSettings,
                  } as Response),
                100
              )
            )
        );

      const { result } = renderHook(() =>
        useVoiceSettings('user_001', 'org_001', { optimisticUpdates: true })
      );

      await waitFor(() => {
        expect(result.current.settings).toEqual(mockSettings);
      });

      // Update settings
      act(() => {
        result.current.updateSettings({ tts: { speed: 1.5 } });
      });

      // Should immediately show optimistic update
      expect(result.current.settings?.tts.speed).toBe(1.5);

      // Wait for server response
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
    });

    it('should revert optimistic updates on error', async () => {
      // Mock initial load
      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockSettings,
        } as Response)
        // Mock failed update
        .mockRejectedValueOnce(new Error('Update failed'))
        // Mock successful reload
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockSettings,
        } as Response);

      const { result } = renderHook(() =>
        useVoiceSettings('user_001', 'org_001', { optimisticUpdates: true })
      );

      await waitFor(() => {
        expect(result.current.settings).toEqual(mockSettings);
      });

      // Attempt to update settings (will fail)
      await act(async () => {
        await result.current.updateSettings({ tts: { speed: 1.5 } });
      });

      // Should revert to original settings
      await waitFor(() => {
        expect(result.current.settings?.tts.speed).toBe(1.0);
      });

      expect(result.current.error).toBeTruthy();
    });

    it('should handle update without loaded settings', async () => {
      const { result } = renderHook(() =>
        useVoiceSettings('user_001', 'org_001', { autoLoad: false })
      );

      await act(async () => {
        await result.current.updateSettings({ tts: { speed: 1.5 } });
      });

      expect(result.current.error).toContain('No settings loaded');
    });
  });

  describe('Reset Functionality', () => {
    it('should reset to default settings', async () => {
      // Mock initial load
      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockUpdatedSettings,
        } as Response)
        // Mock reset to defaults
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockSettings,
        } as Response);

      const { result } = renderHook(() =>
        useVoiceSettings('user_001', 'org_001')
      );

      await waitFor(() => {
        expect(result.current.settings).toBeTruthy();
      });

      // Reset to defaults
      await act(async () => {
        await result.current.resetToDefaults();
      });

      // Should have default settings
      expect(result.current.settings?.tts.default_provider).toBe('coqui_xtts');
      expect(result.current.settings?.tts.speed).toBe(1.0);
    });

    it('should reset to organization defaults', async () => {
      const orgDefaults = {
        ...mockSettings,
        tts: {
          ...mockSettings.tts,
          default_provider: 'openai_tts',
          speed: 1.2,
        },
      };

      // Mock initial load
      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockSettings,
        } as Response)
        // Mock org defaults fetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => orgDefaults,
        } as Response)
        // Mock save
        .mockResolvedValueOnce({
          ok: true,
          json: async () => orgDefaults,
        } as Response);

      const { result } = renderHook(() =>
        useVoiceSettings('user_001', 'org_001')
      );

      await waitFor(() => {
        expect(result.current.settings).toEqual(mockSettings);
      });

      // Reset to org defaults
      await act(async () => {
        await result.current.resetToOrgDefaults();
      });

      await waitFor(() => {
        expect(result.current.settings?.tts.default_provider).toBe('openai_tts');
      });
    });

    it('should handle org defaults fetch error', async () => {
      // Mock initial load
      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockSettings,
        } as Response)
        // Mock org defaults fetch error
        .mockRejectedValueOnce(new Error('Failed to load org defaults'));

      const { result } = renderHook(() =>
        useVoiceSettings('user_001', 'org_001')
      );

      await waitFor(() => {
        expect(result.current.settings).toEqual(mockSettings);
      });

      // Try to reset to org defaults
      await act(async () => {
        await result.current.resetToOrgDefaults();
      });

      expect(result.current.error).toBeTruthy();
      expect(result.current.error).toContain('Failed to load organization defaults');
    });
  });

  describe('Error Handling', () => {
    it('should set error state on failed fetch', async () => {
      global.fetch = vi.fn().mockRejectedValueOnce(new Error('Network failure'));

      const { result } = renderHook(() =>
        useVoiceSettings('user_001', 'org_001')
      );

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
      });

      expect(result.current.error).toContain('Network failure');
      expect(result.current.isLoading).toBe(false);
    });

    it('should handle server errors (non-404)', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      } as Response);

      const { result } = renderHook(() =>
        useVoiceSettings('user_001', 'org_001')
      );

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
      });

      expect(result.current.error).toContain('Failed to load settings');
    });
  });

  describe('State Management', () => {
    it('should track dirty state correctly', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockSettings,
      } as Response);

      const { result } = renderHook(() =>
        useVoiceSettings('user_001', 'org_001')
      );

      await waitFor(() => {
        expect(result.current.settings).toEqual(mockSettings);
      });

      // Initially not dirty
      expect(result.current.isDirty).toBe(false);

      // Make a change
      act(() => {
        result.current.updateTTSSettings({ speed: 1.5 });
      });

      // Should be dirty now
      expect(result.current.isDirty).toBe(true);
    });

    it('should preserve settings immutability on partial updates', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockSettings,
      } as Response);

      const { result } = renderHook(() =>
        useVoiceSettings('user_001', 'org_001')
      );

      await waitFor(() => {
        expect(result.current.settings).toEqual(mockSettings);
      });

      const originalAsrSettings = result.current.settings?.asr;

      // Update only TTS
      act(() => {
        result.current.updateTTSSettings({ speed: 1.5 });
      });

      // ASR settings should remain unchanged
      expect(result.current.settings?.asr).toEqual(originalAsrSettings);
    });
  });
});
