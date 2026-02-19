/**
 * Centralized API Configuration for ChurchFlow
 *
 * All services use ChurchFlow's own backend with shared routes mounted.
 * TTS, voice library, and wallet endpoints are available via shared routes
 * on the ChurchFlow backend (no need to call core_backend directly).
 */

// ChurchFlow backend - all endpoints (app-specific and shared)
export const CHURCHFLOW_API_URL = import.meta.env.VITE_API_BASE_URL || 'https://churchflow-api.ailabsafrica.com/api/v1';

// API base URL - uses ChurchFlow backend for all services including TTS
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL?.replace('/api/v1', '') || 'https://churchflow-api.ailabsafrica.com';
export const CORE_API_URL = API_BASE_URL;

// WebSocket URLs
export const WS_BASE_URL = API_BASE_URL.replace('https://', 'wss://').replace('http://', 'ws://');

// Helper function to build API endpoints
export const buildApiUrl = (path: string, baseUrl: string = API_BASE_URL): string => {
  const cleanPath = path.startsWith('/') ? path.slice(1) : path;
  const cleanBase = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
  return `${cleanBase}/${cleanPath}`;
};

/**
 * Legacy helper used across the ChurchFlow frontend.
 *
 * Automatically prefixes relative paths with `/api/v1` on the ChurchFlow backend,
 * while allowing full API paths (starting with `api/`) to pass through unchanged.
 *
 * Examples:
 *   getApiUrl('conferences')            -> `${API_BASE_URL}/api/v1/conferences`
 *   getApiUrl('api/v1/conferences')     -> `${API_BASE_URL}/api/v1/conferences`
 *   getApiUrl('/api/v1/registrations')  -> `${API_BASE_URL}/api/v1/registrations`
 */
export const getApiUrl = (path: string, baseUrl: string = API_BASE_URL): string => {
  const cleanBase = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
  let cleanPath = path.trim();

  // Strip leading slash for consistency
  if (cleanPath.startsWith('/')) {
    cleanPath = cleanPath.slice(1);
  }

  // If the path already begins with "api/", assume the caller provided the full API prefix.
  if (cleanPath.startsWith('api/')) {
    return `${cleanBase}/${cleanPath}`;
  }

  // Default: prefix with /api/v1/
  return `${cleanBase}/api/v1/${cleanPath}`;
};

// Common API endpoints
export const API_ENDPOINTS = {
  // TTS Lab - uses core backend
  tts: {
    providers: buildApiUrl('/api/tts/providers'),
    provider: (providerId: string) => buildApiUrl(`/api/tts/providers/${providerId}`),
    synthesize: buildApiUrl('/api/tts/synthesize'),
    voices: buildApiUrl('/api/tts/voices'),
    health: buildApiUrl('/api/tts/health'),
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

  // First Timers - uses ChurchFlow backend
  FIRST_TIMERS: {
    BASE: buildApiUrl('/api/v1/first-timers'),
    STATS: buildApiUrl('/api/v1/first-timers/stats'),
    BY_ID: (id: string) => buildApiUrl(`/api/v1/first-timers/${id}`),
    UPDATE_FOLLOW_UP: (id: string) => buildApiUrl(`/api/v1/first-timers/${id}/follow-up`),
    CONVERT_TO_MEMBER: (id: string) => buildApiUrl(`/api/v1/first-timers/${id}/convert-to-member`),
  },

  // Users/Members - uses ChurchFlow backend
  USERS: {
    BASE: buildApiUrl('/api/v1/users'),
    ME: buildApiUrl('/api/v1/users/me'),
    SEARCH: buildApiUrl('/api/v1/users/search'),
    REGISTER_EXISTING_MEMBER: buildApiUrl('/api/v1/users/register-existing-member'),
  },

  // Branches - uses ChurchFlow backend
  BRANCHES: {
    BASE: buildApiUrl('/api/v1/branches'),
    LIST: buildApiUrl('/api/v1/branches'),
  },
};

export default {
  API_BASE_URL,
  CORE_API_URL,
  CHURCHFLOW_API_URL,
  WS_BASE_URL,
  buildApiUrl,
  getApiUrl,
  API_ENDPOINTS,
};
