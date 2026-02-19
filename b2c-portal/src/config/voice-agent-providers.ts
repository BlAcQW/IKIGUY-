/**
 * Voice Agent Provider Configuration
 *
 * Centralized configuration for all LLM, TTS, and ASR providers
 * available in the Voice Agent configuration.
 *
 * Synced with TTS Lab, LLM Lab, and ASR Lab configurations.
 */

export interface ProviderOption {
  value: string;
  label: string;
  status?: 'online' | 'building' | 'training' | 'offline';
  badge?: string; // ✅, 🔵, 🟡, ☁️, 🖥️
  description?: string;
}

export interface VoiceAgentProvider {
  id: string;
  name: string;
  type: 'api' | 'local' | 'cloud';
  status: 'online' | 'building' | 'training' | 'offline';
  endpoint?: string;
}

// ===================================
// LLM PROVIDERS & MODELS
// ===================================

export const LLM_PROVIDERS: Record<string, VoiceAgentProvider> = {
  gemini: {
    id: 'gemini',
    name: 'Google Gemini',
    type: 'cloud',
    status: 'online',
    endpoint: 'https://generativelanguage.googleapis.com',
  },
  openai: {
    id: 'openai',
    name: 'OpenAI',
    type: 'cloud',
    status: 'online',
    endpoint: 'https://api.openai.com',
  },
  anthropic: {
    id: 'anthropic',
    name: 'Anthropic (Claude)',
    type: 'cloud',
    status: 'online',
    endpoint: 'https://api.anthropic.com',
  },
  ollama: {
    id: 'ollama',
    name: 'Ollama (Local GPU)',
    type: 'local',
    status: 'online',
    endpoint: 'https://ollama.ailabsafrica.com',
  },
  ghananlp: {
    id: 'ghananlp',
    name: 'GhanaNLP',
    type: 'api',
    status: 'offline',
  },
  abena_ai: {
    id: 'abena_ai',
    name: 'Abena AI',
    type: 'api',
    status: 'offline',
  },
  meta_mms: {
    id: 'meta_mms',
    name: 'Meta (Llama)',
    type: 'cloud',
    status: 'online',
  },
};

