/**
 * ASR Provider Configuration
 *
 * Defines all available ASR (Automatic Speech Recognition) providers and their capabilities.
 */

export interface ASRCapabilities {
  realtime: boolean;
  multiLanguage: boolean;
  diarization: boolean; // Speaker identification
  punctuation: boolean;
  timestamps: boolean;
  wordLevelTimestamps?: boolean;
  customVocabulary?: boolean;
  noiseReduction?: boolean;
}

export interface ASRProvider {
  id: string;
  name: string;
  endpoint: string;
  status: 'online' | 'offline' | 'building';
  languages: number;
  languageList?: string[];
  capabilities: ASRCapabilities;
  description: string;
  icon?: string;
  modelSize?: string;
  latency?: string; // e.g., "100ms", "500ms", "2s"
}

export const ASR_PROVIDERS: Record<string, ASRProvider> = {
  whisper: {
    id: 'whisper',
    name: 'OpenAI Whisper',
    endpoint: 'https://flow-api.ailabsafrica.com/api/voice-lab/transcribe',
    status: 'online',
    languages: 99,
    languageList: ['tw', 'ak', 'en', 'es', 'fr', 'de', 'zh', 'ja', 'ko', 'ar', 'hi', 'ru', 'pt'], // Partial list
    capabilities: {
      realtime: true,  // Enabled via Faster Whisper and streaming variants
      multiLanguage: true,
      diarization: true,
      punctuation: true,
      timestamps: true,
      wordLevelTimestamps: true,
      customVocabulary: false,
      noiseReduction: true,
    },
    description: 'OpenAI Whisper models including GiftMark fine-tuned variant (92.9% accuracy for Akan/Twi), standard models, and Faster Whisper optimizations. Multiple model sizes available for different use cases.',
    icon: '🎙️',
    modelSize: 'Varies (39MB to 3.1GB)',
    latency: 'Varies by model (100ms to 5s)',
  },

  meta_mms: {
    id: 'meta_mms',
    name: 'Meta MMS',
    endpoint: 'https://flow-api.ailabsafrica.com/api/mms/transcribe',
    status: 'online',
    languages: 1000,
    languageList: ['tw', 'ak', 'ee', 'gaa', 'dag', 'ha', 'yo', 'ig', 'zu', 'sw'], // Subset of supported languages
    capabilities: {
      realtime: false,
      multiLanguage: true,
      diarization: false,
      punctuation: true,
      timestamps: true,
      wordLevelTimestamps: false,
      customVocabulary: false,
      noiseReduction: true,
    },
    description: 'Meta Massively Multilingual Speech model. Supports 1000+ languages including many African languages.',
    icon: '🌍',
    modelSize: '1.9GB',
    latency: '2-4s',
  },

  seamless_m4t: {
    id: 'seamless_m4t',
    name: 'SeamlessM4T',
    endpoint: 'https://flow-api.ailabsafrica.com/seamless',
    status: 'building',
    languages: 100,
    capabilities: {
      realtime: false,
      multiLanguage: true,
      diarization: false,
      punctuation: true,
      timestamps: true,
      wordLevelTimestamps: false,
      customVocabulary: false,
      noiseReduction: true,
    },
    description: 'Meta\'s multimodal and multilingual AI translation model.',
    icon: '🌐',
    modelSize: '2.3GB',
    latency: '3-5s',
  },

  pyannote_diarization: {
    id: 'pyannote_diarization',
    name: 'Pyannote Diarization',
    endpoint: 'https://flow-api.ailabsafrica.com/diarization',
    status: 'building',
    languages: 0, // Language agnostic
    capabilities: {
      realtime: false,
      multiLanguage: false,
      diarization: true,
      punctuation: false,
      timestamps: true,
      wordLevelTimestamps: false,
      customVocabulary: false,
      noiseReduction: false,
    },
    description: 'Speaker diarization - identifies who spoke when.',
    icon: '👥',
    modelSize: '17MB',
    latency: '1-2s',
  },

  nemo_asr: {
    id: 'nemo_asr',
    name: 'NVIDIA NeMo',
    endpoint: 'https://flow-api.ailabsafrica.com/nemo',
    status: 'offline',
    languages: 50,
    capabilities: {
      realtime: true,
      multiLanguage: true,
      diarization: false,
      punctuation: true,
      timestamps: true,
      wordLevelTimestamps: true,
      customVocabulary: true,
      noiseReduction: true,
    },
    description: 'NVIDIA\'s neural modules for ASR.',
    icon: '🎮',
    modelSize: '1.2GB',
    latency: '500ms',
  },

  custom_akan_asr: {
    id: 'custom_akan_asr',
    name: 'Custom Akan ASR',
    endpoint: 'https://flow-api.ailabsafrica.com/akan-custom',
    status: 'building',
    languages: 1,
    capabilities: {
      realtime: false,
      multiLanguage: false,
      diarization: false,
      punctuation: true,
      timestamps: true,
      wordLevelTimestamps: false,
      customVocabulary: true,
      noiseReduction: true,
    },
    description: 'Custom trained model specifically for Akan language.',
    icon: '🇬🇭',
    modelSize: '450MB',
    latency: '1-2s',
  },
};