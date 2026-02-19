/**
 * Book Types
 *
 * Type definitions for book-related features including visibility controls,
 * moderation, and audit logging.
 */

export type BookVisibility = 'draft' | 'unlisted' | 'private' | 'public';

export interface Book {
  id: string;
  title: string;
  author: string;
  description?: string;
  cover_url?: string;
  author_image_url?: string;
  genre?: string | string[];
  duration?: number;
  processing_status: string;
  created_at?: string;

  // Visibility and moderation
  visibility?: BookVisibility;
  visibility_badge?: string;
  is_hidden?: boolean;
  hidden_by?: string;
  hidden_by_email?: string;
  hidden_reason?: string;
  hidden_at?: string;

  // Progress tracking
  progress?: number;
  last_position?: number;
}

export interface AuditLogEntry {
  id: string;
  action: string;
  entity_id: string;
  actor_id: string;
  actor_email: string;
  actor_role: string;
  reason?: string;
  changes: Record<string, any>;
  metadata: Record<string, any>;
  created_at: string;
}

export interface HiddenBook {
  id: string;
  title: string;
  author: string;
  description?: string;
  cover_url?: string;
  uploaded_by?: string;
  visibility: BookVisibility;
  hidden_by?: string;
  hidden_by_email?: string;
  hidden_at?: string;
  hidden_reason?: string;
}

export interface VisibilityOption {
  value: BookVisibility;
  label: string;
  description: string;
  icon: string;
  color: string;
  badgeColor: string;
}
