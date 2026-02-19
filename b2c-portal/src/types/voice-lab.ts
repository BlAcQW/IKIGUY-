/**
 * Voice Lab Types
 *
 * Shared TypeScript types for all voice-related features.
 * Extracted from voice-api.ts and assistant-api-client.ts for reusability.
 */

// ============================================================================
// Transcription Types
// ============================================================================

export interface TranscriptionOptions {
  language?: string;
  dialect?: string;
  model?: string;
  enhanceText?: boolean;
  returnTimestamps?: boolean;
  enableVAD?: boolean;
  enableStreaming?: boolean;
}

export interface TranscriptionResult {
  text: string;
  enhancedText?: string;
  confidence: number;
  language?: string;
  dialect?: string;
  duration?: number;
  processingTime?: number;
  timestamps?: Array<{ start: number; end: number; text: string }>;
}

// ============================================================================
// Synthesis Types
// ============================================================================

export interface SynthesisOptions {
  model?: string;
  voiceId?: string;
  language?: string;
  speed?: number;
  pitch?: number;
  dialect?: string;
  enhanceText?: boolean;
  outputFormat?: string;
}

export interface SynthesisResult {
  audioBase64: string;
  text: string;
  voiceId: string;
  duration: number;
  processingTime: number;
  sampleRate: number;
  model: string;
}

// ============================================================================
// Chat/LLM Types
// ============================================================================

export interface ChatOptions {
  message: string;
  model?: string;
  mode?: string;
  history?: Array<{ role: string; content: string }>;
  language?: string;
  dialect?: string;
}

export interface ChatResult {
  response: string;
  model: string;
  processingTime: number;
}

// ============================================================================
// Voice Types
// ============================================================================

export enum VoiceGender {
  Male = 'male',
  Female = 'female',
  Neutral = 'neutral',
}

export interface Voice {
  voice_id: string;
  name: string;
  language: string;
  dialect: string;
  gender: string;
  description?: string;
  sample_rate?: number;
  is_custom?: boolean;
}

export interface VoiceFilters {
  language?: string;
  dialect?: string;
  gender?: VoiceGender;
}

// ============================================================================
// Assistant Types
// ============================================================================

export interface Assistant {
  id: string;
  name: string;
  description?: string;
  system_prompt?: string;
  user_id?: string;
  template_id?: string;
  status?: string;
  llm_provider?: string;
  llm_model?: string;
  tts_provider?: string;
  tts_model?: string;
  tts_voice?: string;
  stt_provider?: string;
  stt_model?: string;
  stt_language?: string;
  language?: string;
  country?: string;
  first_message?: string;
  first_message_mode?: string;
  speed?: number;
  pitch?: number;
  created_at?: string;
  updated_at?: string;
  metadata?: Record<string, any>;
  [key: string]: any; // Allow additional properties
}

export interface FetchAssistantsOptions {
  userId?: string;
  activeOnly?: boolean;
}

export interface CreateAssistantData {
  name: string;
  system_prompt?: string;
  user_id?: string;
  llm_provider?: string;
  llm_model?: string;
  language?: string;
  [key: string]: any;
}

export interface AssistantApiError extends Error {
  statusCode: number;
  details?: any;
}

// ============================================================================
// Model Types
// ============================================================================

export enum ASRModel {
  AkanWhisper = 'akan-whisper',
  MetaMMSASR = 'meta-mms-asr',
  WhisperLargeV3 = 'whisper-large-v3',
}

export enum TTSModel {
  AkanMMS = 'akan-mms',
  MetaMMSTTS = 'meta-mms-tts',
  CoquiXTTS = 'coqui-xtts',
  OpenVoice = 'openvoice',
}

export enum LLMModel {
  GeminiFlash = 'gemini-2.5-flash',
  GPT4Mini = 'gpt-4o-mini',
  ClaudeSonnet = 'claude-3-5-sonnet',
}

export interface ModelInfo {
  id: string;
  name: string;
  accuracy?: string;
  quality?: string;
  context?: string;
  description?: string;
}

export interface ModelCategory {
  name: string;
  variants: ModelInfo[];
}

// ============================================================================
// Dialect Types
// ============================================================================

export enum Dialect {
  Asante = 'asante',
  Akuapem = 'akuapem',
  Fante = 'fante',
}

export interface DialectOption {
  value: string;
  label: string;
}

// ============================================================================
// Conversation Types
// ============================================================================

export enum ConversationMode {
  General = 'general',
  Healthcare = 'healthcare',
  Education = 'education',
  Finance = 'finance',
  CustomerService = 'customer_service',
}

export interface ConversationModeInfo {
  id: string;
  name: string;
  icon: string;
  description?: string;
}

export interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: Date;
}

// ============================================================================
// Voice Cloning Types
// ============================================================================

export interface VoiceCloningOptions {
  referenceAudioBase64: string;
  text: string;
  voiceName: string;
  model?: string;
}

export interface VoiceCloningResult {
  audioBase64: string;
  voiceId: string;
  processingTime: number;
}

// ============================================================================
// WebSocket Types
// ============================================================================

export interface WebSocketMessage {
  type: 'audio' | 'text' | 'control' | 'error';
  data: any;
  timestamp?: number;
}

export interface WebSocketConfig {
  url: string;
  reconnect?: boolean;
  maxReconnectAttempts?: number;
  reconnectInterval?: number;
}

// ============================================================================
// Error Types
// ============================================================================

export interface VoiceLabError {
  code: string;
  message: string;
  details?: any;
  statusCode?: number;
}

export interface ValidationError {
  field: string;
  message: string;
}

// ============================================================================
// Usage & Analytics Types
// ============================================================================

export interface UsageStats {
  transcription_minutes: number;
  synthesis_characters: number;
  llm_tokens: number;
  total_requests: number;
}

export interface VoiceLabAnalytics {
  user_id: string;
  period: 'day' | 'week' | 'month';
  usage: UsageStats;
  timestamp: Date;
}

// ============================================================================
// Configuration Types
// ============================================================================

export interface VoiceLabConfig {
  apiBaseUrl: string;
  defaultLanguage: string;
  defaultDialect: Dialect;
  defaultASRModel: ASRModel;
  defaultTTSModel: TTSModel;
  defaultLLMModel: LLMModel;
  enableStreaming: boolean;
  enableVAD: boolean;
  audioFormat: 'wav' | 'mp3' | 'ogg';
  sampleRate: number;
}

// ============================================================================
// Request/Response Wrappers
// ============================================================================

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: VoiceLabError;
  timestamp: Date;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}
