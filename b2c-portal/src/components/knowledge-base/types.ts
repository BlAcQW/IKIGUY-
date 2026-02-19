/**
 * Shared types for Knowledge Base components.
 */

export type DocumentStatus = 'pending' | 'processing' | 'indexed' | 'failed' | 'archived';

export type DocumentSource =
  | 'file_upload'
  | 'manual_entry'
  | 'api_import'
  | 'url_scrape'
  | 'integration_sync';

export interface DocumentMetadata {
  word_count?: number;
  character_count?: number;
  chunk_count?: number;
  filename?: string;
  file_size?: number;
  file_type?: string;
  embedding_model?: string;
  processing_time_ms?: number;
  query_count?: number;
  reference_count?: number;
  last_queried_at?: string;
  confidence_avg?: number;
  usefulness_score?: number;
  custom_fields?: Record<string, any>;
}

export interface DocumentVersion {
  version_id: string;
  version_number: number;
  content: string;
  title: string;
  category: string;
  tags: string[];
  changed_by?: string;
  change_reason?: string;
  changes_summary?: string;
  created_at: string;
}

export interface KnowledgeDocument {
  id: string;
  company_name: string;
  collection_name: string;
  title: string;
  content: string;
  content_hash?: string;
  category: string;
  tags: string[];
  source: DocumentSource;
  source_uri?: string;
  status: DocumentStatus;
  current_version: number;
  versions: DocumentVersion[];
  metadata: DocumentMetadata;
  vector_ids: string[];
  embedding_dimension: number;
  created_by?: string;
  updated_by?: string;
  created_at: string;
  updated_at: string;
  indexed_at?: string;
  is_active: boolean;
  is_archived: boolean;
}

export interface DocumentFilter {
  company_name: string;
  category?: string;
  tags?: string[];
  status?: DocumentStatus;
  source?: DocumentSource;
  search_query?: string;
  is_active?: boolean;
  is_archived?: boolean;
  created_after?: string;
  created_before?: string;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface DocumentResponse {
  success: boolean;
  document?: KnowledgeDocument;
  message?: string;
}

export interface DocumentListResponse {
  success: boolean;
  documents: KnowledgeDocument[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface BulkDeleteRequest {
  company_name: string;
  document_ids: string[];
  deleted_by?: string;
}

export interface BulkDeleteResponse {
  success: boolean;
  deleted_count: number;
  failed_count: number;
  failed_ids: string[];
  errors: string[];
}

export interface QueryMetric {
  id: string;
  company_name: string;
  query: string;
  response: string;
  confidence_score: number;
  processing_time_ms: number;
  sources_used: string[];
  num_sources: number;
  requires_escalation: boolean;
  escalation_reason?: string;
  query_category?: string;
  user_id?: string;
  session_id?: string;
  user_rating?: number;
  user_feedback?: string;
  created_at: string;
}

export interface AnalyticsOverview {
  total_queries: number;
  avg_confidence_score: number;
  escalation_rate: number;
  avg_processing_time_ms: number;
  total_documents: number;
  indexed_documents: number;
  failed_documents: number;
  daily_query_trend: Array<{ date: string; count: number }>;
  confidence_trend: Array<{ date: string; avg_confidence: number }>;
}

export interface ConfidenceBucket {
  range: string;
  count: number;
  percentage: number;
}

export interface TopQuery {
  query: string;
  count: number;
  avg_confidence: number;
  escalation_rate: number;
}

export interface EscalationAnalysis {
  total_escalations: number;
  escalation_rate: number;
  reasons: Array<{ reason: string; count: number }>;
  trend: Array<{ date: string; count: number }>;
}

export interface SourceUsage {
  document_title: string;
  reference_count: number;
  avg_confidence: number;
  last_used: string;
}

export interface PerformanceMetrics {
  avg_response_time_ms: number;
  min_response_time_ms: number;
  max_response_time_ms: number;
  p50_response_time_ms: number;
  p95_response_time_ms: number;
  total_queries: number;
}

export interface TimeSeriesData {
  timestamp: string;
  query_count: number;
  avg_confidence: number;
  escalation_count: number;
}
