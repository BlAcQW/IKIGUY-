/**
 * Voice Settings Type Definitions
 *
 * Shared types for voice configuration across KasaAI applications.
 */

// ============================================================================
// TTS Types
// ============================================================================

export interface TTSSettings {
  default_provider: string;
  default_voice: string | null;
  speed: number;
  pitch: number;
}

export interface TTSProvider {
  id: string;
  name: string;
  description: string;
  endpoint: string;
  status: 'online' | 'offline' | 'building' | 'training';
  languages: number;
  languageList: string[];
  capabilities: {
    voiceCloning: boolean;
    multiLanguage: boolean;
    speedControl: boolean;
    multiSpeaker: boolean;
    realTimeConversation?: boolean;
  };
  cost?: {
    input: number;
    output: number;
  };
  baseModel?: string;
  modelSize?: string;
  contextWindow?: number;
  maxTokens?: number;
  fineTuned?: boolean;
  trainingData?: string;
}

export interface SynthesisRequest {
  text: string;
  language?: string;
  speaker?: string | number;
  speed?: number;
  pitch?: number;
  onProgress?: (progress: number, stage: string) => void;
}

export interface VoiceCloningRequest {
  text: string;
  referenceAudio: File;
  language?: string;
  alpha?: number;
  beta?: number;
  diffusion_steps?: number;
  embedding_scale?: number;
  onProgress?: (progress: number, stage: string) => void;
}

export interface CostEstimate {
  estimated_cost: number;
  character_count: number;
  provider_id: string;
}

// ============================================================================
// ASR Types
// ============================================================================

export interface ASRSettings {
  default_provider: string;
  language: string;
  task: 'transcribe' | 'translate';
}

export interface ASRProvider {
  id: string;
  name: string;
  endpoint: string;
  status: 'online' | 'offline' | 'degraded';
  last_check: string;
  response_time_ms: number | null;
  error_message: string | null;
  provider_type: 'asr';
}

export interface TranscriptionRequest {
  audio: File | Blob;
  language?: string;
  task?: 'transcribe' | 'translate';
  responseFormat?: 'json' | 'text' | 'srt' | 'vtt';
  temperature?: number;
  timestampGranularities?: string[];
}

export interface TranscriptionSegment {
  id: number;
  start: number;
  end: number;
  text: string;
  tokens?: number[];
  temperature?: number;
  avg_logprob?: number;
  compression_ratio?: number;
  no_speech_prob?: number;
}

export interface TranscriptionResult {
  text: string;
  providerId: string;
  language?: string;
  duration?: number;
  segments?: TranscriptionSegment[];
  cost: number;
  transactionId?: string;
  processingTime: number;
  modelName?: string;
}

// ============================================================================
// LLM Types
// ============================================================================

export interface LLMSettings {
  default_model: string;
  temperature: number;
  max_tokens: number;
}

export interface LLMProvider {
  id: string;
  name: string;
  description: string;
  endpoint: string;
  status: 'online' | 'offline' | 'degraded' | 'training' | 'building';
  last_check: string;
  response_time_ms: number | null;
  error_message: string | null;
  provider_type: 'llm';
  baseModel?: string;
  modelSize?: string;
  contextWindow?: number;
  maxTokens?: number;
  languages?: string;
  cost?: {
    input: number;
    output: number;
  };
  capabilities?: {
    streaming: boolean;
    multiLanguage: boolean;
    culturalContext: boolean;
    functionCalling: boolean;
    reasoning: boolean;
    codeGeneration: boolean;
    vision: boolean;
  };
  fineTuned?: boolean;
  trainingData?: string;
}

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  messages: ChatMessage[];
  temperature?: number;
  maxTokens?: number;
  topP?: number;
  streaming?: boolean;
  systemPrompt?: string;
}

export interface ChatResponse {
  message: string;
  modelId: string;
  usage: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
  finishReason: string;
  cost: number;
  transactionId?: string;
  processingTime: number;
}

// ============================================================================
// Voice Library Types
// ============================================================================

export interface VoicePreferences {
  favorite_voices: string[];
  custom_voices: string[];
}

export interface ClonedVoice {
  voice_id: string;
  name: string;
  provider: string;
  reference_audio_path: string;
  reference_audio_size: number;
  cloned_at: string;
  language: string;
  gender: 'male' | 'female' | 'neutral';
  accent: string;
  description: string;
  capabilities: string[];
  status: 'pending' | 'processing' | 'completed' | 'failed';
  error_message?: string;
}

// ============================================================================
// Complete Voice Settings
// ============================================================================

export interface VoiceSettings {
  user_id: string;
  organization_id: string;
  tts: TTSSettings;
  asr: ASRSettings;
  llm: LLMSettings;
  voices: VoicePreferences;
  created_at?: string;
  updated_at?: string;
}

// ============================================================================
// API Response Types
// ============================================================================

export interface ProvidersResponse<T> {
  providers: Record<string, T>;
  count: number;
  online_count: number;
  offline_count: number;
}

export interface VoiceSettingsResponse {
  success: boolean;
  data: VoiceSettings;
  message?: string;
}

export interface VoiceSettingsUpdateRequest {
  tts?: Partial<TTSSettings>;
  asr?: Partial<ASRSettings>;
  llm?: Partial<LLMSettings>;
  voices?: Partial<VoicePreferences>;
}
