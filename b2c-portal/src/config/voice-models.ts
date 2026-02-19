/**
 * Voice Lab Model Configurations
 *
 * Centralized configuration for ASR, TTS, and LLM models.
 * This file contains all available models and their metadata.
 */

// ============================================================================
// ASR Models (Speech-to-Text)
// ============================================================================

export interface ASRModelVariant {
  id: string;
  name: string;
  accuracy: string;
  verified?: boolean;
}

export interface ASRModelCategory {
  name: string;
  variants: ASRModelVariant[];
}

export const ASR_MODELS: Record<string, ASRModelCategory> = {
  whisper: {
    name: 'Whisper (Ghanaian Languages)',
    variants: [
      { id: 'akan-whisper', name: 'Akan Whisper (GiftMark) - Best for Twi', accuracy: '92.9%', verified: true },
      { id: 'faster-whisper-tiny', name: 'Faster Whisper Tiny (39M)', accuracy: '~75%' },
      { id: 'faster-whisper-base', name: 'Faster Whisper Base (74M)', accuracy: '~85%' },
      { id: 'faster-whisper-small', name: 'Faster Whisper Small (244M)', accuracy: '~90%' },
      { id: 'faster-whisper-medium', name: 'Faster Whisper Medium (769M)', accuracy: '~93%' },
      { id: 'faster-whisper-large', name: 'Faster Whisper Large (1550M)', accuracy: '~95%' },
      { id: 'faster-whisper-large-v3', name: 'Faster Whisper Large v3', accuracy: '~96%' },
    ],
  },
  alternative: {
    name: 'Alternative ASR',
    variants: [
      { id: 'meta-mms', name: 'Meta MMS-1B (1000+ languages)', accuracy: '~88%' },
      { id: 'wav2vec2-akan', name: 'Wav2Vec2 Akan', accuracy: '~85%' },
      { id: 'african-whisper', name: 'African Whisper (Multi-dialect)', accuracy: '~90%' },
    ],
  },
};

// ============================================================================
// TTS Models (Text-to-Speech)
// ============================================================================

export interface TTSModelVariant {
  id: string;
  name: string;
  quality: string;
  verified?: boolean;
}

export interface TTSModelCategory {
  name: string;
  variants: TTSModelVariant[];
}

export const TTS_MODELS: Record<string, TTSModelCategory> = {
  advanced: {
    name: 'Advanced',
    variants: [
      { id: 'xtts-twi-v1', name: 'XTTS Twi v1 (Voice Cloning)', quality: '4.5', verified: true },
      { id: 'f5-tts', name: 'F5-TTS (Zero-shot)', quality: '4.5' },
      { id: 'coqui-tts', name: 'Coqui TTS', quality: '4.2' },
      { id: 'xtts-v2', name: 'XTTS-v2 (Cloning)', quality: '4.4' },
    ],
  },
  lightweight: {
    name: 'Lightweight',
    variants: [
      { id: 'akan-mms', name: 'Akan MMS', quality: '4.0', verified: true },
      { id: 'kokoro-82m', name: 'Kokoro 82M (Mobile)', quality: '3.8' },
      { id: 'meta-mms-tts', name: 'Meta MMS TTS', quality: '4.0' },
      { id: 'chattts', name: 'ChatTTS', quality: '3.9' },
    ],
  },
};

// ============================================================================
// LLM Models (Language Models)
// ============================================================================

export interface LLMModelVariant {
  id: string;
  name: string;
  context: string;
  verified?: boolean;
}

export interface LLMModelCategory {
  name: string;
  variants: LLMModelVariant[];
}

export const LLM_MODELS: Record<string, LLMModelCategory> = {
  cloud: {
    name: 'Cloud LLMs',
    variants: [
      { id: 'gemini-2.5-flash', name: 'Google Gemini 2.5 Flash', context: '1M', verified: true },
      { id: 'gpt-5-mini', name: 'OpenAI GPT-5 Mini', context: '128K' },
      { id: 'claude-sonnet-4', name: 'Anthropic Claude Sonnet 4', context: '200K' },
    ],
  },
  local: {
    name: 'Local LLMs',
    variants: [
      { id: 'llama-3.1-8b', name: 'Llama 3.1 8B', context: '8K' },
      { id: 'mistral-7b', name: 'Mistral 7B', context: '32K' },
      { id: 'qwen-2.5', name: 'Qwen 2.5', context: '128K' },
    ],
  },
};

// ============================================================================
// Conversation Modes
// ============================================================================

export interface ConversationMode {
  id: string;
  name: string;
  icon: string;
}

export const CONVERSATION_MODES: ConversationMode[] = [
  { id: 'healthcare', name: 'Healthcare Assistant', icon: '🏥' },
  { id: 'education', name: 'Educational Tutor', icon: '📚' },
  { id: 'finance', name: 'Financial Advisor', icon: '💰' },
  { id: 'general', name: 'General Assistant', icon: '💬' },
];

// ============================================================================
// Dialect Options
// ============================================================================

export interface DialectOption {
  value: string;
  label: string;
}

export const DIALECT_OPTIONS: DialectOption[] = [
  { value: 'asante', label: 'Asante Twi' },
  { value: 'akuapem', label: 'Akuapem Twi' },
  { value: 'fante', label: 'Fante' },
];

// ============================================================================
// Default Values
// ============================================================================

export const DEFAULT_ASR_MODEL = 'akan-whisper';
export const DEFAULT_TTS_MODEL = 'akan-mms';
export const DEFAULT_LLM_MODEL = 'gemini-2.5-flash';
export const DEFAULT_DIALECT = 'asante';
export const DEFAULT_CONVERSATION_MODE = 'general';

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Get ASR model by ID
 */
export function getASRModel(modelId: string): ASRModelVariant | undefined {
  for (const category of Object.values(ASR_MODELS)) {
    const model = category.variants.find((m) => m.id === modelId);
    if (model) return model;
  }
  return undefined;
}

/**
 * Get TTS model by ID
 */
export function getTTSModel(modelId: string): TTSModelVariant | undefined {
  for (const category of Object.values(TTS_MODELS)) {
    const model = category.variants.find((m) => m.id === modelId);
    if (model) return model;
  }
  return undefined;
}

/**
 * Get LLM model by ID
 */
export function getLLMModel(modelId: string): LLMModelVariant | undefined {
  for (const category of Object.values(LLM_MODELS)) {
    const model = category.variants.find((m) => m.id === modelId);
    if (model) return model;
  }
  return undefined;
}

/**
 * Get all verified ASR models
 */
export function getVerifiedASRModels(): ASRModelVariant[] {
  return Object.values(ASR_MODELS)
    .flatMap((category) => category.variants)
    .filter((model) => model.verified);
}

/**
 * Get all verified TTS models
 */
export function getVerifiedTTSModels(): TTSModelVariant[] {
  return Object.values(TTS_MODELS)
    .flatMap((category) => category.variants)
    .filter((model) => model.verified);
}

/**
 * Get all verified LLM models
 */
export function getVerifiedLLMModels(): LLMModelVariant[] {
  return Object.values(LLM_MODELS)
    .flatMap((category) => category.variants)
    .filter((model) => model.verified);
}

/**
 * Get conversation mode by ID
 */
export function getConversationMode(modeId: string): ConversationMode | undefined {
  return CONVERSATION_MODES.find((mode) => mode.id === modeId);
}

/**
 * Get dialect option by value
 */
export function getDialectOption(dialectValue: string): DialectOption | undefined {
  return DIALECT_OPTIONS.find((dialect) => dialect.value === dialectValue);
}