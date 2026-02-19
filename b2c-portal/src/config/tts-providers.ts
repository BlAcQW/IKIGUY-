/**
 * TTS Provider Configuration
 *
 * Defines all available TTS providers and their capabilities.
 */

export interface TTSCapabilities {
  voiceCloning: boolean;
  multiLanguage: boolean;
  speedControl: boolean;
  pitchControl: boolean;
  multiSpeaker?: boolean;
  emotionControl?: boolean;
  realTimeConversation?: boolean;
  ssmlSupport?: boolean;
}

export interface TTSProvider {
  id: string;
  name: string;
  endpoint: string;
  status: 'online' | 'offline' | 'building' | 'degraded';
  languages: number;
  languageList?: string[];
  capabilities: TTSCapabilities;
  description: string;
  icon?: string;
  // Real-time monitoring fields
  lastChecked?: string;
  responseTime?: number;
  error?: string;
  gpuMemory?: number;
  modelLoaded?: boolean;
}

export const TTS_PROVIDERS: Record<string, TTSProvider> = {
  coqui_xtts: {
    id: 'coqui_xtts',
    name: 'Coqui XTTS v2',
    endpoint: 'https://coqui.ailabsafrica.com',
    status: 'online',
    languages: 17,
    languageList: ['en', 'es', 'fr', 'de', 'it', 'pt', 'pl', 'tr', 'ru', 'nl', 'cs', 'ar', 'zh-cn', 'hu', 'ko', 'ja', 'hi'],
    capabilities: {
      voiceCloning: true,
      multiLanguage: true,
      speedControl: true,
      pitchControl: false,
      ssmlSupport: true,
    },
    description: 'Multilingual TTS with voice cloning capabilities. Supports 17 languages. Running locally on Docker (Port 8005).',
    icon: '🎙️',
  },
  melotts: {
    id: 'melotts',
    name: 'MeloTTS',
    endpoint: 'https://melotts.ailabsafrica.com',
    status: 'online',
    languages: 6,
    languageList: ['EN', 'ES', 'FR', 'ZH', 'JP', 'KR'],
    capabilities: {
      voiceCloning: false,
      multiLanguage: true,
      speedControl: true,
      pitchControl: true,
      multiSpeaker: true,
      ssmlSupport: true,
    },
    description: 'Fast multilingual synthesis with multi-speaker support. Running locally on Docker (Port 8001).',
    icon: '🔊',
  },
  openvoice: {
    id: 'openvoice',
    name: 'OpenVoice',
    endpoint: 'https://openvoice.ailabsafrica.com',
    status: 'online',
    languages: 2,
    languageList: ['EN', 'ZH'],
    capabilities: {
      voiceCloning: true,
      multiLanguage: true,
      speedControl: false,
      pitchControl: true,
      emotionControl: true,
    },
    description: 'Advanced voice cloning with emotion control. Running locally on Docker (Port 8003).',
    icon: '🎭',
  },
  kokoro: {
    id: 'kokoro',
    name: 'Kokoro TTS',
    endpoint: 'https://kokoro.ailabsafrica.com',
    status: 'building',
    languages: 0,
    capabilities: {
      voiceCloning: false,
      multiLanguage: false,
      speedControl: true,
      pitchControl: false,
    },
    description: 'High-quality TTS synthesis. Currently being deployed.',
    icon: '💬',
  },
  f5tts: {
    id: 'f5tts',
    name: 'F5-TTS',
    endpoint: 'https://f5tts.ailabsafrica.com',
    status: 'online',
    languages: 4,
    languageList: ['en', 'zh', 'ja', 'ko'],
    capabilities: {
      voiceCloning: true,
      multiLanguage: true,
      speedControl: true,
      pitchControl: false,
      emotionControl: false,
      multiSpeaker: false,
    },
    description: 'Flow-matching based TTS with voice cloning. Running on RunPod GPU (A40 46GB).',
    icon: '🌊',
  },
  styletts2: {
    id: 'styletts2',
    name: 'StyleTTS2',
    endpoint: 'https://styletts.ailabsafrica.com',
    status: 'online',
    languages: 1,
    languageList: ['en'],
    capabilities: {
      voiceCloning: true,
      multiLanguage: false,
      speedControl: false,
      pitchControl: false,
      emotionControl: true,
      multiSpeaker: false,
    },
    description: 'High-quality expressive TTS with style transfer and voice cloning. Running on RunPod GPU (A40 46GB).',
    icon: '🎨',
  },
  moshi: {
    id: 'moshi',
    name: 'Kyutai Moshi',
    endpoint: 'https://moshi.ailabsafrica.com',
    status: 'online',
    languages: 1,
    languageList: ['en'],
    capabilities: {
      voiceCloning: false,
      multiLanguage: false,
      speedControl: false,
      pitchControl: false,
      emotionControl: false,
      multiSpeaker: false,
      realTimeConversation: true,
    },
    description: 'Real-time conversational AI with full-duplex dialogue. Running on RunPod GPU (A40 46GB, using 15GB).',
    icon: '⚡',
  },
  crawl4ai: {
    id: 'crawl4ai',
    name: 'Crawl4AI',
    endpoint: 'https://crawl4ai.ailabsafrica.com',
    status: 'online',
    languages: 0,
    capabilities: {
      voiceCloning: false,
      multiLanguage: false,
      speedControl: false,
      pitchControl: false,
    },
    description: 'Web scraping and content extraction service. Utility service for TTS content preparation.',
    icon: '🕷️',
  },
};

