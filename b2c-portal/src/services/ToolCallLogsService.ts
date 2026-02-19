/**
 * Tool Call Logs Service
 *
 * Handles all API interactions for tool call logging system.
 * Provides access to tool call logs, statistics, and analytics.
 */

import { API_BASE_URL } from '@/config/api-config';

// ===========================
// Type Definitions
// ===========================

export type ToolCallStatus = 'success' | 'failed' | 'timeout' | 'error';

export interface CityNormalization {
  original: string;
  normalized: string;
  confidence: number;
  method: string;
}

export interface ToolCallLog {
  id: string;
  tool_call_id: string;
  company_name: string;
  query_original: string;
  query_normalized?: string;
  response: string;
  response_length: number;
  status: ToolCallStatus;
  error_message?: string;
  processing_time: number;
  retrieval_time?: number;
  llm_time?: number;
  documents_retrieved: number;
  documents_sent_to_llm: number;
  confidence_score: number;
  requires_escalation: boolean;
  escalation_reason?: string;
  sources_used: string[];
  ip_address?: string;
  user_agent?: string;
  vapi_call_id?: string;
  created_at: string;
  is_cached: boolean;
  cache_key?: string;
  city_normalization?: CityNormalization;
}

export interface ToolCallLogsFilter {
  company_name?: string;
  automation_id?: string;
  status?: ToolCallStatus;
  days?: number;
  page?: number;
  page_size?: number;
  search?: string;
}

export interface ToolCallLogsListResponse {
  success: boolean;
  logs: ToolCallLog[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ToolStats {
  success: boolean;
  tool_name: string;
  total_calls: number;
  successful_calls: number;
  failed_calls: number;
  success_rate: number;
  avg_processing_time: number;
  avg_confidence_score: number;
  total_escalations: number;
  escalation_rate: number;
  avg_cached_response_time: number;
  cache_hit_rate: number;
  most_recent_call?: string;
  oldest_call?: string;
}

// ===========================
// Helper Functions
// ===========================

/**
 * Build query string from filter object.
 */
const buildQueryString = (params: Record<string, any>): string => {
  const query = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.append(key, String(value));
    }
  });

  return query.toString();
};

/**
 * Make authenticated API request.
 */
const makeRequest = async <T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> => {
  const token = localStorage.getItem('auth_token');

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
    ...options.headers,
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
  }

  return response.json();
};

// ===========================
// Service Class
// ===========================

class ToolCallLogsService {
  /**
   * Get paginated list of tool call logs with optional filters.
   *
   * @param filters - Filter criteria for logs
   * @returns Paginated list of tool call logs
   *
   * @example
   * ```typescript
   * const logs = await toolCallLogsService.getToolCallLogs({
   *   company_name: 'premier_health_production',
   *   days: 7,
   *   page: 1,
   *   page_size: 50
   * });
   * ```
   */
  async getToolCallLogs(filters: ToolCallLogsFilter = {}): Promise<ToolCallLogsListResponse> {
    const queryString = buildQueryString(filters);
    return makeRequest<ToolCallLogsListResponse>(
      `/tool-calls/logs?${queryString}`
    );
  }

  /**
   * Get detailed information about a specific tool call log.
   *
   * @param logId - MongoDB _id of the tool call log
   * @returns Detailed tool call log
   *
   * @example
   * ```typescript
   * const log = await toolCallLogsService.getToolCallDetail('507f1f77bcf86cd799439011');
   * ```
   */
  async getToolCallDetail(logId: string): Promise<ToolCallLog> {
    return makeRequest<ToolCallLog>(`/tool-calls/logs/${logId}`);
  }

  /**
   * Get statistics for a specific tool/company.
   *
   * @param companyName - Company/knowledge base name (e.g., "premier_health_production")
   * @param days - Number of days to analyze (default 30, max 90)
   * @returns Tool statistics including success rates and performance metrics
   *
   * @example
   * ```typescript
   * const stats = await toolCallLogsService.getToolStats('premier_health_production', 30);
   * console.log(`Success rate: ${stats.success_rate}%`);
   * console.log(`Avg processing time: ${stats.avg_processing_time}ms`);
   * ```
   */
  async getToolStats(companyName: string, days: number = 30): Promise<ToolStats> {
    const queryString = buildQueryString({ days });
    return makeRequest<ToolStats>(
      `/tool-calls/stats/${encodeURIComponent(companyName)}?${queryString}`
    );
  }

