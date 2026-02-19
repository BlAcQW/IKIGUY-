/**
 * useAIProvider Hook
 *
 * Generic hook for managing AI providers (TTS, LLM, ASR, etc.)
 * Provides state management, auto-refresh, and provider selection.
 *
 * @example
 * ```tsx
 * const {
 *   providers,
 *   selectedProvider,
 *   setSelectedProvider,
 *   loading,
 *   error,
 *   refetch
 * } = useAIProvider('tts', {
 *   apiUrl: 'https://api.ailabsafrica.com',
 *   refreshInterval: 60000,
 *   autoRefresh: true
 * });
 * ```
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import type {
  AIProvider,
  ProviderType,
  ProviderStatus,
  UseAIProviderOptions,
  UseAIProviderReturn,
} from './types';

/**
 * Default API URL from environment or fallback
 */
const getDefaultApiUrl = (): string => {
  if (typeof window !== 'undefined') {
    // @ts-ignore - Vite env vars
    return window.__VITE_API_URL__ || import.meta.env?.VITE_API_URL || 'http://localhost:8000';
  }
  return 'http://localhost:8000';
};

/**
 * Get authentication token from localStorage
 */
const getAuthToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('supabase_token') || localStorage.getItem('auth_token');
};

export function useAIProvider(
  providerType: ProviderType,
  options: UseAIProviderOptions = {}
): UseAIProviderReturn {
  const {
    apiUrl = getDefaultApiUrl(),
    refreshInterval = 60000,
    autoRefresh = true,
    initialProviderId,
    onProviderChange,
    onProvidersLoaded,
    onError,
  } = options;

  // State
  const [providers, setProviders] = useState<Record<string, AIProvider>>({});
  const [selectedProvider, setSelectedProviderState] = useState<AIProvider | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  // Refs for cleanup
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  /**
   * Fetch providers from API
   */
  const fetchProviders = useCallback(
    async (forceRefresh = false) => {
      // Cancel any in-flight request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      // Create new abort controller
      abortControllerRef.current = new AbortController();

      setLoading(true);
      setError(null);

      try {
        const token = getAuthToken();
        const url = new URL(`/api/v1/${providerType}/providers`, apiUrl);
        if (forceRefresh) {
          url.searchParams.set('force_refresh', 'true');
        }

        const response = await fetch(url.toString(), {
          headers: token
            ? {
                Authorization: `Bearer ${token}`,
              }
            : {},
          signal: abortControllerRef.current.signal,
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch providers: ${response.statusText}`);
        }

        const { data, success } = await response.json();

        if (!success || !data) {
          throw new Error('Invalid response format from API');
        }

        setProviders(data);

        // Call onProvidersLoaded callback
        if (onProvidersLoaded) {
          onProvidersLoaded(data);
        }

        // Auto-select provider if needed
        if (!selectedProvider && Object.keys(data).length > 0) {
          // Select initial provider if specified
          if (initialProviderId && data[initialProviderId]) {
            setSelectedProviderState(data[initialProviderId]);
          } else {
            // Otherwise select first online provider
            const firstOnline = Object.values(data).find(
              (p: AIProvider) => p.status === 'online'
            );
            if (firstOnline) {
              setSelectedProviderState(firstOnline);
            } else {
              // No online providers, select first one
              setSelectedProviderState(Object.values(data)[0] as AIProvider);
            }
          }
        } else if (selectedProvider && data[selectedProvider.id]) {
          // Update selected provider with latest data
          setSelectedProviderState(data[selectedProvider.id]);
        }
      } catch (err) {
        // Ignore abort errors
        if (err instanceof Error && err.name === 'AbortError') {
          return;
        }

        const error = err instanceof Error ? err : new Error('Unknown error');
        setError(error);

        // Call onError callback
        if (onError) {
          onError(error);
        }

        console.error('Error fetching AI providers:', error);
      } finally {
        setLoading(false);
      }
    },
    [
      providerType,
      apiUrl,
      selectedProvider,
      initialProviderId,
      onProvidersLoaded,
      onError,
    ]
  );

  /**
   * Set selected provider with callback
   */
  const setSelectedProvider = useCallback(
    (provider: AIProvider | null) => {
      setSelectedProviderState(provider);

      // Call onProviderChange callback
      if (onProviderChange) {
        onProviderChange(provider);
      }
    },
    [onProviderChange]
  );

  /**
   * Select provider by ID
   */
  const selectProviderById = useCallback(
    (providerId: string) => {
      const provider = providers[providerId];
      if (provider) {
        setSelectedProvider(provider);
      } else {
        console.warn(`Provider ${providerId} not found`);
      }
    },
    [providers, setSelectedProvider]
  );

  /**
   * Manually refetch providers
   */
  const refetch = useCallback(async () => {
    await fetchProviders(true);
  }, [fetchProviders]);

  /**
   * Get providers by status
   */
  const getProvidersByStatus = useCallback(
    (status: ProviderStatus): AIProvider[] => {
      return Object.values(providers).filter((p) => p.status === status);
    },
    [providers]
  );

  /**
   * Get providers by capability
   */
  const getProvidersByCapability = useCallback(
    (capability: string): AIProvider[] => {
      return Object.values(providers).filter((p) => p.capabilities[capability] === true);
    },
    [providers]
  );

  /**
   * Get online providers
   */
  const getOnlineProviders = useCallback((): AIProvider[] => {
    return getProvidersByStatus('online');
  }, [getProvidersByStatus]);

  /**
   * Initial fetch and auto-refresh setup
   */
  useEffect(() => {
    // Initial fetch
    fetchProviders(false);

    // Set up auto-refresh if enabled
    if (autoRefresh && refreshInterval > 0) {
      intervalRef.current = setInterval(() => {
        fetchProviders(false);
      }, refreshInterval);
    }

    // Cleanup
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [fetchProviders, autoRefresh, refreshInterval]);

  return {
    providers,
    selectedProvider,
    setSelectedProvider,
    selectProviderById,
    loading,
    error,
    refetch,
    getProvidersByStatus,
    getProvidersByCapability,
    getOnlineProviders,
  };
}
