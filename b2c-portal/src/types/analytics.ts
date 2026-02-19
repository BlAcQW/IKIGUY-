/**
 * Shared analytics types for B2C Portal analytics components
 */

export interface VAPICallMetrics {
  id: string;
  automation_id: string;
  campaign_id?: string;
  call_duration: number;
  call_status: string;
  sentiment_score?: number;
  cost?: number;
  created_at: string;
  metadata: Record<string, any>;
}

export interface AutomationHealth {
  id: string;
  automation_id: string;
  campaign_id?: string;
  status: string;
  error_count: number;
  success_rate: number;
  last_execution: string;
  performance_metrics: Record<string, any>;
}

export interface CampaignPerformance {
  id: string;
  campaign_id: string;
  total_calls: number;
  successful_calls: number;
  failed_calls: number;
  total_cost: number;
  avg_call_duration: number;
  avg_sentiment_score?: number;
  success_rate: number;
  total_conversions: number;
  conversion_rate: number;
}

export interface CallLogEntry {
  id: string;
  call_id: string;
  assistant_id?: string;
  automation_id?: string;
  campaign_id?: string;
  phone_number?: string;
  call_status: string;
  call_duration?: number;
  cost?: number;
  transcript?: string;
  summary?: string;
  sentiment_score?: number;
  tool_calls?: any[];
  webhook_data?: any;
  metadata?: any;
  created_at: string;
  updated_at?: string;
}

export interface ToolCallHealth {
  tool_name: string;
  total_calls: number;
  success_rate: number;
  avg_execution_time?: number;
  error_rate: number;
  common_errors: string[];
  last_called: string;
  status: 'healthy' | 'warning' | 'error';
}

export interface VAPITestResult {
  test_id: string;
  test_type: string;
  success: boolean;
  duration: number;
  details: any;
  error?: string;
  timestamp: string;
}

export interface DashboardSummary {
  period: {
    start_date: string;
    end_date: string;
  };
  vapi_metrics: {
    total_calls: number;
    total_cost: number;
    avg_call_duration: number;
    avg_sentiment_score: number;
  };
  automation_health: {
    total_automations: number;
    healthy_automations: number;
    health_percentage: number;
  };
  campaign_performance: {
    total_campaigns: number;
    avg_success_rate: number;
    total_conversions: number;
  };
}

export interface AnalyticsOverview {
  total_automations: number;
  deployed_automations: number;
  success_rate: number;
  total_calls: number;
  total_cost: number;
  avg_sentiment: number;
  period_start: string;
  period_end: string;
}

export interface AutomationStatusResponse {
  config_id: string;
  status: string;
  deployment_date?: string;
  last_activity?: string;
  error_message?: string;
  metrics: {
    success_rate: number;
    total_executions: number;
    avg_execution_time: number;
  };
}

export type TimeRange = '1d' | '7d' | '30d' | '90d';
export type AnalyticsStatus = 'healthy' | 'warning' | 'error' | 'unknown';