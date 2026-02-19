/**
 * useComprehensiveTTS Hook
 *
 * React hook to fetch and manage comprehensive TTS providers from backend.
 * Fetches from /api/tts/providers endpoint which uses @shared/tts/config.py
 *
 * Features:
 * - List TTS providers with health status
 * - Synthesize speech with automatic billing
 * - Clone voices from reference audio
 * - Estimate synthesis costs
 * - Check wallet balance
 * - Cache statistics
 *
 * Usage:
 * ```tsx
 * const {
 *   providers,
 *   loading,
 *   error,
 *   synthesize,
 *   cloneVoice,
 *   estimateCost,
 *   walletBalance,
 *   cacheStats,
 *   refetch
 * } = useComprehensiveTTS(apiBaseUrl, userId);
 * ```
 */

import { useState, useEffect } from 'react';
import type { TTSProviderInfo } from '../components/voice-settings/ComprehensiveTTSSelector';
import type {
  TTSRequest,
  TTSResponse,
  VoiceCloneRequest,
  AudioFormat,
  TTSProvider,
} from '../types/tts';

export interface SynthesizeRequest {
  user_id: string;
  text: string;
  provider?: string;
  language?: string;
  speaker?: string;
  speed?: number;
  output_format?: AudioFormat;
  sample_rate?: number;
}

export interface VoiceCloneRequestWithUser {
  user_id: string;
  text: string;
  reference_audio: Uint8Array;
  provider?: string;
  language?: string;
  speed?: number;
  output_format?: AudioFormat;
  sample_rate?: number;
}

export interface SynthesizeResponse {
  audio?: Uint8Array;
  audio_url?: string;
  format: AudioFormat;
  sample_rate: number;
  duration?: number;
  provider: string;
  language: string;
  cost: number;
  transaction_id: string;
  processing_time?: number;
}

export interface CostEstimate {
  text_length: number;
  provider_id: string;
  voice_cloning: boolean;
  estimated_cost: number;
  currency: string;
  pricing_tier: string;
}

export interface CacheStats {
  total_entries: number;
  cache_hits: number;
  cache_misses: number;
  hit_rate: number;
  total_size_bytes: number;
  total_size_mb: number;
  avg_entry_size_bytes: number;
  oldest_entry?: Date;
  newest_entry?: Date;
}

export interface WalletBalance {
  balance: number;
  currency: string;
  formatted: string;
}

export interface UseComprehensiveTTSResult {
  providers: TTSProviderInfo[];
  loading: boolean;
  error: string | null;
  walletBalance: WalletBalance | null;
  synthesize: (request: Omit<SynthesizeRequest, 'user_id'>) => Promise<SynthesizeResponse>;
  cloneVoice: (request: Omit<VoiceCloneRequestWithUser, 'user_id'>) => Promise<SynthesizeResponse>;
  estimateCost: (text: string, provider: string, voiceCloning?: boolean) => Promise<CostEstimate>;
  cacheStats: () => Promise<CacheStats>;
  refetch: () => void;
}

