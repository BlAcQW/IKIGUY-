/**
 * API client for ChurchFlow backend
 */

import { getApiUrl } from '../config';
import { encodeHeaderValue } from './header-utils';

// Re-export for convenience
export { getApiUrl };

export interface GreetingAudio {
  audio_url: string;
  text: string;
  duration_seconds?: number;
  provider_used: string;
  cost_usd?: number;
}

export interface VoiceGreetingConfig {
  enabled: boolean;
  greeting_type: 'simple' | 'personalized';
  message_template: string | null;
  tts_provider: string;
  voice_id: string | null;
  speed: number;
  pitch: number;
  language: string;
  personalization_enabled: boolean;
}

export interface VoiceGreetingConfigUpdate {
  enabled?: boolean;
  greeting_type?: 'simple' | 'personalized';
  message_template?: string;
  tts_provider?: string;
  voice_id?: string;
  speed?: number;
  pitch?: number;
  language?: string;
  personalization_enabled?: boolean;
}

export interface VoiceGreetingPreviewRequest {
  message_template: string;
  tts_provider: string;
  voice_id?: string;
  speed?: number;
  pitch?: number;
  language?: string;
  sample_user_data?: {
    user_name?: string;
    branch?: string;
    volunteer_role?: string;
  };
}

/**
 * Get authentication headers for API requests
 */
const getAuthHeaders = (): HeadersInit => {
  const token = localStorage.getItem('access_token');
  const orgId = localStorage.getItem('current_organization_id');
  const encodedOrgId = encodeHeaderValue(orgId);

  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
    ...(encodedOrgId && { 'X-Organization-ID': encodedOrgId })
  };
};

/**
 * Handle API response and auto-logout on 401 Unauthorized
 *
 * This ensures expired or invalid tokens automatically redirect to login
 * instead of showing errors to the user.
 */
const handleApiResponse = async (response: Response): Promise<Response> => {
  if (response.status === 401) {
    console.log('Token expired or invalid - logging out...');

    // Clear all auth data
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_role');
    localStorage.removeItem('user_email');
    sessionStorage.clear();

    // Redirect to login
    window.location.href = '/login?expired=true';

    // Throw to prevent further processing
    throw new Error('Session expired. Please log in again.');
  }

  return response;
};

/**
 * Exchange Supabase token for backend JWT
 *
 * This function gets a fresh Supabase JWT token from the active session
 * and exchanges it for a ChurchFlow backend JWT token. This is necessary
 * because backend API endpoints validate tokens using the backend's SECRET_KEY.
 *
 * @returns Backend JWT token
 * @throws Error if token exchange fails or no valid Supabase session
 */
export const exchangeToken = async (): Promise<string> => {
  // Import supabase dynamically to avoid circular dependencies
  const { supabase } = await import('@/lib/supabase');

  // Get fresh Supabase token from active session
  const { data: { session } } = await supabase.auth.getSession();

  if (!session?.access_token) {
    throw new Error('No valid Supabase session');
  }

  const response = await fetch(
    getApiUrl('auth/exchange-token'),
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json'
      }
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Token exchange failed' }));
    throw new Error(error.detail || 'Token exchange failed');
  }

  const data = await response.json();
  return data.access_token;
};

/**
 * Get voice greeting configuration for a conference
 */
export const getConferenceVoiceGreeting = async (
  conferenceId: string
): Promise<VoiceGreetingConfig> => {
  const response = await fetch(
    getApiUrl(`voice-greetings/conferences/${conferenceId}/voice-greeting`),
    {
      method: 'GET',
      headers: getAuthHeaders()
    }
  );

  await handleApiResponse(response);

  if (!response.ok) {
    throw new Error('Failed to fetch voice greeting configuration');
  }

  return response.json();
};

/**
 * Update voice greeting configuration for a conference
 */
export const updateConferenceVoiceGreeting = async (
  conferenceId: string,
  config: VoiceGreetingConfigUpdate
): Promise<VoiceGreetingConfig> => {
  const response = await fetch(
    getApiUrl(`voice-greetings/conferences/${conferenceId}/voice-greeting`),
    {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(config)
    }
  );

  await handleApiResponse(response);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update voice greeting configuration');
  }

  return response.json();
};

/**
 * Preview voice greeting for a conference
 */
export const previewConferenceVoiceGreeting = async (
  conferenceId: string,
  previewRequest: VoiceGreetingPreviewRequest
): Promise<GreetingAudio> => {
  const response = await fetch(
    getApiUrl(`voice-greetings/conferences/${conferenceId}/voice-greeting/preview`),
    {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(previewRequest)
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to generate preview');
  }

  return response.json();
};

/**
 * Get voice greeting configuration for a bus route
 */
export const getBusRouteVoiceGreeting = async (
  routeId: string
): Promise<VoiceGreetingConfig> => {
  const response = await fetch(
    getApiUrl(`voice-greetings/buses/routes/${routeId}/voice-greeting`),
    {
      method: 'GET',
      headers: getAuthHeaders()
    }
  );

  if (!response.ok) {
    throw new Error('Failed to fetch voice greeting configuration');
  }

  return response.json();
};

/**
 * Update voice greeting configuration for a bus route
 */
export const updateBusRouteVoiceGreeting = async (
  routeId: string,
  config: VoiceGreetingConfigUpdate
): Promise<VoiceGreetingConfig> => {
  const response = await fetch(
    getApiUrl(`voice-greetings/buses/routes/${routeId}/voice-greeting`),
    {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(config)
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update voice greeting configuration');
  }

  return response.json();
};

/**
 * Preview voice greeting for a bus route
 */
export const previewBusRouteVoiceGreeting = async (
  routeId: string,
  previewRequest: VoiceGreetingPreviewRequest
): Promise<GreetingAudio> => {
  const response = await fetch(
    getApiUrl(`voice-greetings/buses/routes/${routeId}/voice-greeting/preview`),
    {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(previewRequest)
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to generate preview');
  }

  return response.json();
};
