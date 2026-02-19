// EventFlow TypeScript Types
// Comprehensive type definitions for the EventFlow application

export type EventStatus = 'planning' | 'active' | 'completed' | 'cancelled';
export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'blocked';
export type TaskPriority = 'critical' | 'high' | 'medium' | 'low';
export type TaskCategory = 'logistics' | 'catering' | 'transport' | 'protocol' | 'marketing' | 'technical' | 'other';
export type NotificationChannel = 'voice' | 'sms' | 'whatsapp' | 'push' | 'email';
export type PricingTier = 'free' | 'basic' | 'premium' | 'enterprise';

// User & Authentication
export interface User {
  id: string;
  phone: string;
  name: string;
  email?: string;
  organization?: string;
  roles: string[];
  wallet_id: string;
  created_at: string;
  last_active: string;
  profile_image_url?: string;
  fcm_token?: string;
  pricing_tier: PricingTier;
}

// Event Management
export interface Event {
  id: string;
  name: string;
  type: string;
  date: string;
  location: string;
  venue_coordinates?: {
    type: 'Point';
    coordinates: [number, number];
  };
  num_guests: number;
  budget_min?: number;
  budget_max?: number;
  status: EventStatus;
  organizer_id: string;
  organizer?: User;
  created_at: string;
  description: string;
  documents: string[];
  tags: string[];
}

// Responsible Person
export interface ResponsiblePerson {
  id: string;
  event_id: string;
  name: string;
  phone: string;
  email?: string;
  role: string;
  user_id?: string;
  created_at: string;
}

// Task Management
export interface Task {
  id: string;
  event_id: string;
  title: string;
  description: string;
  category: TaskCategory;
  priority: TaskPriority;
  status: TaskStatus;
  assigned_to: string;
  assigned_person?: ResponsiblePerson;
  deadline: string;
  created_at: string;
  completed_at?: string;
  depends_on: string[];
  estimated_cost?: number;
  actual_cost?: number;
  notes: string;
  last_followup_at?: string;
  followup_count: number;
}

// Task Update/Activity
export interface TaskUpdate {
  id: string;
  task_id: string;
  update_text: string;
  status: TaskStatus;
  updated_by: 'ai_call' | 'manual' | 'team_member';
  source: NotificationChannel;
  timestamp: string;
  call_recording_url?: string;
  transcription?: string;
}

// Dashboard & Analytics
export interface EventMetrics {
  total_tasks: number;
  completed: number;
  in_progress: number;
  pending: number;
  overdue: number;
  completion_rate: number;
}

export interface CostMetrics {
  total_spent: number;
  voice_calls: number;
  messages_sent: number;
}

export interface DashboardData {
  event: Event;
  tasks: EventMetrics;
  costs: CostMetrics;
  ai_summary: string;
  days_until_event: number;
  next_actions: Recommendation[];
}

// AI Recommendations
export type RecommendationType = 'missing_task' | 'risk_alert' | 'suggestion';
export type RecommendationAction = 'create_task' | 'escalate' | 'remind' | 'none';

export interface Recommendation {
  type: RecommendationType;
  priority: TaskPriority;
  message: string;
  action: RecommendationAction;
  task_id?: string;
  metadata?: Record<string, any>;
}

// Voice AI & Communications
export interface VoiceCall {
  id: string;
  task_id: string;
  responsible_person_id: string;
  status: 'queued' | 'ringing' | 'in-progress' | 'completed' | 'failed' | 'no-answer';
  duration_seconds?: number;
  cost: number;
  started_at?: string;
  ended_at?: string;
  recording_url?: string;
  transcription?: string;
  outcome?: string;
  metadata?: Record<string, any>;
}

export interface Notification {
  id: string;
  event_id?: string;
  task_id?: string;
  recipient_id: string;
  channel: NotificationChannel;
  message: string;
  status: 'pending' | 'sent' | 'delivered' | 'failed';
  cost: number;
  sent_at?: string;
  delivered_at?: string;
  metadata?: Record<string, any>;
}

// Wallet & Payments
export interface Wallet {
  wallet_id: string;
  user_id: string;
  balance: number;
  currency: string;
  status: 'active' | 'suspended' | 'closed';
  created_at: string;
  updated_at: string;
}

export interface Transaction {
  id: string;
  wallet_id: string;
  type: 'credit' | 'debit';
  amount: number;
  description: string;
  balance_after: number;
  status: 'pending' | 'completed' | 'failed' | 'reversed';
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface TopUpRequest {
  amount: number;
  payment_method: 'paystack' | 'stripe' | 'momo';
  callback_url?: string;
}

export interface TopUpResponse {
  transaction_id: string;
  payment_url?: string;
  reference: string;
  status: string;
}

// API Request/Response Types
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface ApiError {
  error: string;
  message: string;
  details?: Record<string, any>;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: ApiError;
  message?: string;
}

// Form & UI State
export interface EventFormData {
  name: string;
  type: string;
  date: string;
  location: string;
  num_guests: number;
  budget_min?: number;
  budget_max?: number;
  description: string;
  responsible_persons: Omit<ResponsiblePerson, 'id' | 'event_id' | 'created_at'>[];
  tags: string[];
}

export interface TaskFormData {
  title: string;
  description: string;
  category: TaskCategory;
  priority: TaskPriority;
  assigned_to: string;
  deadline: string;
  estimated_cost?: number;
  notes: string;
}

// Filter & Sort Options
export interface TaskFilters {
  status?: TaskStatus[];
  category?: TaskCategory[];
  priority?: TaskPriority[];
  assigned_to?: string[];
  overdue?: boolean;
}

export interface EventFilters {
  status?: EventStatus[];
  type?: string[];
  date_from?: string;
  date_to?: string;
}

export type SortOrder = 'asc' | 'desc';

export interface SortOptions {
  field: string;
  order: SortOrder;
}

// Navigation & Routes
export interface NavItem {
  name: string;
  path: string;
  icon: string;
  badge?: number;
}

// Settings & Preferences
export interface UserPreferences {
  notifications: {
    push: boolean;
    email: boolean;
    sms: boolean;
  };
  theme: 'light' | 'dark' | 'auto';
  language: string;
}

// Usage Statistics
export interface UsageStats {
  period: 'day' | 'week' | 'month';
  voice_calls: {
    count: number;
    duration_minutes: number;
    cost: number;
  };
  messages: {
    sms: number;
    whatsapp: number;
    cost: number;
  };
  total_cost: number;
  events_created: number;
  tasks_created: number;
}
