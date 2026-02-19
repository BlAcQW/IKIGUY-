/**
 * SSE Event Type Definitions
 *
 * TypeScript type definitions for Server-Sent Events (SSE) used across
 * campaign management systems (SMS, Voice, WhatsApp).
 *
 * These types match the backend event definitions in:
 * /opt/kasaai/apps/shared/services/campaign_events.py
 */

// ==================== Base Event ====================

export interface SSEEvent {
  campaign_id: string;
  event_type: string;
  timestamp: string;
}

// ==================== SMS Campaign Events ====================

export interface SMSProgress {
  total_recipients: number;
  sent: number;
  delivered: number;
  failed: number;
  pending: number;
}

export interface SMSCampaignProgressEvent extends SSEEvent {
  event_type: 'sms_progress';
  progress: SMSProgress;
  total_cost: number;
  status?: string;
}

export interface SMSStatusChangeEvent extends SSEEvent {
  event_type: 'sms_status_change';
  old_status: string;
  new_status: string;
  reason?: string;
}

export interface SMSMessageSentEvent extends SSEEvent {
  event_type: 'sms_message_sent';
  message_id: string;
  recipient_name: string;
  recipient_phone: string;
  cost: number;
}

export interface SMSMessageFailedEvent extends SSEEvent {
  event_type: 'sms_message_failed';
  message_id: string;
  recipient_name: string;
  recipient_phone: string;
  error_message: string;
}

// ==================== Voice Campaign Events ====================

export interface VoiceProgress {
  calls_made: number;
  calls_total: number;
  success_count: number;
  failed_count: number;
  in_progress_count: number;
  success_rate: number;
  avg_duration: number;
}

export interface VoiceProgressEvent extends SSEEvent {
  event_type: 'voice_progress';
  calls_made: number;
  calls_total: number;
  success_count: number;
  failed_count: number;
  in_progress_count?: number;
  success_rate: number;
  avg_duration?: number;
  current_cost: number;
  status?: string;
}

export interface CallCompletedEvent extends SSEEvent {
  event_type: 'call_completed';
  call_id: string;
  contact_name: string;
  phone_number: string;
  duration: number;
  status: 'success' | 'failed';
  transcript_available: boolean;
  summary?: string;
  cost: number;
  error_message?: string;
}

export interface CallStartedEvent extends SSEEvent {
  event_type: 'call_started';
  call_id: string;
  contact_name: string;
  phone_number: string;
}

export interface CallFailedEvent extends SSEEvent {
  event_type: 'call_failed';
  call_id: string;
  contact_name: string;
  phone_number: string;
  error_message: string;
}

export interface VoiceStatusChangeEvent extends SSEEvent {
  event_type: 'voice_status_change';
  old_status: string;
  new_status: string;
  reason?: string;
}

// ==================== WhatsApp Campaign Events ====================

export interface WhatsAppProgress {
  total_recipients: number;
  sent: number;
  delivered: number;
  read: number;
  failed: number;
  pending: number;
}

export interface WhatsAppProgressEvent extends SSEEvent {
  event_type: 'whatsapp_progress';
  progress: WhatsAppProgress;
  total_cost: number;
  status?: string;
}

export interface WhatsAppStatusChangeEvent extends SSEEvent {
  event_type: 'whatsapp_status_change';
  old_status: string;
  new_status: string;
  reason?: string;
}

export interface WhatsAppMessageSentEvent extends SSEEvent {
  event_type: 'whatsapp_message_sent';
  message_id: string;
  recipient_name: string;
  recipient_phone: string;
  cost: number;
}

// ==================== General Events ====================

export interface CampaignCompletedEvent extends SSEEvent {
  event_type: 'campaign_completed';
  message: string;
  final_stats?: Record<string, any>;
}

export interface CampaignErrorEvent extends SSEEvent {
  event_type: 'campaign_error';
  error_message: string;
  error_type?: string;
  recoverable: boolean;
}

export interface AudienceProcessingEvent extends SSEEvent {
  event_type: 'audience_processing';
  phase: 'loading' | 'filtering' | 'building_queue' | 'complete';
  contacts_discovered: number;
  contacts_filtered: number;
  queue_size: number;
  message?: string;
}

export interface InitialEvent extends SSEEvent {
  event_type: 'initial';
  data: Record<string, any>;
}

// ==================== Union Types ====================

/**
 * Union type for all SMS campaign events
 */
export type SMSCampaignEvent =
  | SMSCampaignProgressEvent
  | SMSStatusChangeEvent
  | SMSMessageSentEvent
  | SMSMessageFailedEvent;

/**
 * Union type for all voice campaign events
 */
export type VoiceCampaignEvent =
  | VoiceProgressEvent
  | CallCompletedEvent
  | CallStartedEvent
  | CallFailedEvent
  | VoiceStatusChangeEvent;

/**
 * Union type for all WhatsApp campaign events
 */
export type WhatsAppCampaignEvent =
  | WhatsAppProgressEvent
  | WhatsAppStatusChangeEvent
  | WhatsAppMessageSentEvent;

/**
 * Union type for all campaign SSE events
 */
export type CampaignSSEEvent =
  | SMSCampaignEvent
  | VoiceCampaignEvent
  | WhatsAppCampaignEvent
  | CampaignCompletedEvent
  | CampaignErrorEvent
  | AudienceProcessingEvent
  | InitialEvent;

// ==================== Type Guards ====================

/**
 * Type guard to check if event is SMS progress event
 */
export function isSMSProgressEvent(event: SSEEvent): event is SMSCampaignProgressEvent {
  return event.event_type === 'sms_progress';
}

/**
 * Type guard to check if event is voice progress event
 */
export function isVoiceProgressEvent(event: SSEEvent): event is VoiceProgressEvent {
  return event.event_type === 'voice_progress';
}

/**
 * Type guard to check if event is call completed event
 */
export function isCallCompletedEvent(event: SSEEvent): event is CallCompletedEvent {
  return event.event_type === 'call_completed';
}

/**
 * Type guard to check if event is campaign completed event
 */
export function isCampaignCompletedEvent(event: SSEEvent): event is CampaignCompletedEvent {
  return event.event_type === 'campaign_completed';
}

/**
 * Type guard to check if event is campaign error event
 */
export function isCampaignErrorEvent(event: SSEEvent): event is CampaignErrorEvent {
  return event.event_type === 'campaign_error';
}

// ==================== Utility Types ====================

/**
 * Extract event data from event type
 */
export type EventData<T extends SSEEvent> = Omit<T, 'campaign_id' | 'event_type' | 'timestamp'>;

/**
 * Campaign status values
 */
export type CampaignStatus =
  | 'draft'
  | 'scheduled'
  | 'running'
  | 'paused'
  | 'completed'
  | 'failed'
  | 'cancelled';

/**
 * Event type string literals
 */
export type EventTypeString =
  | 'sms_progress'
  | 'sms_status_change'
  | 'sms_message_sent'
  | 'sms_message_failed'
  | 'voice_progress'
  | 'voice_status_change'
  | 'call_completed'
  | 'call_started'
  | 'call_failed'
  | 'whatsapp_progress'
  | 'whatsapp_status_change'
  | 'whatsapp_message_sent'
  | 'campaign_completed'
  | 'campaign_error'
  | 'audience_processing'
  | 'initial';
