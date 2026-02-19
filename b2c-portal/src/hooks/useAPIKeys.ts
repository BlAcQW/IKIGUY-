/**
 * Custom hook for managing API keys
 *
 * Provides functions to:
 * - List API keys
 * - Create new API keys
 * - Revoke API keys
 * - Get usage statistics
 *
 * Created: 2025-10-27
 * Sprint 5: Analytics & Ecosystem (Phase 8)
 */

import { useState, useCallback, useEffect } from 'react';
import { API_BASE_URL } from '../config/api-config';

export interface APIKey {
  id: string;
  name: string;
  key_prefix: string;
  scopes: string[];
  rate_limit: number;
  last_used_at?: string;
  request_count: number;
  created_at: string;
  expires_at?: string;
  revoked: boolean;
}

export interface APIKeyWithSecret extends APIKey {
  api_key: string;
}

export interface APIKeyCreate {
  name: string;
  scopes: string[];
  rate_limit: number;
  expires_in_days?: number;
}

export interface UseAPIKeysReturn {
  keys: APIKey[];
  isLoading: boolean;
  error: string | null;
  fetchKeys: () => Promise<void>;
  createKey: (keyData: APIKeyCreate) => Promise<APIKeyWithSecret | null>;
  revokeKey: (keyId: string) => Promise<boolean>;
  refreshKeys: () => Promise<void>;
}

export const useAPIKeys = (): UseAPIKeysReturn => {
  const [keys, setKeys] = useState<APIKey[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Fetch list of API keys
   */
  const fetchKeys = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const url = `${API_BASE_URL}/api/keys`;

      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch API keys: ${response.statusText}`);
      }

      const data: APIKey[] = await response.json();
      setKeys(data);

      return;
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to fetch API keys';
      setError(errorMessage);
      console.error('Error fetching API keys:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Create a new API key
   */
  const createKey = useCallback(async (keyData: APIKeyCreate): Promise<APIKeyWithSecret | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const url = `${API_BASE_URL}/api/keys`;

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(keyData),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to create API key');
      }

      const key: APIKeyWithSecret = await response.json();

      // Refresh keys list
      await fetchKeys();

      return key;
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to create API key';
      setError(errorMessage);
      console.error('Error creating API key:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [fetchKeys]);

  /**
   * Revoke an API key
   */
  const revokeKey = useCallback(async (keyId: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      const url = `${API_BASE_URL}/api/keys/${keyId}`;

      const response = await fetch(url, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('API key not found');
        }
        throw new Error(`Failed to revoke API key: ${response.statusText}`);
      }

      // Refresh keys list after revocation
      await fetchKeys();

      return true;
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to revoke API key';
      setError(errorMessage);
      console.error('Error revoking API key:', err);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [fetchKeys]);

  /**
   * Refresh keys list
   */
  const refreshKeys = useCallback(async () => {
    await fetchKeys();
  }, [fetchKeys]);

  // Load keys on mount
  useEffect(() => {
    fetchKeys();
  }, [fetchKeys]);

  return {
    keys,
    isLoading,
    error,
    fetchKeys,
    createKey,
    revokeKey,
    refreshKeys,
  };
};