export const LLM_MODELS_BY_PROVIDER: Record<string, ProviderOption[]> = {
  // ===== Cloud API Providers =====
  gemini: [
    { value: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash', status: 'online', badge: '✅ ☁️', description: 'Fastest, recommended for real-time conversations' },
    { value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro', status: 'online', badge: '☁️' },
    { value: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash', status: 'online', badge: '☁️' },
    { value: 'gemini-pro', label: 'Gemini Pro', status: 'online', badge: '☁️' },
  ],
  openai: [
    { value: 'gpt-4o', label: 'GPT-4o', status: 'online', badge: '☁️' },
    { value: 'gpt-4o-mini', label: 'GPT-4o Mini', status: 'online', badge: '☁️', description: 'Fast and cost-effective' },
    { value: 'gpt-4-turbo', label: 'GPT-4 Turbo', status: 'online', badge: '☁️' },
    { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo', status: 'online', badge: '☁️' },
  ],
  anthropic: [
    { value: 'claude-3-5-sonnet-20241022', label: 'Claude 3.5 Sonnet', status: 'online', badge: '☁️' },
    { value: 'claude-3-opus-20240229', label: 'Claude 3 Opus', status: 'online', badge: '☁️' },
    { value: 'claude-3-sonnet-20240229', label: 'Claude 3 Sonnet', status: 'online', badge: '☁️' },
    { value: 'claude-3-haiku-20240307', label: 'Claude 3 Haiku', status: 'online', badge: '☁️', description: 'Fastest Claude model' },
  ],

  // ===== Local GPU Models (Ollama) =====
  ollama: [
    // Fine-tuned Ghanaian Models
    { value: 'kasaai_llama_twi', label: '🇬🇭 KasaAI Llama 3.2 Twi', status: 'training', badge: '🔵 🖥️', description: 'Fine-tuned for Twi & Ghanaian culture (3B, 128K context)' },
    { value: 'kasaai_aya_ghana', label: '🇬🇭 KasaAI Aya-23 Ghana', status: 'training', badge: '🔵 🖥️', description: 'Twi, Akan, Ga, Ewe - 5 languages (8B)' },
    { value: 'kasaai_mistral_ghana', label: '🇬🇭 KasaAI Mistral 7B Ghana', status: 'building', badge: '🟡 🖥️', description: 'Advanced Ghanaian reasoning with cultural context' },

    // Base Models
    { value: 'llama_32_3b', label: '🦙 Llama 3.2 3B (Base)', status: 'online', badge: '✅ 🖥️', description: 'Fast, efficient, 128K context window' },
    { value: 'aya_23_8b', label: '🌐 Aya-23 8B (Base)', status: 'online', badge: '✅ 🖥️', description: 'Excellent multilingual - 23 languages' },
    { value: 'mistral_7b', label: '🌬️ Mistral 7B (Base)', status: 'online', badge: '✅ 🖥️', description: 'High-quality reasoning & code generation' },

    // Specialized Models
    { value: 'llama_32_vision', label: '👁️ Llama 3.2 11B Vision', status: 'building', badge: '🟡 🖥️', description: 'Image understanding + chat capabilities' },
    { value: 'deepseek_coder', label: '💻 DeepSeek Coder 6.7B', status: 'building', badge: '🟡 🖥️', description: '80+ programming languages specialist' },

    // Legacy format (for compatibility)
    { value: 'llama3.2:3b', label: 'Llama 3.2 3B', status: 'online', badge: '✅ 🖥️', description: 'Fast, 2GB, 128K context' },
    { value: 'aya-23:8b', label: 'Aya-23 8B', status: 'online', badge: '✅ 🖥️', description: 'Multilingual, 4.8GB' },
    { value: 'mistral:7b', label: 'Mistral 7B', status: 'online', badge: '✅ 🖥️', description: 'High-quality reasoning, 4.4GB' },
  ],

  // ===== Specialized Providers =====
  ghananlp: [
    { value: 'ghananlp-twi-v1', label: 'GhanaNLP Twi v1', status: 'offline' },
    { value: 'ghananlp-ewe-v1', label: 'GhanaNLP Ewe v1', status: 'offline' },
    { value: 'ghananlp-ga-v1', label: 'GhanaNLP Ga v1', status: 'offline' },
  ],
  abena_ai: [
    { value: 'abena-multilingual-v2', label: 'Abena Multilingual v2', status: 'offline' },
    { value: 'abena-twi-v2', label: 'Abena Twi v2', status: 'offline' },
    { value: 'abena-yoruba-v1', label: 'Abena Yoruba v1', status: 'offline' },
  ],
  meta_mms: [
    { value: 'llama-3-70b', label: 'Llama 3 70B', status: 'online', badge: '☁️' },
    { value: 'llama-3-8b', label: 'Llama 3 8B', status: 'online', badge: '☁️' },
    { value: 'llama-2-70b', label: 'Llama 2 70B', status: 'online', badge: '☁️' },
    { value: 'llama-2-13b', label: 'Llama 2 13B', status: 'online', badge: '☁️' },
  ],
};

// ===================================
// TTS PROVIDERS & VOICES
// ===================================

export const TTS_PROVIDERS: Record<string, VoiceAgentProvider> = {
  meta_mms: {
    id: 'meta_mms',
    name: 'Meta MMS (1000+ languages)',
    type: 'local',
    status: 'online',
    endpoint: 'https://flow-api.ailabsafrica.com',
  },
  xtts: {
    id: 'xtts',
    name: 'XTTS (Voice Cloning)',
    type: 'local',
    status: 'online',
    endpoint: 'https://coqui.ailabsafrica.com',
  },
  f5tts: {
    id: 'f5tts',
    name: 'F5-TTS (Zero-shot Cloning)',
    type: 'local',
    status: 'online',
    endpoint: 'https://f5tts.ailabsafrica.com',
  },
  styletts2: {
    id: 'styletts2',
    name: 'StyleTTS2 (Expressive)',
    type: 'local',
    status: 'online',
    endpoint: 'https://styletts.ailabsafrica.com',
  },
  melotts: {
    id: 'melotts',
    name: 'MeloTTS (Fast)',
    type: 'local',
    status: 'online',
    endpoint: 'https://melotts.ailabsafrica.com',
  },
  openvoice: {
    id: 'openvoice',
    name: 'OpenVoice (Emotion Control)',
    type: 'local',
    status: 'online',
    endpoint: 'https://openvoice.ailabsafrica.com',
  },
  kokoro: {
    id: 'kokoro',
    name: 'Kokoro TTS',
    type: 'local',
    status: 'online',
    endpoint: 'https://kokoro.ailabsafrica.com',
  },
  chatterbox: {
    id: 'chatterbox',
    name: 'Chatterbox (Voice Cloning)',
    type: 'local',
    status: 'online',
    endpoint: 'http://localhost:8004',
  },
  fish_speech: {
    id: 'fish_speech',
    name: 'Fish Speech (Zero-shot)',
    type: 'cloud',
    status: 'online',
    endpoint: 'https://fishspeech.ailabsafrica.com',
  },
  gpt_sovits: {
    id: 'gpt_sovits',
    name: 'GPT-SoVITS (Voice Cloning)',
    type: 'cloud',
    status: 'online',
    endpoint: 'https://gptsovits.ailabsafrica.com',
  },
  zonos: {
    id: 'zonos',
    name: 'Zonos TTS (Emotion Control)',
    type: 'cloud',
    status: 'online',
    endpoint: 'https://zonos.ailabsafrica.com',
  },
  tts_webui: {
    id: 'tts_webui',
    name: 'TTS-WebUI (20+ Models)',
    type: 'cloud',
    status: 'online',
    endpoint: 'https://tts-webui.ailabsafrica.com',
  },
  elevenlabs: {
    id: 'elevenlabs',
    name: 'ElevenLabs',
    type: 'cloud',
    status: 'online',
  },
  coqui_ghanaian: {
    id: 'coqui_ghanaian',
    name: 'Coqui Ghanaian',
    type: 'local',
    status: 'offline',
  },
  openai: {
    id: 'openai',
    name: 'OpenAI TTS',
    type: 'cloud',
    status: 'online',
  },
};

export const TTS_VOICES_BY_PROVIDER: Record<string, ProviderOption[]> = {
  // ===== African Languages (Meta MMS) =====
  meta_mms: [
    { value: 'akan-mms', label: 'Akan/Twi (MMS)', status: 'online', badge: '✅ 🖥️', description: 'Verified for Ghanaian Twi' },
    { value: 'mms-tts-aka', label: 'Akan/Twi (Alt)', status: 'online', badge: '🖥️' },
    { value: 'mms-tts-ewe', label: 'Ewe', status: 'online', badge: '🖥️' },
    { value: 'mms-tts-gaa', label: 'Ga', status: 'online', badge: '🖥️' },
    { value: 'mms-tts-yor', label: 'Yoruba', status: 'online', badge: '🖥️' },
    { value: 'mms-tts-hau', label: 'Hausa', status: 'online', badge: '🖥️' },
    { value: 'mms-tts-swa', label: 'Swahili', status: 'online', badge: '🖥️' },
  ],

  // ===== Voice Cloning Providers =====
  xtts: [
    { value: 'xtts-twi-v1', label: 'XTTS Twi v1 (Voice Cloning)', status: 'online', badge: '✅ 🖥️', description: 'Requires reference audio' },
  ],
  f5tts: [
    { value: 'f5-default', label: 'F5-TTS Default', status: 'online', badge: '✅ 🖥️', description: 'Zero-shot cloning, 4 languages (en, zh, ja, ko)' },
  ],
  styletts2: [
    { value: 'style-default', label: 'StyleTTS2 Default', status: 'online', badge: '✅ 🖥️', description: 'Expressive, English only, requires reference' },
  ],
  melotts: [
    { value: 'melo-en', label: 'English', status: 'online', badge: '✅ 🖥️' },
    { value: 'melo-es', label: 'Spanish', status: 'online', badge: '🖥️' },
    { value: 'melo-fr', label: 'French', status: 'online', badge: '🖥️' },
    { value: 'melo-zh', label: 'Chinese', status: 'online', badge: '🖥️' },
    { value: 'melo-jp', label: 'Japanese', status: 'online', badge: '🖥️' },
    { value: 'melo-kr', label: 'Korean', status: 'online', badge: '🖥️' },
  ],
  openvoice: [
    { value: 'openvoice-en', label: 'English', status: 'online', badge: '✅ 🖥️', description: 'Emotion control' },
    { value: 'openvoice-zh', label: 'Chinese', status: 'online', badge: '🖥️' },
  ],
  kokoro: [
    { value: 'af_heart', label: 'Heart (Female, American)', status: 'online', badge: '✅ 🖥️', description: 'Natural, warm female voice' },
    { value: 'af_bella', label: 'Bella (Female, American)', status: 'online', badge: '🖥️' },
    { value: 'af_nicole', label: 'Nicole (Female, American)', status: 'online', badge: '🖥️' },
    { value: 'am_adam', label: 'Adam (Male, American)', status: 'online', badge: '🖥️' },
    { value: 'am_michael', label: 'Michael (Male, American)', status: 'online', badge: '🖥️' },
    { value: 'bf_emma', label: 'Emma (Female, British)', status: 'online', badge: '🖥️' },
    { value: 'bm_george', label: 'George (Male, British)', status: 'online', badge: '🖥️' },
  ],
  chatterbox: [
    { value: 'chatterbox-default', label: 'Chatterbox Default', status: 'online', badge: '✅ 🖥️', description: 'Expressive voice cloning with reference audio' },
    { value: 'chatterbox-female-1', label: 'Female Voice 1', status: 'online', badge: '🖥️', description: 'Natural female voice' },
    { value: 'chatterbox-male-1', label: 'Male Voice 1', status: 'online', badge: '🖥️', description: 'Natural male voice' },
  ],

  // ===== RunPod GPU Providers =====
  fish_speech: [
    { value: 'fish-default', label: 'Fish Speech Default', status: 'online', badge: '✅ ☁️', description: 'Zero-shot cloning, 8 languages' },
  ],
  gpt_sovits: [
    { value: 'gptsovits-default', label: 'GPT-SoVITS Default', status: 'online', badge: '✅ ☁️', description: 'GPT-based zero-shot cloning' },
  ],
  zonos: [
    { value: 'zonos-default', label: 'Zonos Default', status: 'online', badge: '✅ ☁️', description: 'Emotion control sliders' },
  ],
  tts_webui: [
    { value: 'styletts2', label: 'StyleTTS2', status: 'online', badge: '☁️', description: 'Expressive, high-quality' },
    { value: 'f5-tts', label: 'F5-TTS', status: 'online', badge: '☁️', description: 'Zero-shot cloning' },
    { value: 'voxcpm', label: 'VoxCPM', status: 'online', badge: '✅ ☁️', description: 'Context-aware, voice cloning' },
    { value: 'xtts_v2', label: 'XTTS v2', status: 'online', badge: '☁️', description: 'Voice cloning' },
    { value: 'bark', label: 'Bark', status: 'online', badge: '☁️', description: 'Multilingual, music' },
    { value: 'tortoise', label: 'Tortoise', status: 'online', badge: '☁️', description: 'High quality, slow' },
  ],

  // ===== Cloud Providers =====
  elevenlabs: [
    { value: 'adam', label: 'Adam', status: 'online', badge: '☁️' },
    { value: 'rachel', label: 'Rachel', status: 'online', badge: '☁️' },
    { value: 'sam', label: 'Sam', status: 'online', badge: '☁️' },
    { value: 'josh', label: 'Josh', status: 'online', badge: '☁️' },
    { value: 'emily', label: 'Emily', status: 'online', badge: '☁️' },
  ],
  coqui_ghanaian: [
    { value: 'coqui_twi_female', label: 'Twi Female', status: 'offline' },
    { value: 'coqui_twi_male', label: 'Twi Male', status: 'offline' },
    { value: 'coqui_ewe_female', label: 'Ewe Female', status: 'offline' },
    { value: 'coqui_ga_female', label: 'Ga Female', status: 'offline' },
  ],
  openai: [
    { value: 'alloy', label: 'Alloy', status: 'online', badge: '☁️' },
    { value: 'echo', label: 'Echo', status: 'online', badge: '☁️' },
    { value: 'fable', label: 'Fable', status: 'online', badge: '☁️' },
    { value: 'onyx', label: 'Onyx', status: 'online', badge: '☁️' },
    { value: 'nova', label: 'Nova', status: 'online', badge: '☁️' },
    { value: 'shimmer', label: 'Shimmer', status: 'online', badge: '☁️' },
  ],
};

// ===================================
// ASR/STT PROVIDERS & MODELS
// ===================================

export const ASR_PROVIDERS: Record<string, VoiceAgentProvider> = {
  whisper: {
    id: 'whisper',
    name: 'OpenAI Whisper',
    type: 'local',
    status: 'online',
    endpoint: 'https://flow-api.ailabsafrica.com',
  },
  meta_mms: {
    id: 'meta_mms',
    name: 'Meta MMS',
    type: 'local',
    status: 'online',
    endpoint: 'https://flow-api.ailabsafrica.com',
  },
  seamless_m4t: {
    id: 'seamless_m4t',
    name: 'SeamlessM4T',
    type: 'local',
    status: 'online',
    endpoint: 'https://flow-api.ailabsafrica.com',
  },
  openai: {
    id: 'openai',
    name: 'OpenAI Whisper API',
    type: 'cloud',
    status: 'online',
  },
  google: {
    id: 'google',
    name: 'Google Cloud STT',
    type: 'cloud',
    status: 'online',
  },
  deepgram: {
    id: 'deepgram',
    name: 'Deepgram',
    type: 'cloud',
    status: 'online',
  },
};

export const ASR_MODELS_BY_PROVIDER: Record<string, ProviderOption[]> = {
  // ===== OpenAI Whisper Models (All Variants) =====
  whisper: [
    { value: 'giftmark-akan-whisper', label: 'GiftMark Akan Whisper (92.9% accuracy)', status: 'online', badge: '✅ 🖥️', description: 'Fine-tuned for Twi/Akan, 923MB, 1-2s latency' },
    { value: 'whisper-large-v3', label: 'Whisper Large v3', status: 'online', badge: '✅ 🖥️', description: '99 languages, 3.1GB, 2-5s latency, most accurate' },
    { value: 'whisper-medium', label: 'Whisper Medium', status: 'online', badge: '🖥️', description: 'Balanced size and accuracy' },
    { value: 'whisper-small', label: 'Whisper Small', status: 'online', badge: '🖥️', description: 'Faster processing, good accuracy' },
    { value: 'whisper-base', label: 'Whisper Base', status: 'online', badge: '🖥️', description: 'Lightweight, fastest' },
    { value: 'whisper-tiny', label: 'Whisper Tiny', status: 'online', badge: '🖥️', description: 'Ultra-light, lowest latency' },
    { value: 'faster-whisper-large-v3', label: 'Faster Whisper Large v3', status: 'online', badge: '✅ 🖥️', description: '4x faster than original, 300-800ms latency' },
    { value: 'faster-whisper-medium', label: 'Faster Whisper Medium', status: 'online', badge: '🖥️', description: 'Fast with good accuracy' },
    { value: 'faster-whisper-small', label: 'Faster Whisper Small', status: 'online', badge: '🖥️', description: 'Real-time capable' },
    { value: 'whisper-streaming', label: 'Whisper Streaming', status: 'online', badge: '✅ 🖥️', description: '100-300ms latency, ultra-low latency streaming' },
  ],

  // ===== Meta MMS Models =====
  meta_mms: [
    { value: 'mms-1b-all', label: 'MMS 1B All Languages', status: 'online', badge: '🖥️', description: '1000+ languages' },
    { value: 'mms-1b-aka', label: 'MMS 1B Akan/Twi', status: 'online', badge: '🖥️' },
    { value: 'mms-1b-ewe', label: 'MMS 1B Ewe', status: 'online', badge: '🖥️' },
  ],

  // ===== SeamlessM4T Models =====
  seamless_m4t: [
    { value: 'seamless-m4t-v2-large', label: 'SeamlessM4T v2 Large', status: 'online', badge: '🖥️', description: 'Multilingual speech recognition and translation' },
  ],

  // ===== Cloud API Models =====
  openai: [
    { value: 'whisper-1', label: 'Whisper v1 (Auto-detect)', status: 'online', badge: '☁️', description: 'Cloud API, requires credits' },
  ],
  google: [
    { value: 'google-stt-default', label: 'Google STT Default', status: 'online', badge: '☁️' },
  ],
  deepgram: [
    { value: 'deepgram-nova', label: 'Deepgram Nova', status: 'online', badge: '☁️', description: 'Real-time, high accuracy' },
  ],
};

// ===================================
// HELPER FUNCTIONS
// ===================================

export function getProviderStatus(providerId: string, type: 'llm' | 'tts' | 'asr'): 'online' | 'building' | 'training' | 'offline' {
  let providers: Record<string, VoiceAgentProvider>;

  switch (type) {
    case 'llm':
      providers = LLM_PROVIDERS;
      break;
    case 'tts':
      providers = TTS_PROVIDERS;
      break;
    case 'asr':
      providers = ASR_PROVIDERS;
      break;
  }

  return providers[providerId]?.status || 'offline';
}

export function getProviderType(providerId: string, type: 'llm' | 'tts' | 'asr'): 'api' | 'local' | 'cloud' {
  let providers: Record<string, VoiceAgentProvider>;

  switch (type) {
    case 'llm':
      providers = LLM_PROVIDERS;
      break;
    case 'tts':
      providers = TTS_PROVIDERS;
      break;
    case 'asr':
      providers = ASR_PROVIDERS;
      break;
  }

  return providers[providerId]?.type || 'api';
}

export function isProviderOnline(providerId: string, type: 'llm' | 'tts' | 'asr'): boolean {
  return getProviderStatus(providerId, type) === 'online';
}
