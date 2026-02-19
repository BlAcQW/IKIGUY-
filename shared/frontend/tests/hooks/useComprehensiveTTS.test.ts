/**
 * Integration Tests for useComprehensiveTTS Hook
 *
 * Tests TTS provider management including:
 * - Provider fetching from backend API
 * - Synthesis via hook methods
 * - Real-time health status updates
 * - Error handling and retries
 *
 * Phase 3.6 of TTS System Consolidation
 *
 * @author KasaAI
 * @date 2025-11-23
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useComprehensiveTTS } from '../../hooks/useComprehensiveTTS';
import type { TTSProviderInfo } from '../../types/tts';

// Mock provider data
const mockProviders: TTSProviderInfo[] = [
  {
    id: 'coqui_xtts',
    name: 'Coqui XTTS',
    description: 'Multilingual TTS with voice cloning',
    status: 'online',
    endpoint: 'https://ttslab.ailabsafrica.com/coqui_xtts',
    capabilities: {
      streaming: false,
      cloning: true,
      emotions: false,
      multilingual: true,
      speed_control: true,
      pitch_control: true,
    },
    supported_languages: ['en', 'es', 'fr', 'de', 'it', 'pt', 'pl', 'tr', 'ru', 'nl', 'cs', 'ar', 'zh', 'ja', 'hu', 'ko', 'hi'],
    voices: [
      { voice_id: 'default', name: 'Default Voice', language: 'en', gender: 'neutral' }
    ],
    model_info: {
      model_name: 'xtts_v2',
      version: '2.0',
      size_mb: 1800,
    },
    pricing: {
      per_character: 0.00001,
      per_minute: 0.01,
    },
  },
  {
    id: 'openvoice',
    name: 'OpenVoice',
    description: 'Instant voice cloning',
    status: 'online',
    endpoint: 'https://ttslab.ailabsafrica.com/openvoice',
    capabilities: {
      streaming: false,
      cloning: true,
      emotions: true,
      multilingual: true,
      speed_control: true,
      pitch_control: false,
    },
    supported_languages: ['en', 'zh', 'es', 'fr', 'ja', 'ko'],
    voices: [
      { voice_id: 'default', name: 'Default Voice', language: 'en', gender: 'neutral' }
    ],
    model_info: {
      model_name: 'openvoice_v2',
      version: '2.0',
      size_mb: 250,
    },
    pricing: {
      per_character: 0.00002,
      per_minute: 0.015,
    },
  },
];

const mockProvidersResponse = {
  providers: mockProviders,
  count: mockProviders.length,
  online_count: 2,
  offline_count: 0,
  degraded_count: 0,
};

const mockSynthesisResponse = {
  audio_url: 'https://example.com/audio.wav',
  audio_base64: 'UklGRiQAAABXQVZFZm10IBAAAAABAAEA...',
  duration: 2.5,
  character_count: 50,
  cost: 0.0005,
  provider_used: 'coqui_xtts',
};

describe('useComprehensiveTTS - Unit Tests', () => {
  beforeEach(() => {
    // Reset fetch mock before each test
    vi.resetAllMocks();
    global.fetch = vi.fn();
  });

  describe('Provider Fetching', () => {
    it('should fetch providers on mount when autoFetch is true', async () => {
      // Mock successful fetch
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockProvidersResponse,
      } as Response);

      const { result } = renderHook(() =>
        useComprehensiveTTS('https://api.example.com', undefined, {
          autoFetch: true,
          endpointPath: '/api/tts/providers'
        })
      );

      // Initially loading
      expect(result.current.loading).toBe(true);

      // Wait for providers to load
      await waitFor(() => {
        expect(result.current.providers).toEqual(mockProviders);
      });

      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.example.com/api/tts/providers',
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
    });

    it('should not auto-fetch when autoFetch is false', async () => {
      const { result } = renderHook(() =>
        useComprehensiveTTS('https://api.example.com', undefined, {
          autoFetch: false
        })
      );

      expect(result.current.providers).toEqual([]);
      expect(result.current.loading).toBe(false);
      expect(global.fetch).not.toHaveBeenCalled();
    });

    it('should filter to online providers when onlineOnly is true', async () => {
      const mixedProviders = [
        { ...mockProviders[0], status: 'online' as const },
        { ...mockProviders[1], status: 'offline' as const },
      ];

      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({ providers: mixedProviders }),
      } as Response);

      const { result } = renderHook(() =>
        useComprehensiveTTS('https://api.example.com', undefined, {
          autoFetch: true,
          onlineOnly: true
        })
      );

      await waitFor(() => {
        expect(result.current.providers.length).toBe(1);
        expect(result.current.providers[0].status).toBe('online');
      });
    });

    it('should handle fetch errors gracefully', async () => {
      global.fetch = vi.fn().mockRejectedValueOnce(new Error('Network error'));

      const { result } = renderHook(() =>
        useComprehensiveTTS('https://api.example.com', undefined, {
          autoFetch: true
        })
      );

      await waitFor(() => {
        expect(result.current.error).toContain('Network error');
        expect(result.current.loading).toBe(false);
      });
    });

    it('should handle 404 errors', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
      } as Response);

      const { result } = renderHook(() =>
        useComprehensiveTTS('https://api.example.com', undefined, {
          autoFetch: true
        })
      );

      await waitFor(() => {
        expect(result.current.error).toContain('404');
        expect(result.current.providers).toEqual([]);
      });
    });
  });

  describe('Manual Refetch', () => {
    it('should refetch providers when refetch() is called', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockProvidersResponse,
      } as Response);

      const { result } = renderHook(() =>
        useComprehensiveTTS('https://api.example.com', undefined, {
          autoFetch: false
        })
      );

      expect(result.current.providers).toEqual([]);

      // Call refetch
      await act(async () => {
        await result.current.refetch();
      });

      await waitFor(() => {
        expect(result.current.providers).toEqual(mockProviders);
      });
    });
  });

  describe('Synthesis via Hook', () => {
    it('should synthesize text successfully', async () => {
      // Mock providers fetch
      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockProvidersResponse,
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockSynthesisResponse,
        } as Response);

      const { result } = renderHook(() =>
        useComprehensiveTTS('https://api.example.com', undefined, {
          autoFetch: true
        })
      );

      // Wait for providers to load
      await waitFor(() => {
        expect(result.current.providers.length).toBeGreaterThan(0);
      });

      // Synthesize text
      let synthResult;
      await act(async () => {
        synthResult = await result.current.synthesize(
          'Hello world',
          'coqui_xtts',
          'default',
          { speed: 1.0, pitch: 0.0 }
        );
      });

      expect(synthResult).toEqual(mockSynthesisResponse);
      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.example.com/api/tts/synthesize',
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('"text":"Hello world"'),
        })
      );
    });

    it('should handle synthesis errors', async () => {
      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockProvidersResponse,
        } as Response)
        .mockResolvedValueOnce({
          ok: false,
          status: 500,
          statusText: 'Internal Server Error',
        } as Response);

      const { result } = renderHook(() =>
        useComprehensiveTTS('https://api.example.com', undefined, {
          autoFetch: true
        })
      );

      await waitFor(() => {
        expect(result.current.providers.length).toBeGreaterThan(0);
      });

      await expect(
        act(async () => {
          await result.current.synthesize('Hello', 'coqui_xtts', 'default');
        })
      ).rejects.toThrow();
    });
  });

  describe('Voice Cloning via Hook', () => {
    it('should clone voice successfully', async () => {
      const mockCloneResponse = {
        voice_id: 'cloned_voice_001',
        success: true,
        message: 'Voice cloned successfully',
      };

      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockProvidersResponse,
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockCloneResponse,
        } as Response);

      const { result } = renderHook(() =>
        useComprehensiveTTS('https://api.example.com', undefined, {
          autoFetch: true
        })
      );

      await waitFor(() => {
        expect(result.current.providers.length).toBeGreaterThan(0);
      });

      const mockAudioBlob = new Blob(['fake audio'], { type: 'audio/wav' });
      let cloneResult;

      await act(async () => {
        cloneResult = await result.current.cloneVoice(
          'coqui_xtts',
          'My Cloned Voice',
          mockAudioBlob
        );
      });

      expect(cloneResult).toEqual(mockCloneResponse);
    });
  });

  describe('Cost Estimation', () => {
    it('should estimate synthesis cost', async () => {
      const mockCostResponse = {
        character_count: 50,
        estimated_duration: 2.5,
        estimated_cost: 0.0005,
        provider: 'coqui_xtts',
      };

      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockProvidersResponse,
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockCostResponse,
        } as Response);

      const { result } = renderHook(() =>
        useComprehensiveTTS('https://api.example.com', undefined, {
          autoFetch: true
        })
      );

      await waitFor(() => {
        expect(result.current.providers.length).toBeGreaterThan(0);
      });

      let costResult;
      await act(async () => {
        costResult = await result.current.estimateCost('Hello world', 'coqui_xtts');
      });

      expect(costResult).toEqual(mockCostResponse);
    });
  });

  describe('Wallet Balance', () => {
    it('should fetch wallet balance when userId is provided', async () => {
      const mockWalletResponse = {
        balance: 10.50,
        currency: 'USD',
      };

      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockProvidersResponse,
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockWalletResponse,
        } as Response);

      const { result } = renderHook(() =>
        useComprehensiveTTS('https://api.example.com', 'user_001', {
          autoFetch: true
        })
      );

      await waitFor(() => {
        expect(result.current.walletBalance).toBe(10.50);
      });
    });

    it('should not fetch wallet balance when userId is not provided', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockProvidersResponse,
      } as Response);

      const { result } = renderHook(() =>
        useComprehensiveTTS('https://api.example.com', undefined, {
          autoFetch: true
        })
      );

      await waitFor(() => {
        expect(result.current.providers.length).toBeGreaterThan(0);
      });

      expect(result.current.walletBalance).toBeNull();
      expect(global.fetch).toHaveBeenCalledTimes(1); // Only providers fetch
    });
  });

  describe('Custom Auth Headers', () => {
    it('should include custom auth headers in requests', async () => {
      const mockAuthHeaders = {
        'Authorization': 'Bearer test-token',
        'X-Custom-Header': 'custom-value',
      };

      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockProvidersResponse,
      } as Response);

      const { result } = renderHook(() =>
        useComprehensiveTTS('https://api.example.com', undefined, {
          autoFetch: true,
          getAuthHeaders: () => mockAuthHeaders,
        })
      );

      await waitFor(() => {
        expect(result.current.providers.length).toBeGreaterThan(0);
      });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token',
            'X-Custom-Header': 'custom-value',
          }),
        })
      );
    });
  });
});

/**
 * Integration Tests
 *
 * These tests run against the actual backend API
 * Set VITE_RUN_INTEGRATION_TESTS=true to enable
 */
