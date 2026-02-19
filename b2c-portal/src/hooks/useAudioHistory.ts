/**
 * Custom hook for managing TTS audio history
 *
 * Provides functions to:
 * - List audio history with pagination
 * - Get history item details with full audio
 * - Delete history items
 * - Search and filter history
 *
 * Created: 2025-10-27
 * Sprint 2: User Experience Enhancements (Phase 8)
 */

import { useState, useCallback } from 'react';
import { API_BASE_URL } from '../config/api-config';

export interface AudioHistoryItem {
  _id: string;
  user_id: string;
  text: string;
  full_text: string;
  provider_id: string;
  voice_id?: string;
  language: string;
  audio_base64?: string;
  duration_seconds: number;
  cost: number;
  character_count: number;
  created_at: string;
  deleted_at?: string;
}

export interface AudioHistoryListResponse {
  items: AudioHistoryItem[];
  total: number;
  page: number;
  limit: number;
  has_more: boolean;
}

export interface UseAudioHistoryReturn {
  items: AudioHistoryItem[];
  total: number;
  page: number;
  hasMore: boolean;
  isLoading: boolean;
  error: string | null;
  fetchHistory: (page?: number, limit?: number, search?: string, provider?: string) => Promise<void>;
  getHistoryItem: (itemId: string) => Promise<AudioHistoryItem | null>;
  deleteHistoryItem: (itemId: string) => Promise<boolean>;
  playHistoryItem: (itemId: string) => Promise<void>;
}

export const useAudioHistory = (): UseAudioHistoryReturn => {
  const [items, setItems] = useState<AudioHistoryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Fetch audio history with pagination and filters.
   */
  const fetchHistory = useCallback(async (
    pageNum: number = 1,
    limit: number = 20,
    search?: string,
    provider?: string
  ) => {
    setIsLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      params.append('page', pageNum.toString());
      params.append('limit', limit.toString());
      if (search) params.append('search', search);
      if (provider) params.append('provider', provider);

      const url = `${API_BASE_URL}/api/tts/history?${params.toString()}`;

      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch history: ${response.statusText}`);
      }

      const data: AudioHistoryListResponse = await response.json();
      setItems(data.items);
      setTotal(data.total);
      setPage(data.page);
      setHasMore(data.has_more);

    } catch (err: any) {
      const errorMessage = err.message || 'Failed to fetch audio history';
      setError(errorMessage);
      console.error('Error fetching audio history:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Get a specific history item with full audio data.
   */
  const getHistoryItem = useCallback(async (itemId: string): Promise<AudioHistoryItem | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const url = `${API_BASE_URL}/api/tts/history/${itemId}`;

      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('History item not found');
        }
        throw new Error(`Failed to fetch history item: ${response.statusText}`);
      }

      const data: AudioHistoryItem = await response.json();
      return data;

    } catch (err: any) {
      const errorMessage = err.message || 'Failed to fetch history item';
      setError(errorMessage);
      console.error('Error fetching history item:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Delete a history item (soft delete).
   */
  const deleteHistoryItem = useCallback(async (itemId: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      const url = `${API_BASE_URL}/api/tts/history/${itemId}`;

      const response = await fetch(url, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('History item not found or already deleted');
        }
        throw new Error(`Failed to delete history item: ${response.statusText}`);
      }

      // Remove from local state
      setItems(prev => prev.filter(item => item._id !== itemId));
      setTotal(prev => prev - 1);

      return true;

    } catch (err: any) {
      const errorMessage = err.message || 'Failed to delete history item';
      setError(errorMessage);
      console.error('Error deleting history item:', err);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Play audio from a history item.
   */
  const playHistoryItem = useCallback(async (itemId: string): Promise<void> => {
    try {
      // Fetch the full history item with audio
      const item = await getHistoryItem(itemId);

      if (!item || !item.audio_base64) {
        throw new Error('Audio data not available');
      }

      // Convert base64 to audio blob
      const audioBytes = Uint8Array.from(atob(item.audio_base64), c => c.charCodeAt(0));
      const blob = new Blob([audioBytes], { type: 'audio/wav' });
      const audioUrl = URL.createObjectURL(blob);

      // Create and play audio
      const audio = new Audio(audioUrl);
      audio.onended = () => {
        URL.revokeObjectURL(audioUrl);
      };
      await audio.play();

    } catch (err: any) {
      const errorMessage = err.message || 'Failed to play audio';
      setError(errorMessage);
      console.error('Error playing audio:', err);
    }
  }, [getHistoryItem]);

  return {
    items,
    total,
    page,
    hasMore,
    isLoading,
    error,
    fetchHistory,
    getHistoryItem,
    deleteHistoryItem,
    playHistoryItem,
  };
};