export function useComprehensiveTTS(
  apiBaseUrl: string,
  userId?: string,
  options?: {
    onlineOnly?: boolean;
    autoFetch?: boolean;
    endpointPath?: string;
    getAuthHeaders?: () => Promise<Record<string, string>> | Record<string, string>;
    skipWalletBalance?: boolean;  // Skip wallet balance fetching
  }
): UseComprehensiveTTSResult {
  const [providers, setProviders] = useState<TTSProviderInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [walletBalance, setWalletBalance] = useState<WalletBalance | null>(null);

  const fetchProviders = async () => {
    setLoading(true);
    setError(null);

    try {
      const endpointPath = options?.endpointPath || '/tts/providers';

      // Convert /api/v1 base URL to /api for TTS routes
      const ttsBaseUrl = (apiBaseUrl || '').replace(/\/v1\/?$/, '');

      // Get auth headers if provided
      const authHeaders = options?.getAuthHeaders ? await options.getAuthHeaders() : {};

      const response = await fetch(`${ttsBaseUrl}${endpointPath}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...authHeaders,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch TTS providers: ${response.statusText}`);
      }

      const data = await response.json();

      // Transform backend response to match our interface
      // Backend returns {providers: {id: {...}, ...}, count: N}
      const providersDict = data.providers || {};
      const providerArray = Object.values(providersDict);

      const transformedProviders: TTSProviderInfo[] = providerArray.map((p: any) => ({
        id: p.provider || p.id, // Backend uses 'provider' field for ID
        name: p.name,
        description: p.description || '',
        status: p.status || 'online',
        deployment: getDeployment(p.endpoint),
        endpoint: p.endpoint || '',
        capabilities: {
          voice_cloning: p.capabilities?.voiceCloning || p.capabilities?.voice_cloning || false,
          multi_language: p.capabilities?.multiLanguage || p.capabilities?.multi_language || false,
          speed_control: p.capabilities?.speedControl || p.capabilities?.speed_control || false,
          pitch_control: p.capabilities?.pitchControl || p.capabilities?.pitch_control || false,
          multi_speaker: p.capabilities?.multiSpeaker || p.capabilities?.multi_speaker || false,
          multi_model: p.capabilities?.multi_model || false,
          emotion_control: p.capabilities?.emotionControl || p.capabilities?.emotion_control || false,
          real_time_conversation: p.capabilities?.realTimeConversation || p.capabilities?.real_time_conversation || false,
          ssml_support: p.capabilities?.ssml_support || false,
          streaming: p.capabilities?.streaming || false,
          supported_languages: p.languageList || p.capabilities?.supported_languages || [],
          supported_formats: p.capabilities?.supported_formats || [],
          available_models: p.capabilities?.available_models || [],
        },
        languages: p.languagesDict || convertLanguagesToDict(p.languageList || p.capabilities?.supported_languages || []),
        speakers: p.speakers || {},
        icon: p.icon || getProviderIcon(p.provider || p.id),
      }));

      // Filter online only if requested
      const filteredProviders = options?.onlineOnly
        ? transformedProviders.filter(p => p.status === 'online')
        : transformedProviders;

      setProviders(filteredProviders);
    } catch (err: any) {
      console.error('Error fetching TTS providers:', err);
      setError(err.message || 'Failed to fetch TTS providers');

      // Set default providers as fallback
      setProviders(getDefaultProviders());
    } finally {
      setLoading(false);
    }
  };

  // Synthesize speech with automatic billing
  const synthesize = async (request: Omit<SynthesizeRequest, 'user_id'>): Promise<SynthesizeResponse> => {
    if (!userId) {
      throw new Error('User ID is required for synthesis');
    }

    const authHeaders = options?.getAuthHeaders ? await options.getAuthHeaders() : {};

    // Convert /api/v1 base URL to /api for TTS routes
    const ttsBaseUrl = apiBaseUrl.replace(/\/v1\/?$/, '');

    const response = await fetch(`${ttsBaseUrl}/tts/synthesize`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...authHeaders,
      },
      body: JSON.stringify({
        user_id: userId,
        ...request,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(errorData.detail || 'Synthesis failed');
    }

    const data = await response.json();

    // Update wallet balance if transaction was successful
    if (data.transaction_id && walletBalance) {
      setWalletBalance({
        ...walletBalance,
        balance: walletBalance.balance - data.cost,
        formatted: `${walletBalance.currency} ${(walletBalance.balance - data.cost).toFixed(2)}`,
      });
    }

    return data;
  };

  // Clone voice from reference audio
  const cloneVoice = async (request: Omit<VoiceCloneRequestWithUser, 'user_id'>): Promise<SynthesizeResponse> => {
    if (!userId) {
      throw new Error('User ID is required for voice cloning');
    }

    const authHeaders = options?.getAuthHeaders ? await options.getAuthHeaders() : {};

    // Convert Uint8Array to base64 for JSON transmission
    const base64Audio = btoa(
      String.fromCharCode(...Array.from(request.reference_audio))
    );

    // Convert /api/v1 base URL to /api for TTS routes
    const ttsBaseUrl = apiBaseUrl.replace(/\/v1\/?$/, '');

    const response = await fetch(`${ttsBaseUrl}/tts/clone-voice`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...authHeaders,
      },
      body: JSON.stringify({
        user_id: userId,
        text: request.text,
        reference_audio: base64Audio,
        provider: request.provider,
        language: request.language,
        speed: request.speed,
        output_format: request.output_format,
        sample_rate: request.sample_rate,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(errorData.detail || 'Voice cloning failed');
    }

    const data = await response.json();

    // Update wallet balance
    if (data.transaction_id && walletBalance) {
      setWalletBalance({
        ...walletBalance,
        balance: walletBalance.balance - data.cost,
        formatted: `${walletBalance.currency} ${(walletBalance.balance - data.cost).toFixed(2)}`,
      });
    }

    return data;
  };

  // Estimate synthesis cost
  const estimateCost = async (
    text: string,
    provider: string,
    voiceCloning: boolean = false
  ): Promise<CostEstimate> => {
    const authHeaders = options?.getAuthHeaders ? await options.getAuthHeaders() : {};

    const params = new URLSearchParams({
      text,
      provider,
      voice_cloning: voiceCloning.toString(),
    });

    // Convert /api/v1 base URL to /api for TTS routes
    const ttsBaseUrl = apiBaseUrl.replace(/\/v1\/?$/, '');

    const response = await fetch(`${ttsBaseUrl}/tts/estimate-cost?${params}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...authHeaders,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(errorData.detail || 'Cost estimation failed');
    }

    return response.json();
  };

  // Get cache statistics
  const getCacheStats = async (): Promise<CacheStats> => {
    const authHeaders = options?.getAuthHeaders ? await options.getAuthHeaders() : {};

    // Convert /api/v1 base URL to /api for TTS routes
    const ttsBaseUrl = apiBaseUrl.replace(/\/v1\/?$/, '');

    const response = await fetch(`${ttsBaseUrl}/tts/cache/stats`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...authHeaders,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(errorData.detail || 'Failed to fetch cache stats');
    }

    return response.json();
  };

  // Fetch wallet balance
  const fetchWalletBalance = async () => {
    if (!userId || options?.skipWalletBalance) return;

    try {
      const authHeaders = options?.getAuthHeaders ? await options.getAuthHeaders() : {};

      const response = await fetch(`${apiBaseUrl}/wallet/balance`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...authHeaders,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setWalletBalance({
          balance: data.balance || 0,
          currency: data.currency || 'GHS',
          formatted: `${data.currency || 'GHS'} ${(data.balance || 0).toFixed(2)}`,
        });
      }
    } catch (err) {
      console.warn('Failed to fetch wallet balance:', err);
      // Don't set error state - wallet is optional
    }
  };

  useEffect(() => {
    if (options?.autoFetch !== false) {
      fetchProviders();
      fetchWalletBalance();
    }
  }, [apiBaseUrl, userId]);

  return {
    providers,
    loading,
    error,
    walletBalance,
    synthesize,
    cloneVoice,
    estimateCost,
    cacheStats: getCacheStats,
    refetch: () => {
      fetchProviders();
      fetchWalletBalance();
    },
  };
}

// Helper function to determine deployment type from endpoint
function getDeployment(endpoint: string): 'runpod' | 'local' | 'cloud' {
  if (!endpoint) return 'local';
  if (endpoint.includes('runpod') || endpoint.includes('f5tts') || endpoint.includes('styletts') || endpoint.includes('moshi') || endpoint.includes('tts-webui') || endpoint.includes('fishspeech')) {
    return 'runpod';
  }
  return 'local';
}

// Helper function to convert language list to dictionary
function convertLanguagesToDict(languageList: string[]): Record<string, string> {
  const languageNames: Record<string, string> = {
    en: 'English', es: 'Spanish', fr: 'French', de: 'German', it: 'Italian',
    pt: 'Portuguese', pl: 'Polish', tr: 'Turkish', ru: 'Russian', nl: 'Dutch',
    cs: 'Czech', ar: 'Arabic', 'zh-cn': 'Chinese (Simplified)', hu: 'Hungarian',
    ko: 'Korean', ja: 'Japanese', hi: 'Hindi', zh: 'Chinese',
    EN: 'English', ES: 'Spanish', FR: 'French', ZH: 'Chinese', JP: 'Japanese', KR: 'Korean',
  };

  const result: Record<string, string> = {};
  languageList.forEach(code => {
    result[code] = languageNames[code] || code.toUpperCase();
  });
  return result;
}

// Helper function to assign icons to providers
function getProviderIcon(providerId: string): string {
  const iconMap: Record<string, string> = {
    f5tts: '🎵',
    styletts2: '🎨',
    moshi: '🤖',
    coqui_xtts: '🎭',
    melotts: '🎼',
    openvoice: '🎪',
    kokoro: '🌸',
    tts_webui: '🎛️',
    fish_speech: '🐠',
    zonos: '🌊',
    parler_tts: '🗣️',
    indextts: '📇',
    voxcpm: '🎙️',
    gpt_sovits: '🎬',
  };
  return iconMap[providerId] || '🔊';
}

// Default providers if API fetch fails
function getDefaultProviders(): TTSProviderInfo[] {
  return [
    {
      id: 'f5tts',
      name: 'F5-TTS',
      description: 'Flow-matching based TTS with voice cloning. Running on RunPod GPU.',
      status: 'online',
      deployment: 'runpod',
      endpoint: 'https://f5tts.ailabsafrica.com',
      capabilities: {
        voice_cloning: true,
        multi_language: true,
        speed_control: true,
        streaming: true,
        supported_languages: ['en', 'zh', 'ja', 'ko'],
        supported_formats: ['wav', 'mp3'],
      },
      languages: {
        en: 'English',
        zh: 'Chinese',
        ja: 'Japanese',
        ko: 'Korean',
      },
      icon: '🎵',
    },
    {
      id: 'styletts2',
      name: 'StyleTTS2',
      description: 'High-quality expressive TTS with style transfer. Running on RunPod GPU.',
      status: 'online',
      deployment: 'runpod',
      endpoint: 'https://styletts.ailabsafrica.com',
      capabilities: {
        voice_cloning: true,
        emotion_control: true,
        streaming: true,
        supported_languages: ['en'],
        supported_formats: ['wav', 'mp3'],
      },
      languages: {
        en: 'English',
      },
      icon: '🎨',
    },
    {
      id: 'kokoro',
      name: 'Kokoro TTS',
      description: 'Fast, high-quality TTS with natural prosody. Based on Kokoro-82M model.',
      status: 'online',
      deployment: 'local',
      endpoint: 'https://kokoro.ailabsafrica.com',
      capabilities: {
        multi_speaker: true,
        speed_control: true,
        pitch_control: true,
        supported_languages: ['en'],
        supported_formats: ['wav', 'mp3'],
      },
      languages: {
        en: 'English',
      },
      speakers: {
        af_heart: 'Heart (female, American)',
        af_bella: 'Bella (female, American)',
        af_nicole: 'Nicole (female, American)',
        af_sarah: 'Sarah (female, American)',
        af_sky: 'Sky (female, American)',
        am_adam: 'Adam (male, American)',
        am_michael: 'Michael (male, American)',
        bf_emma: 'Emma (female, British)',
        bf_isabella: 'Isabella (female, British)',
        bm_george: 'George (male, British)',
        bm_lewis: 'Lewis (male, British)',
      },
      icon: '🌸',
    },
    {
      id: 'tts_webui',
      name: 'TTS-WebUI',
      description: 'Comprehensive TTS platform with 20+ models including StyleTTS2, RVC, XTTS, F5-TTS, and more.',
      status: 'online',
      deployment: 'runpod',
      endpoint: 'https://tts-webui.ailabsafrica.com',
      capabilities: {
        voice_cloning: true,
        multi_language: true,
        multi_model: true,
        speed_control: true,
        emotion_control: true,
        streaming: true,
        supported_languages: ['en', 'es', 'fr', 'de', 'zh', 'ja', 'ko', 'pt', 'ru'],
        supported_formats: ['wav', 'mp3', 'pcm'],
        available_models: [
          'styletts2', 'rvc', 'bark', 'tortoise', 'melotts', 'mms',
          'f5-tts', 'xtts_v2', 'openvoice', 'kokoro', 'parler-tts',
          'whisper', 'musicgen', 'stable-audio', 'demucs',
          'gpt-sovits', 'chatterbox', 'mahaTTS', 'vall-e-x',
        ],
      },
      languages: {
        en: 'English',
        es: 'Spanish',
        fr: 'French',
        de: 'German',
        zh: 'Chinese',
        ja: 'Japanese',
        ko: 'Korean',
        pt: 'Portuguese',
        ru: 'Russian',
      },
      icon: '🎛️',
    },
  ];
}