describe('useComprehensiveTTS - Integration Tests', () => {
  const RUN_INTEGRATION = import.meta.env.VITE_RUN_INTEGRATION_TESTS === 'true';
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://dev-api.ailabsafrica.com';

  beforeEach(() => {
    if (!RUN_INTEGRATION) {
      console.log('⏭️  Skipping integration tests (set VITE_RUN_INTEGRATION_TESTS=true to enable)');
    }
  });

  it.skipIf(!RUN_INTEGRATION)('should fetch real providers from backend', async () => {
    const { result } = renderHook(() =>
      useComprehensiveTTS(API_BASE_URL, undefined, {
        autoFetch: true,
        endpointPath: '/api/tts/providers'
      })
    );

    // Wait for providers to load (may take a few seconds)
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    }, { timeout: 10000 });

    // Verify we got providers
    expect(result.current.providers.length).toBeGreaterThan(0);
    expect(result.current.error).toBeNull();

    // Verify provider structure
    const firstProvider = result.current.providers[0];
    expect(firstProvider).toHaveProperty('id');
    expect(firstProvider).toHaveProperty('name');
    expect(firstProvider).toHaveProperty('status');
    expect(firstProvider).toHaveProperty('capabilities');
    expect(firstProvider).toHaveProperty('supported_languages');

    console.log(`✅ Fetched ${result.current.providers.length} providers from ${API_BASE_URL}`);
  }, 15000);

  it.skipIf(!RUN_INTEGRATION)('should verify health status updates', async () => {
    const { result } = renderHook(() =>
      useComprehensiveTTS(API_BASE_URL, undefined, {
        autoFetch: true,
        endpointPath: '/api/tts/providers'
      })
    );

    await waitFor(() => {
      expect(result.current.providers.length).toBeGreaterThan(0);
    }, { timeout: 10000 });

    const initialProviders = [...result.current.providers];

    // Refetch to simulate health status update
    await act(async () => {
      await result.current.refetch();
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Verify providers still exist and have status
    expect(result.current.providers.length).toBe(initialProviders.length);
    result.current.providers.forEach(provider => {
      expect(['online', 'offline', 'degraded']).toContain(provider.status);
    });

    console.log('✅ Health status updates verified');
  }, 15000);

  it.skipIf(!RUN_INTEGRATION)('should perform real synthesis (if providers are online)', async () => {
    const { result } = renderHook(() =>
      useComprehensiveTTS(API_BASE_URL, undefined, {
        autoFetch: true,
        endpointPath: '/api/tts/providers'
      })
    );

    await waitFor(() => {
      expect(result.current.providers.length).toBeGreaterThan(0);
    }, { timeout: 10000 });

    // Find an online provider
    const onlineProvider = result.current.providers.find(p => p.status === 'online');

    if (!onlineProvider) {
      console.log('⏭️  No online providers available, skipping synthesis test');
      return;
    }

    console.log(`Using provider: ${onlineProvider.name} (${onlineProvider.id})`);

    // Perform synthesis
    let synthResult;
    await act(async () => {
      synthResult = await result.current.synthesize(
        'This is a test.',
        onlineProvider.id,
        onlineProvider.voices?.[0]?.voice_id || 'default',
        { speed: 1.0, pitch: 0.0 }
      );
    });

    // Verify synthesis response
    expect(synthResult).toBeDefined();
    expect(synthResult).toHaveProperty('audio_url');
    expect(synthResult.provider_used).toBe(onlineProvider.id);

    console.log(`✅ Synthesis successful with ${onlineProvider.name}`);
  }, 30000);
});
