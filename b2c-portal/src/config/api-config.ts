/**
 * Centralized API Configuration
 * All API endpoints should use these constants instead of hardcoded URLs
 */

// Main API URLs
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://api.ailabsafrica.com';
export const CORE_API_URL = import.meta.env.VITE_CORE_API_URL || 'https://api.ailabsafrica.com';
export const PUBLIC_API_URL = import.meta.env.VITE_PUBLIC_API_URL || 'https://api.ailabsafrica.com';

// WebSocket URLs (automatically derived from API URLs)
export const WS_BASE_URL = API_BASE_URL.replace('https://', 'wss://').replace('http://', 'ws://');
export const CORE_WS_URL = CORE_API_URL.replace('https://', 'wss://').replace('http://', 'ws://');

// External service URLs (can be overridden by env vars)
export const VAPI_API_URL = import.meta.env.VITE_VAPI_API_URL || 'https://api.vapi.ai';
export const N8N_API_URL = import.meta.env.VITE_N8N_API_URL || 'https://automate.inspirecreations.it.com/api/v1';
export const N8N_WEBHOOK_URL = N8N_API_URL.replace('/api/v1', '');

// Helper function to build API endpoints
export const buildApiUrl = (path: string, baseUrl: string = API_BASE_URL): string => {
  // Remove leading slash from path if present
  const cleanPath = path.startsWith('/') ? path.slice(1) : path;
  // Ensure base URL doesn't end with slash
  const cleanBase = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
  return `${cleanBase}/${cleanPath}`;
};

