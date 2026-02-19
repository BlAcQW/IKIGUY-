/**
 * Centralized API Configuration for StudyFlow
 *
 * All APIs now served from StudyFlow backend (including TTS via shared routes).
 * Core API only used for wallet and voice library services that require centralization.
 */

// StudyFlow backend (includes TTS via shared routes)
export const STUDYFLOW_API_URL = import.meta.env.VITE_API_BASE_URL || 'https://studyflow-api.ailabsafrica.com/api/v1';

// StudyFlow API base (without /api/v1 suffix, for TTS routes at /api/tts)
export const STUDYFLOW_API_BASE = import.meta.env.VITE_API_URL || 'https://studyflow-api.ailabsafrica.com';

// Core backend for wallet and voice library (shared across apps)
export const CORE_API_URL = import.meta.env.VITE_CORE_API_URL || 'https://api.ailabsafrica.com';

// For backward compatibility - points to StudyFlow for app-specific services
export const API_BASE_URL = STUDYFLOW_API_BASE;

// WebSocket URLs
export const WS_BASE_URL = CORE_API_URL.replace('https://', 'wss://').replace('http://', 'ws://');

// StudyFlow WebSocket URL for voice-agent
export const STUDYFLOW_WS_URL = STUDYFLOW_API_BASE.replace('https://', 'wss://').replace('http://', 'ws://');

// Helper function to build API endpoints
export const buildApiUrl = (path: string, baseUrl: string = CORE_API_URL): string => {
  const cleanPath = path.startsWith('/') ? path.slice(1) : path;
  const cleanBase = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
  return `${cleanBase}/${cleanPath}`;
};

// Common API endpoints
export const API_ENDPOINTS = {
  // TTS - uses StudyFlow backend (with shared TTS router)
  tts: {
    providers: buildApiUrl('/api/tts/providers', STUDYFLOW_API_BASE),
    provider: (providerId: string) => buildApiUrl(`/api/tts/providers/${providerId}`, STUDYFLOW_API_BASE),
    synthesize: buildApiUrl('/api/tts/synthesize', STUDYFLOW_API_BASE),
    voices: buildApiUrl('/api/tts/voices', STUDYFLOW_API_BASE),
    health: buildApiUrl('/api/tts/health', STUDYFLOW_API_BASE),
  },

  // Voice Library - uses core backend
  voiceLibrary: {
    base: buildApiUrl('/api/voice-library'),
    voices: buildApiUrl('/api/voice-library/voices'),
    voice: (voiceId: string) => buildApiUrl(`/api/voice-library/${voiceId}`),
    settings: buildApiUrl('/api/voice-library/settings'),
    favorites: {
      list: buildApiUrl('/api/voice-library/favorites/list'),
      add: buildApiUrl('/api/voice-library/favorites/add'),
      remove: buildApiUrl('/api/voice-library/favorites/remove'),
    },
    ratings: {
      add: buildApiUrl('/api/voice-library/ratings/add'),
    },
  },

  // Wallet - uses core backend
  wallet: {
    balance: buildApiUrl('/api/wallet/balance'),
    settings: buildApiUrl('/api/wallet/settings'),
    transactions: buildApiUrl('/api/wallet/transactions'),
  },
};

export default {
  API_BASE_URL,
  CORE_API_URL,
  STUDYFLOW_API_URL,
  WS_BASE_URL,
  buildApiUrl,
  API_ENDPOINTS,
};
