/**
 * Automation Analytics Service
 *
 * Handles API communication for automation analytics data from VAPI.
 */

import { getAuthHeaders } from '@/lib/auth-utils';
import { API_BASE_URL } from '@/config/api-config';

export interface CallMetrics {
  total_calls: number;
  successful_calls: number;
  failed_calls: number;
  voicemail_calls: number;
  no_answer_calls: number;
  avg_duration: number;
  total_duration: number;
  total_duration_minutes?: number;
  min_duration?: number;
  max_duration?: number;
  success_rate: number;
  connect_rate: number;
  call_breakdown: {
    answered: number;
    ended: number;
    failed: number;
    voicemail: number;
    no_answer: number;
    other: number;
  };
  // AI-powered metrics
  ai_enriched_count: number;
  ai_enrichment_rate: number;
  sentiment_breakdown: {
    positive: number;
    negative: number;
    neutral: number;
    mixed: number;
  };
  dominant_sentiment: string;
  // Cost metrics
  total_cost: number;
  avg_cost_per_call: number;
  // Custom cost rate fields (for non-USD billing)
  cost_currency?: string;
  cost_currency_symbol?: string;
  cost_rate_per_call?: number;
  cost_breakdown?: {
    custom_cost?: number;
    rate_per_call?: number;
    currency?: string;
    total_calls?: number;
    vapi_cost?: number;
    vonage_cost?: number;
    total_cost?: number;
  };
  // VAPI cost breakdown by component
  vapi_cost_breakdown?: {
    llm: number;
    stt: number;
    tts: number;
    vapi: number;
    transport: number;
    total: number;
  };
  // Usage metrics (tokens, characters)
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
    tts_characters: number;
  };
}

export interface TrendDataPoint {
  date: string;
  calls: number;
  successful: number;
  duration: number;
}

export interface EnrichedCall {
  id: string;
  status: string;
  duration: number;
  customer?: { number: string };
  createdAt: string;
  endedAt?: string;
  // AI-enriched fields
  ai_summary?: string;
  sentiment?: string;
  vonage_cost?: number;
  ai_enriched?: boolean;
  transcript_preview?: string;
}

export interface AutomationAnalytics {
  automation_id: string;
  automation_name: string;
  assistant_id: string | null;
  time_range: string;
  period: {
    start: string;
    end: string;
  };
  metrics: CallMetrics;
  trend_data: TrendDataPoint[];
  recent_calls: EnrichedCall[];
  last_updated: string;
  error?: string;
}

export interface AnalyticsSummary {
  automation_id: string;
  automation_name: string;
  assistant_id: string | null;
  time_range: string;
  metrics: CallMetrics;
  last_updated: string;
}

export interface CallData {
  calls: any[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    pages: number;
  };
}

export interface SyncResult {
  success: boolean;
  automation_id: string;
  total_calls: number;
  new_calls: number;
  updated_calls: number;
  synced_at: string;
  error?: string;
}

export interface HealthStatus {
  automation_id: string;
  healthy: boolean;
  components: {
    vapi: {
      status: string;
      assistant_id?: string;
    };
    analytics: {
      status: string;
      last_updated?: string;
    };
  };
  checked_at: string;
  error?: string;
}

class AutomationAnalyticsService {
  /**
   * Get comprehensive analytics for an automation
   */
  async getAutomationAnalytics(
    configId: string,
    timeRange: '7d' | '30d' | '90d' | 'all' = '30d',
    forceRefresh: boolean = false
  ): Promise<AutomationAnalytics> {
    const params = new URLSearchParams({
      time_range: timeRange,
      force_refresh: forceRefresh.toString()
    });

    const response = await fetch(
      `${API_BASE_URL}/api/automation-analytics/${configId}?${params}`,
      {
        method: 'GET',
        headers: await getAuthHeaders()
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to fetch analytics' }));
      throw new Error(error.detail || 'Failed to fetch automation analytics');
    }

    const result = await response.json();
    return result.data;
  }

  /**
   * Get summary metrics for an automation (lighter weight)
   */
  async getAutomationSummary(
    configId: string,
    timeRange: '7d' | '30d' | '90d' | 'all' = '30d'
  ): Promise<AnalyticsSummary> {
    const params = new URLSearchParams({
      time_range: timeRange
    });

    const response = await fetch(
      `${API_BASE_URL}/api/automation-analytics/${configId}/summary?${params}`,
      {
        method: 'GET',
        headers: await getAuthHeaders()
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to fetch summary' }));
      throw new Error(error.detail || 'Failed to fetch automation summary');
    }

    const result = await response.json();
    return result.data;
  }

  /**
   * Get paginated call history for an automation
   */
  async getAutomationCalls(
    configId: string,
    page: number = 1,
    limit: number = 20,
    status?: string
  ): Promise<CallData> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString()
    });

    if (status) {
      params.append('status', status);
    }

    const response = await fetch(
      `${API_BASE_URL}/api/automation-analytics/${configId}/calls?${params}`,
      {
        method: 'GET',
        headers: await getAuthHeaders()
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to fetch calls' }));
      throw new Error(error.detail || 'Failed to fetch automation calls');
    }

    const result = await response.json();
    return result.data;
  }

  /**
   * Force refresh analytics from VAPI
   */
  async refreshAnalytics(configId: string): Promise<AutomationAnalytics> {
    const response = await fetch(
      `${API_BASE_URL}/api/automation-analytics/${configId}/refresh`,
      {
        method: 'POST',
        headers: await getAuthHeaders()
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to refresh analytics' }));
      throw new Error(error.detail || 'Failed to refresh analytics');
    }

    const result = await response.json();
    return result.data;
  }

  /**
   * Sync call data from VAPI to local database
   */
  async syncAutomationCalls(configId: string): Promise<SyncResult> {
    const response = await fetch(
      `${API_BASE_URL}/api/automation-analytics/${configId}/sync`,
      {
        method: 'POST',
        headers: await getAuthHeaders()
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to sync calls' }));
      throw new Error(error.detail || 'Failed to sync automation calls');
    }

    return await response.json();
  }

  /**
   * Get health status for automation analytics
   */
  async getAnalyticsHealth(configId: string): Promise<HealthStatus> {
    const response = await fetch(
      `${API_BASE_URL}/api/automation-analytics/${configId}/health`,
      {
        method: 'GET',
        headers: await getAuthHeaders()
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to check health' }));
      throw new Error(error.detail || 'Failed to check analytics health');
    }

    const result = await response.json();
    return result.data;
  }
}

// Export singleton instance
export const automationAnalyticsService = new AutomationAnalyticsService();

export default automationAnalyticsService;