export const GHANAIAN_VOICES = [
  {
    id: 'nana_aba',
    name: 'Nana Aba',
    file: 'nana_aba.wav',
    path: '/opt/kasaai/apps/voice-lab/voices/nana_aba.wav',
    size: '6.1MB',
    description: 'Professional female Ghanaian voice',
  },
  {
    id: 'adom_okyere',
    name: 'Adom Okyere',
    file: 'adom_okyere.wav',
    path: '/opt/kasaai/apps/voice-lab/voices/adom_okyere.wav',
    size: '13MB',
    description: 'Male Ghanaian voice',
  },
  {
    id: 'juliet_bawuah',
    name: 'Juliet Bawuah',
    file: 'juliet_bawuah.wav',
    path: '/opt/kasaai/apps/voice-lab/voices/juliet_bawuah.wav',
    size: '3.0MB',
    description: 'Female Ghanaian voice',
  },
  {
    id: 'nana_aba_24bit',
    name: 'Nana Aba (24-bit)',
    file: 'nana_aba_24_bit.wav',
    path: '/opt/kasaai/apps/voice-lab/voices/nana_aba_24_bit.wav',
    size: '9.2MB',
    description: 'High-quality 24-bit professional female Ghanaian voice',
  },
  {
    id: 'archbishop_1',
    name: 'Archbishop 1',
    file: 'archbishop_1_ref.wav',
    path: '/opt/kasaai/apps/voice-lab/voices/archbishop_1_ref.wav',
    size: '751KB',
    description: 'Male Ghanaian voice - Archbishop reference',
  },
  {
    id: 'archbishop_2',
    name: 'Archbishop 2',
    file: 'archbishop_2_ref.wav',
    path: '/opt/kasaai/apps/voice-lab/voices/archbishop_2_ref.wav',
    size: '751KB',
    description: 'Male Ghanaian voice - Archbishop reference',
  },
];

/**
 * Get TTS providers by status
 */
export const getProvidersByStatus = (status: 'online' | 'offline' | 'building') => {
  return Object.values(TTS_PROVIDERS).filter(provider => provider.status === status);
};

/**
 * Get TTS providers with specific capability
 */
export const getProvidersByCapability = (capability: keyof TTSCapabilities) => {
  return Object.values(TTS_PROVIDERS).filter(
    provider => provider.capabilities[capability] === true
  );
};
