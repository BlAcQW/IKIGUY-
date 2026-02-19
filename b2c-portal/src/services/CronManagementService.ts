/**
 * Cron Management Service
 * Handles API calls for managing scheduled cron jobs
 */

import { getAuthHeaders } from '@/lib/auth-utils';
import { API_BASE_URL } from '@/config/api-config';

export interface CronJob {
  id: string;
  name: string;
  description: string;
  func_name: string;
  trigger_type: string;
  trigger_details: Record<string, any>;
  next_run_time: string | null;
  is_paused: boolean;
  job_type: string;
  created_at?: string;
  created_by?: string;
  metadata?: Record<string, any>;
}

export interface CronJobDetail extends CronJob {
  recent_logs: CronExecutionLog[];
}

export interface CronExecutionLog {
  _id: string;
  job_id: string;
  job_name: string;
  status: string;
  duration_ms: number;
  executed_at: string;
  error_message?: string;
  result?: any;
}

export interface CronStats {
  total_jobs: number;
  active_jobs: number;
  paused_jobs: number;
  jobs_by_type: Record<string, number>;
  recent_success_rate: number;
  recent_executions: number;
}

class CronManagementService {
  /**
   * Get all scheduled cron jobs
   */
  async getCronJobs(status?: string, jobType?: string): Promise<{ success: boolean; jobs: CronJob[]; total: number }> {
    try {
      const headers = await getAuthHeaders();
      const params = new URLSearchParams();

      if (status) params.append('status', status);
      if (jobType) params.append('job_type', jobType);

      const queryString = params.toString() ? `?${params.toString()}` : '';
      const response = await fetch(`${API_BASE_URL}/cron-management/jobs${queryString}`, {
        method: 'GET',
        headers: {
          ...headers,
          'x-service-token': 'kasaai-b2c-portal'
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || 'Failed to fetch cron jobs');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching cron jobs:', error);
      throw error;
    }
  }

  /**
   * Get details of a specific cron job
   */
  async getCronJob(jobId: string): Promise<{ success: boolean; job: CronJobDetail }> {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/cron-management/jobs/${jobId}`, {
        method: 'GET',
        headers: {
          ...headers,
          'x-service-token': 'kasaai-b2c-portal'
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || 'Failed to fetch cron job');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching cron job:', error);
      throw error;
    }
  }

  /**
   * Pause a cron job
   */
  async pauseCronJob(jobId: string): Promise<{ success: boolean; message: string }> {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/cron-management/jobs/${jobId}/pause`, {
        method: 'POST',
        headers: {
          ...headers,
          'x-service-token': 'kasaai-b2c-portal'
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || 'Failed to pause cron job');
      }

      return await response.json();
    } catch (error) {
      console.error('Error pausing cron job:', error);
      throw error;
    }
  }

  /**
   * Resume a paused cron job
   */
  async resumeCronJob(jobId: string): Promise<{ success: boolean; message: string }> {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/cron-management/jobs/${jobId}/resume`, {
        method: 'POST',
        headers: {
          ...headers,
          'x-service-token': 'kasaai-b2c-portal'
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || 'Failed to resume cron job');
      }

      return await response.json();
    } catch (error) {
      console.error('Error resuming cron job:', error);
      throw error;
    }
  }

  /**
   * Delete a cron job
   */
  async deleteCronJob(jobId: string): Promise<{ success: boolean; message: string }> {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/cron-management/jobs/${jobId}`, {
        method: 'DELETE',
        headers: {
          ...headers,
          'x-service-token': 'kasaai-b2c-portal'
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || 'Failed to delete cron job');
      }

      return await response.json();
    } catch (error) {
      console.error('Error deleting cron job:', error);
      throw error;
    }
  }

  /**
   * Get execution logs for cron jobs
   */
  async getExecutionLogs(
    jobId?: string,
    status?: string,
    limit: number = 100
  ): Promise<{ success: boolean; logs: CronExecutionLog[]; total: number }> {
    try {
      const headers = await getAuthHeaders();
      const params = new URLSearchParams();

      if (jobId) params.append('job_id', jobId);
      if (status) params.append('status', status);
      params.append('limit', limit.toString());

      const queryString = params.toString() ? `?${params.toString()}` : '';
      const response = await fetch(`${API_BASE_URL}/cron-management/logs${queryString}`, {
        method: 'GET',
        headers: {
          ...headers,
          'x-service-token': 'kasaai-b2c-portal'
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || 'Failed to fetch execution logs');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching execution logs:', error);
      throw error;
    }
  }

  /**
   * Get cron statistics
   */
  async getCronStats(): Promise<{ success: boolean; stats: CronStats }> {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/cron-management/stats`, {
        method: 'GET',
        headers: {
          ...headers,
          'x-service-token': 'kasaai-b2c-portal'
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || 'Failed to fetch cron stats');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching cron stats:', error);
      throw error;
    }
  }

  /**
   * Initialize demo cron jobs
   */
  async initializeDemoJobs(): Promise<{ success: boolean; message: string }> {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/cron-management/demo/initialize`, {
        method: 'POST',
        headers: {
          ...headers,
          'x-service-token': 'kasaai-b2c-portal'
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || 'Failed to initialize demo jobs');
      }

      return await response.json();
    } catch (error) {
      console.error('Error initializing demo jobs:', error);
      throw error;
    }
  }

  /**
   * Create a custom cron job
   */
  async createCronJob(jobData: {
    name: string;
    description: string;
    cron_expression: string;
    job_type: string;
    webhook_url?: string;
    script_path?: string;
    metadata?: Record<string, any>;
  }): Promise<{ success: boolean; job_id: string; message: string }> {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/cron-management/jobs/create`, {
        method: 'POST',
        headers: {
          ...headers,
          'Content-Type': 'application/json',
          'x-service-token': 'kasaai-b2c-portal'
        },
        body: JSON.stringify(jobData),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || 'Failed to create cron job');
      }

      return await response.json();
    } catch (error) {
      console.error('Error creating cron job:', error);
      throw error;
    }
  }
}

export const cronManagementService = new CronManagementService();
