/**
 * Unit tests for useBookVoiceSettings hook.
 *
 * Tests the hook's ability to fetch, update, and clear book voice settings.
 */

import { renderHook, waitFor } from '@testing-library/react';
import { act } from 'react-dom/test-utils';
import { useBookVoiceSettings } from './useBookVoiceSettings';

// Mock fetch
global.fetch = jest.fn();

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

describe('useBookVoiceSettings', () => {
  const mockToken = 'test_token_123';
  const mockBookId = 'book_123';

  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(mockToken);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('should fetch settings on mount', async () => {
    const mockSettings = {
      book_id: mockBookId,
      voice_settings: {
        llm_provider: 'openai',
        llm_model: 'gpt-4o-mini',
        llm_temperature: 0.8,
      },
      has_settings: true,
    };

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockSettings,
    });

    const { result } = renderHook(() => useBookVoiceSettings(mockBookId));

    // Initially loading
    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Verify fetch was called correctly
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining(`/books/${mockBookId}/voice-settings`),
      expect.objectContaining({
        headers: expect.objectContaining({
          'Authorization': `Bearer ${mockToken}`,
        }),
      })
    );

    // Verify settings are set
    expect(result.current.settings).toEqual(mockSettings.voice_settings);
    expect(result.current.hasSettings).toBe(true);
    expect(result.current.error).toBeNull();
  });

  it('should handle fetch error', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      statusText: 'Not Found',
    });

    const { result } = renderHook(() => useBookVoiceSettings(mockBookId));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toContain('Failed to fetch settings');
  });

  it('should handle missing auth token', async () => {
    localStorageMock.getItem.mockReturnValueOnce(null);

    const { result } = renderHook(() => useBookVoiceSettings(mockBookId));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toContain('Authentication required');
  });

  it('should update settings successfully', async () => {
    const initialSettings = {
      book_id: mockBookId,
      voice_settings: {
        llm_provider: 'gemini',
        llm_model: 'gemini-2.5-flash',
      },
      has_settings: true,
    };

    const updatedSettings = {
      voice_settings: {
        llm_provider: 'openai',
        llm_model: 'gpt-4o-mini',
        llm_temperature: 0.8,
      },
    };

    // Mock initial fetch
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => initialSettings,
    });

    const { result } = renderHook(() => useBookVoiceSettings(mockBookId));

    await waitFor(() => {
      expect(result.current.settings).toEqual(initialSettings.voice_settings);
    });

    // Mock update request
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => updatedSettings,
    });

    // Perform update
    await act(async () => {
      await result.current.updateSettings({
        llm_provider: 'openai',
        llm_model: 'gpt-4o-mini',
        llm_temperature: 0.8,
      });
    });

    // Verify PUT request was made
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining(`/books/${mockBookId}/voice-settings`),
      expect.objectContaining({
        method: 'PUT',
        headers: expect.objectContaining({
          'Authorization': `Bearer ${mockToken}`,
          'Content-Type': 'application/json',
        }),
        body: expect.stringContaining('openai'),
      })
    );

    // Verify settings were updated
    expect(result.current.settings).toEqual(updatedSettings.voice_settings);
    expect(result.current.hasSettings).toBe(true);
  });

  it('should clear settings successfully', async () => {
    const initialSettings = {
      book_id: mockBookId,
      voice_settings: {
        llm_provider: 'openai',
        llm_model: 'gpt-4o-mini',
      },
      has_settings: true,
    };

    // Mock initial fetch
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => initialSettings,
    });

    const { result } = renderHook(() => useBookVoiceSettings(mockBookId));

    await waitFor(() => {
      expect(result.current.hasSettings).toBe(true);
    });

    // Mock clear request
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ message: 'Settings cleared' }),
    });

    // Perform clear
    await act(async () => {
      await result.current.clearSettings();
    });

    // Verify DELETE request was made
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining(`/books/${mockBookId}/voice-settings`),
      expect.objectContaining({
        method: 'DELETE',
        headers: expect.objectContaining({
          'Authorization': `Bearer ${mockToken}`,
        }),
      })
    );

    // Verify settings were cleared
    expect(result.current.settings).toBeNull();
    expect(result.current.hasSettings).toBe(false);
  });

  it('should refresh settings', async () => {
    const settings = {
      book_id: mockBookId,
      voice_settings: {
        llm_provider: 'gemini',
      },
      has_settings: true,
    };

    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => settings,
    });

    const { result } = renderHook(() => useBookVoiceSettings(mockBookId));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Clear mock calls from initial fetch
    (global.fetch as jest.Mock).mockClear();

    // Call refresh
    await act(async () => {
      await result.current.refreshSettings();
    });

    // Verify fetch was called again
    expect(global.fetch).toHaveBeenCalledTimes(1);
  });

  it('should handle update error', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ book_id: mockBookId, voice_settings: null, has_settings: false }),
    });

    const { result } = renderHook(() => useBookVoiceSettings(mockBookId));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Mock failed update
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      statusText: 'Internal Server Error',
    });

    // Attempt update - should throw
    await expect(async () => {
      await act(async () => {
        await result.current.updateSettings({ llm_provider: 'openai' });
      });
    }).rejects.toThrow();

    expect(result.current.error).toContain('Failed to update settings');
  });

  it('should handle LLM configuration fields', async () => {
    const llmSettings = {
      book_id: mockBookId,
      voice_settings: {
        llm_provider: 'anthropic',
        llm_model: 'claude-3-5-sonnet-20241022',
        llm_temperature: 0.7,
        system_prompt: 'Custom prompt',
        tts_provider: 'kokoro',
        tts_voice: 'am_adam',
      },
      has_settings: true,
    };

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => llmSettings,
    });

    const { result } = renderHook(() => useBookVoiceSettings(mockBookId));

    await waitFor(() => {
      expect(result.current.settings).toEqual(llmSettings.voice_settings);
    });

    // Verify all LLM fields are accessible
    expect(result.current.settings?.llm_provider).toBe('anthropic');
    expect(result.current.settings?.llm_model).toBe('claude-3-5-sonnet-20241022');
    expect(result.current.settings?.llm_temperature).toBe(0.7);
    expect(result.current.settings?.system_prompt).toBe('Custom prompt');
  });
});