  /**
   * Get all tool call logs for a specific automation.
   *
   * @param automationId - Automation ID (matches vapi_call_id in logs)
   * @param days - Number of days to look back (default 30, max 90)
   * @param page - Page number (default 1)
   * @param pageSize - Items per page (default 50, max 100)
   * @returns Paginated list of tool call logs for the automation
   *
   * @example
   * ```typescript
   * const logs = await toolCallLogsService.getAutomationToolLogs(
   *   'automation_123',
   *   30,
   *   1,
   *   50
   * );
   * ```
   */
  async getAutomationToolLogs(
    automationId: string,
    days: number = 30,
    page: number = 1,
    pageSize: number = 50
  ): Promise<ToolCallLogsListResponse> {
    const queryString = buildQueryString({ days, page, page_size: pageSize });
    return makeRequest<ToolCallLogsListResponse>(
      `/tool-calls/automation/${encodeURIComponent(automationId)}/logs?${queryString}`
    );
  }

  /**
   * Search tool call logs by query text.
   *
   * @param searchTerm - Search term to find in query/response text
   * @param filters - Additional filter criteria
   * @returns Paginated list of matching tool call logs
   *
   * @example
   * ```typescript
   * const logs = await toolCallLogsService.searchToolCallLogs('heart specialist', {
   *   company_name: 'premier_health_production',
   *   days: 7
   * });
   * ```
   */
  async searchToolCallLogs(
    searchTerm: string,
    filters: Omit<ToolCallLogsFilter, 'search'> = {}
  ): Promise<ToolCallLogsListResponse> {
    return this.getToolCallLogs({
      ...filters,
      search: searchTerm,
    });
  }

  /**
   * Get failed tool calls for debugging.
   *
   * @param companyName - Company/knowledge base name
   * @param days - Number of days to look back
   * @param page - Page number
   * @param pageSize - Items per page
   * @returns Paginated list of failed tool calls
   *
   * @example
   * ```typescript
   * const failedCalls = await toolCallLogsService.getFailedToolCalls(
   *   'premier_health_production',
   *   7
   * );
   * ```
   */
  async getFailedToolCalls(
    companyName: string,
    days: number = 7,
    page: number = 1,
    pageSize: number = 50
  ): Promise<ToolCallLogsListResponse> {
    return this.getToolCallLogs({
      company_name: companyName,
      status: 'failed',
      days,
      page,
      page_size: pageSize,
    });
  }

  /**
   * Get escalated tool calls (low confidence or requiring human review).
   *
   * @param companyName - Company/knowledge base name
   * @param days - Number of days to look back
   * @param page - Page number
   * @param pageSize - Items per page
   * @returns Paginated list of escalated tool calls
   *
   * @example
   * ```typescript
   * const escalated = await toolCallLogsService.getEscalatedToolCalls(
   *   'premier_health_production',
   *   7
   * );
   * ```
   */
  async getEscalatedToolCalls(
    companyName: string,
    days: number = 7,
    page: number = 1,
    pageSize: number = 50
  ): Promise<ToolCallLog[]> {
    const result = await this.getToolCallLogs({
      company_name: companyName,
      days,
      page,
      page_size: pageSize,
    });

    // Reason: Filter escalated calls on frontend since backend doesn't have dedicated endpoint
    return result.logs.filter(log => log.requires_escalation);
  }

  /**
   * Get cached vs non-cached tool call statistics.
   *
   * @param companyName - Company/knowledge base name
   * @param days - Number of days to analyze
   * @returns Cache performance statistics
   *
   * @example
   * ```typescript
   * const cacheStats = await toolCallLogsService.getCacheStatistics(
   *   'premier_health_production',
   *   30
   * );
   * console.log(`Cache hit rate: ${cacheStats.cache_hit_rate}%`);
   * ```
   */
  async getCacheStatistics(companyName: string, days: number = 30): Promise<ToolStats> {
    return this.getToolStats(companyName, days);
  }

