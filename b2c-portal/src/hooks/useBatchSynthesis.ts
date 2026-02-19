/**
 * Batch Synthesis Hook
 *
 * Custom hook for managing batch TTS synthesis from CSV files.
 * Created: 2025-10-27
 * Sprint 4: Advanced Features (Phase 9)
 */

import { useState, useCallback } from 'react';
import { API_ENDPOINTS } from '../config/api-config';

interface BatchJob {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  total_items: number;
  completed_items: number;
  failed_items: number;
  total_cost: number;
  zip_filename: string | null;
  created_at: string;
  completed_at: string | null;
}

interface UseBatchSynthesisReturn {
  uploadBatch: (
    file: File,
    providerId: string,
    language?: string,
    voiceId?: string,
    speed?: number,
    pitch?: number
  ) => Promise<BatchJob | null>;
  getBatchJob: (batchId: string) => Promise<BatchJob | null>;
  listBatchJobs: () => Promise<BatchJob[]>;
  downloadBatch: (batchId: string, filename: string) => Promise<void>;
  deleteBatch: (batchId: string) => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

export const useBatchSynthesis = (): UseBatchSynthesisReturn => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const uploadBatch = useCallback(
    async (
      file: File,
      providerId: string,
      language: string = 'en',
      voiceId?: string,
      speed: number = 1.0,
      pitch: number = 0.0
    ): Promise<BatchJob | null> => {
      setIsLoading(true);
      setError(null);

      try {
        const formData = new FormData();
        formData.append('file', file);

        // Build query parameters
        const params = new URLSearchParams({
          provider_id: providerId,
          language: language,
          speed: speed.toString(),
          pitch: pitch.toString(),
        });

        if (voiceId) {
          params.append('voice_id', voiceId);
        }

        const response = await fetch(
          `${API_ENDPOINTS.tts.batch}/upload?${params.toString()}`,
          {
            method: 'POST',
            body: formData,
          }
        );

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || 'Failed to upload batch');
        }

        const data = await response.json();
        return data as BatchJob;
      } catch (err: any) {
        const errorMessage = err.message || 'Failed to upload batch';
        setError(errorMessage);
        console.error('Batch upload error:', err);
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const getBatchJob = useCallback(async (batchId: string): Promise<BatchJob | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_ENDPOINTS.tts.batch}/${batchId}`);

      if (!response.ok) {
        throw new Error('Failed to fetch batch job');
      }

      const data = await response.json();
      return data as BatchJob;
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to fetch batch job';
      setError(errorMessage);
      console.error('Batch fetch error:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const listBatchJobs = useCallback(async (): Promise<BatchJob[]> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_ENDPOINTS.tts.batch}`);

      if (!response.ok) {
        throw new Error('Failed to list batch jobs');
      }

      const data = await response.json();
      return data as BatchJob[];
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to list batch jobs';
      setError(errorMessage);
      console.error('Batch list error:', err);
      return [];
    } finally {
      setIsLoading(false);
    }
  }, []);

  const downloadBatch = useCallback(
    async (batchId: string, filename: string): Promise<void> => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch(`${API_ENDPOINTS.tts.batch}/${batchId}/download`);

        if (!response.ok) {
          throw new Error('Failed to download batch');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename || `batch_${batchId}.zip`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } catch (err: any) {
        const errorMessage = err.message || 'Failed to download batch';
        setError(errorMessage);
        console.error('Batch download error:', err);
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const deleteBatch = useCallback(async (batchId: string): Promise<void> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_ENDPOINTS.tts.batch}/${batchId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete batch');
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to delete batch';
      setError(errorMessage);
      console.error('Batch delete error:', err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    uploadBatch,
    getBatchJob,
    listBatchJobs,
    downloadBatch,
    deleteBatch,
    isLoading,
    error,
  };
};
