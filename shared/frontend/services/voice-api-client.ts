/**
 * Voice API Client
 *
 * Centralized API client for voice services (TTS, ASR, LLM, Voice Lab)
 * Handles authentication, error handling, and request/response formatting.
 *
 * @author KasaAI
 * @date 2025-11-03
 */

import type { VoiceSettings, VoiceSettingsUpdateRequest } from '../types';

export class VoiceAPIClient {
  private baseUrl: string;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || import.meta?.env?.VITE_API_URL || 'http://localhost:30027';
  }

  /**
   * Generic GET request
   */
  private async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || errorData.message || `Request failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Generic POST request
   */
  private async post<T, D = any>(endpoint: string, data?: D): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: data ? JSON.stringify(data) : undefined,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || errorData.message || `Request failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Generic PUT request
   */
  private async put<T, D = any>(endpoint: string, data: D): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'PUT',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || errorData.message || `Request failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Generic DELETE request
   */
  private async delete<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'DELETE',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || errorData.message || `Request failed: ${response.statusText}`);
    }

    return response.json();
  }

  // ============================================================================
  // Voice Settings API
  // ============================================================================

  /**
   * Get user voice settings
   */
  async getMySettings(): Promise<VoiceSettings> {
    return this.get<VoiceSettings>('/api/voice-settings/my-settings');
  }

  /**
   * Update user voice settings
   */
  async updateMySettings(updates: VoiceSettingsUpdateRequest): Promise<VoiceSettings> {
    return this.put<VoiceSettings, VoiceSettingsUpdateRequest>('/api/voice-settings/my-settings', updates);
  }

  /**
   * Get organization default settings
   */
  async getOrgDefaults(): Promise<VoiceSettings> {
    return this.get<VoiceSettings>('/api/voice-settings/org-defaults');
  }

  /**
   * Update organization default settings (admin only)
   */
  async updateOrgDefaults(settings: VoiceSettingsUpdateRequest): Promise<VoiceSettings> {
    return this.put<VoiceSettings, VoiceSettingsUpdateRequest>('/api/voice-settings/org-defaults', settings);
  }

  // ============================================================================
  // TTS API
  // ============================================================================

  /**
   * Get available TTS providers
   */
  async getTTSProviders(forceRefresh: boolean = false) {
    return this.get(`/api/tts/providers${forceRefresh ? '?force_refresh=true' : ''}`);
  }

  /**
   * Get TTS provider details
   */
  async getTTSProvider(providerId: string) {
    return this.get(`/api/tts/providers/${providerId}`);
  }

  /**
   * Synthesize speech
   */
  async synthesize(request: any) {
    return this.post('/api/tts/synthesize', request);
  }

  /**
   * Estimate TTS cost
   */
  async estimateTTSCost(text: string, providerId: string, voiceCloning: boolean = false) {
    return this.post('/api/tts/estimate-cost', {
      provider_id: providerId,
      text,
      voice_cloning: voiceCloning,
    });
  }

  // ============================================================================
  // ASR API
  // ============================================================================

  /**
   * Get available ASR providers
   */
  async getASRProviders(forceRefresh: boolean = false) {
    return this.get(`/api/asr/providers${forceRefresh ? '?force_refresh=true' : ''}`);
  }

  /**
   * Get ASR provider details
   */
  async getASRProvider(providerId: string) {
    return this.get(`/api/asr/providers/${providerId}`);
  }

  /**
   * Get supported languages for ASR provider
   */
  async getASRLanguages(providerId: string) {
    return this.get(`/api/asr/languages/${providerId}`);
  }

  // ============================================================================
  // LLM API
  // ============================================================================

  /**
   * Get available LLM providers
   */
  async getLLMProviders(forceRefresh: boolean = false) {
    return this.get(`/api/llm/providers${forceRefresh ? '?force_refresh=true' : ''}`);
  }

  /**
   * Get LLM provider details
   */
  async getLLMProvider(providerId: string) {
    return this.get(`/api/llm/providers/${providerId}`);
  }

  /**
   * Chat with LLM
   */
  async chat(request: any) {
    return this.post('/api/llm/chat', request);
  }

  /**
   * Estimate LLM cost
   */
  async estimateLLMCost(modelId: string, inputText: string) {
    return this.post('/api/llm/estimate-cost', {
      model_id: modelId,
      input_text: inputText,
    });
  }

  // ============================================================================
  // Voice Lab API
  // ============================================================================

  /**
   * Get voice library
   */
  async getVoices() {
    return this.get('/api/voice-lab/voices');
  }

  /**
   * Get cloned voices
   */
  async getClonedVoices(provider?: string, status?: string) {
    const params = new URLSearchParams();
    if (provider) params.append('provider', provider);
    if (status) params.append('status', status);
    const query = params.toString();
    return this.get(`/api/voice-lab/voices/cloned${query ? `?${query}` : ''}`);
  }

  /**
   * Get library voices
   */
  async getLibraryVoices() {
    return this.get('/api/voice-lab/library-voices');
  }
}

/**
 * Default API client instance
 */
export const voiceAPI = new VoiceAPIClient();