  /**
   * Export tool call logs to CSV format.
   *
   * @param filters - Filter criteria for logs to export
   * @returns CSV string of tool call logs
   *
   * @example
   * ```typescript
   * const csv = await toolCallLogsService.exportToCSV({
   *   company_name: 'premier_health_production',
   *   days: 30
   * });
   * // Download CSV file
   * const blob = new Blob([csv], { type: 'text/csv' });
   * const url = URL.createObjectURL(blob);
   * const a = document.createElement('a');
   * a.href = url;
   * a.download = 'tool-call-logs.csv';
   * a.click();
   * ```
   */
  async exportToCSV(filters: ToolCallLogsFilter = {}): Promise<string> {
    // Reason: Fetch all logs without pagination limit for export
    const allLogs: ToolCallLog[] = [];
    let page = 1;
    let hasMore = true;

    while (hasMore) {
      const result = await this.getToolCallLogs({
        ...filters,
        page,
        page_size: 100, // Max page size for efficiency
      });

      allLogs.push(...result.logs);
      hasMore = page < result.total_pages;
      page++;
    }

    // Convert to CSV
    const headers = [
      'ID',
      'Tool Call ID',
      'Company',
      'Query',
      'Response',
      'Status',
      'Processing Time (ms)',
      'Confidence Score',
      'Escalation',
      'Sources Count',
      'Is Cached',
      'Created At',
    ];

    const rows = allLogs.map(log => [
      log.id,
      log.tool_call_id,
      log.company_name,
      log.query_original.replace(/"/g, '""'), // Escape quotes
      log.response.substring(0, 100).replace(/"/g, '""'), // Truncate and escape
      log.status,
      log.processing_time.toFixed(2),
      log.confidence_score.toFixed(3),
      log.requires_escalation ? 'Yes' : 'No',
      log.sources_used.length,
      log.is_cached ? 'Yes' : 'No',
      log.created_at,
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(',')),
    ].join('\n');

    return csvContent;
  }

  /**
   * Get performance metrics breakdown (retrieval vs LLM time).
   *
   * @param logs - Array of tool call logs to analyze
   * @returns Performance breakdown statistics
   *
   * @example
   * ```typescript
   * const logs = await toolCallLogsService.getToolCallLogs({ days: 7 });
   * const breakdown = toolCallLogsService.getPerformanceBreakdown(logs.logs);
   * console.log(`Avg retrieval time: ${breakdown.avg_retrieval_time}ms`);
   * console.log(`Avg LLM time: ${breakdown.avg_llm_time}ms`);
   * ```
   */
  getPerformanceBreakdown(logs: ToolCallLog[]): {
    avg_retrieval_time: number;
    avg_llm_time: number;
    avg_total_time: number;
    retrieval_percentage: number;
    llm_percentage: number;
  } {
    const logsWithTiming = logs.filter(
      log => log.retrieval_time !== undefined && log.llm_time !== undefined
    );

    if (logsWithTiming.length === 0) {
      return {
        avg_retrieval_time: 0,
        avg_llm_time: 0,
        avg_total_time: 0,
        retrieval_percentage: 0,
        llm_percentage: 0,
      };
    }

    const totalRetrieval = logsWithTiming.reduce(
      (sum, log) => sum + (log.retrieval_time || 0),
      0
    );
    const totalLLM = logsWithTiming.reduce((sum, log) => sum + (log.llm_time || 0), 0);
    const totalTime = totalRetrieval + totalLLM;

    return {
      avg_retrieval_time: totalRetrieval / logsWithTiming.length,
      avg_llm_time: totalLLM / logsWithTiming.length,
      avg_total_time: totalTime / logsWithTiming.length,
      retrieval_percentage: (totalRetrieval / totalTime) * 100,
      llm_percentage: (totalLLM / totalTime) * 100,
    };
  }
}

// Export singleton instance
export const toolCallLogsService = new ToolCallLogsService();
export default toolCallLogsService;