// Common API endpoints
export const API_ENDPOINTS = {
  // Auth endpoints
  auth: {
    login: buildApiUrl('/auth/login'),
    logout: buildApiUrl('/auth/logout'),
    signup: buildApiUrl('/auth/signup'),
    refresh: buildApiUrl('/auth/refresh'),
  },

  // Voice endpoints
  voice: {
    assistants: buildApiUrl('/voice/assistants'),
    stt: buildApiUrl('/voice/stt'),
    tts: buildApiUrl('/voice/tts'),
    vad: buildApiUrl('/voice/vad'),
    session: {
      start: buildApiUrl('/voice/session/start'),
      stop: buildApiUrl('/voice/session/stop'),
    },
    lab: {
      transcribe: buildApiUrl('/api/voice-lab/transcribe'),
      synthesize: buildApiUrl('/api/voice-lab/synthesize'),
      voices: buildApiUrl('/api/voice-lab/voices'),
      cloneVoice: buildApiUrl('/api/voice-lab/clone-voice'),
      streamWs: `${WS_BASE_URL}/api/voice-lab/ws/stream`,  // WebSocket streaming endpoint
    },
  },

  // Admin endpoints
  admin: {
    users: buildApiUrl('/api/admin/users'),
    universalAdmin: (userId: string) => buildApiUrl(`/api/admin/users/${userId}/universal-admin-status`),
  },

  // Custom tools
  customTools: {
    base: buildApiUrl('/custom-tools'),
    search: buildApiUrl('/custom-tools/search'),
    register: buildApiUrl('/custom-tools/db/register'),
    summary: (clientId: string) => buildApiUrl(`/custom-tools/summary/${clientId}`),
    analytics: (toolId: string) => buildApiUrl(`/custom-tools/analytics/${toolId}`),
    init: buildApiUrl('/custom-tools/init/premier-health'),
  },

  // App settings
  appSettings: {
    base: buildApiUrl('/api/app-settings'),
    industries: buildApiUrl('/api/app-settings/industries/available'),
    templates: buildApiUrl('/api/app-settings/templates/by-industry'),
  },

  // Analytics
  analytics: {
    voiceInteractions: buildApiUrl('/analytics/voice-interactions'),
  },

  // Automation Analytics
  automationAnalytics: {
    base: (configId: string) => buildApiUrl(`/api/automation-analytics/${configId}`),
    summary: (configId: string) => buildApiUrl(`/api/automation-analytics/${configId}/summary`),
    calls: (configId: string) => buildApiUrl(`/api/automation-analytics/${configId}/calls`),
    refresh: (configId: string) => buildApiUrl(`/api/automation-analytics/${configId}/refresh`),
    sync: (configId: string) => buildApiUrl(`/api/automation-analytics/${configId}/sync`),
    health: (configId: string) => buildApiUrl(`/api/automation-analytics/${configId}/health`),
  },

  // Health services
  healthServices: {
    search: buildApiUrl('/health-services/search'),
  },

  // TTS Lab
  tts: {
    providers: buildApiUrl('/api/tts/providers'),
    provider: (providerId: string) => buildApiUrl(`/api/tts/providers/${providerId}`),
    synthesize: buildApiUrl('/api/tts/synthesize'),
    synthesizeUpload: buildApiUrl('/api/tts/synthesize/upload'),
    clone: buildApiUrl('/api/tts/clone'),
    estimateCost: buildApiUrl('/api/tts/estimate-cost'),
    voices: buildApiUrl('/api/tts/voices'),
    voice: (filename: string) => buildApiUrl(`/api/tts/voices/${filename}`),
    health: buildApiUrl('/api/tts/health'),
    batch: buildApiUrl('/api/tts/batch'),
  },

  // LLM Lab
  llm: {
    providers: buildApiUrl('/api/llm/providers'),
    provider: (providerId: string) => buildApiUrl(`/api/llm/providers/${providerId}`),
    chat: buildApiUrl('/api/llm/chat'),
    chatStream: buildApiUrl('/api/llm/chat/stream'),
    estimateCost: buildApiUrl('/api/llm/estimate-cost'),
    health: buildApiUrl('/api/llm/health'),
  },

  // ASR Lab
  asr: {
    providers: buildApiUrl('/api/asr/providers'),
    provider: (providerId: string) => buildApiUrl(`/api/asr/providers/${providerId}`),
    transcribe: buildApiUrl('/api/asr/transcribe'),
    transcribeUpload: buildApiUrl('/api/asr/transcribe/upload'),
    estimateCost: buildApiUrl('/api/asr/estimate-cost'),
    languages: (providerId: string) => buildApiUrl(`/api/asr/languages/${providerId}`),
    health: buildApiUrl('/api/asr/health'),
  },

  // Wallet & Billing
  wallet: {
    balance: buildApiUrl('/api/wallet/balance'),
    settings: buildApiUrl('/api/wallet/settings'),
    paymentMethods: buildApiUrl('/api/wallet/payment-methods'),
    paymentMethod: (methodId: string) => buildApiUrl(`/api/wallet/payment-methods/${methodId}`),
    deposit: buildApiUrl('/api/wallet/deposit'),
    transactions: buildApiUrl('/api/wallet/transactions'),
    transaction: (txId: string) => buildApiUrl(`/api/wallet/transactions/${txId}`),
    providers: buildApiUrl('/api/wallet/providers'),
    webhooks: {
      stripe: buildApiUrl('/api/wallet/webhooks/stripe'),
      flutterwave: buildApiUrl('/api/wallet/webhooks/flutterwave'),
      momo: buildApiUrl('/api/wallet/webhooks/momo-callback'),
      mpesa: buildApiUrl('/api/wallet/webhooks/mpesa-callback'),
    },
  },

  // Asterisk Telephony
  asterisk: {
    base: 'https://asterisk-api.ailabsafrica.com',
    ws: 'wss://asterisk-api.ailabsafrica.com/ws/events',
    health: 'https://asterisk-api.ailabsafrica.com/health',
    status: 'https://asterisk-api.ailabsafrica.com/asterisk/status',
    reload: 'https://asterisk-api.ailabsafrica.com/asterisk/reload',
    callHistory: 'https://asterisk-api.ailabsafrica.com/call-history',
    metrics: 'https://asterisk-api.ailabsafrica.com/metrics',
    alerts: 'https://asterisk-api.ailabsafrica.com/alerts',
    originateCall: buildApiUrl('/asterisk/call/originate'),
    sip: {
      peer: 'https://asterisk-api.ailabsafrica.com/sip/peer',
      peers: 'https://asterisk-api.ailabsafrica.com/sip/peers',
      peerDetail: (username: string) => `https://asterisk-api.ailabsafrica.com/sip/peer/${username}`,
    },
    call: {
      route: 'https://asterisk-api.ailabsafrica.com/call/route',
    },
  },

  // Phone Numbers Management
  phoneNumbers: {
    list: buildApiUrl('/phone-numbers'),
    provision: buildApiUrl('/phone-numbers/provision'),
    import: buildApiUrl('/phone-numbers/import'),
    delete: (numberId: string) => buildApiUrl(`/phone-numbers/${numberId}`),
    assign: (numberId: string) => buildApiUrl(`/phone-numbers/${numberId}/assign`),
    unassign: (numberId: string) => buildApiUrl(`/phone-numbers/${numberId}/unassign`),
    providers: buildApiUrl('/phone-numbers/providers/available'),
    byAssistant: (assistantId: string) => buildApiUrl(`/phone-numbers/assistant/${assistantId}`),
  },

  // SIP Registration
  sipRegistration: {
    generateQr: buildApiUrl('/sip-registration/generate-qr'),
    status: (sipUsername: string) => buildApiUrl(`/sip-registration/status/${sipUsername}`),
    antCellular: buildApiUrl('/sip-registration/ant-cellular/status'),
  },

  // Vapi Integration
  vapi: {
    webhook: buildApiUrl('/api/vapi/webhook'),
    call: {
      outbound: buildApiUrl('/api/vapi/call/outbound'),
      end: (callId: string) => buildApiUrl(`/api/vapi/call/${callId}`),
      status: (callId: string) => buildApiUrl(`/api/vapi/call/${callId}/status`),
      active: buildApiUrl('/api/vapi/calls/active'),
    },
  },
};

export default {
  API_BASE_URL,
  CORE_API_URL,
  PUBLIC_API_URL,
  WS_BASE_URL,
  CORE_WS_URL,
  VAPI_API_URL,
  N8N_API_URL,
  N8N_WEBHOOK_URL,
  buildApiUrl,
  API_ENDPOINTS,
};