/**
 * API Client for StudyFlow Backend
 *
 * Handles all HTTP requests to the backend API with authentication.
 */

import { getAuthToken } from './auth-utils';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

// Export API_BASE_URL for use in hooks
export { API_BASE_URL };

/**
 * Get current organization ID from localStorage
 */
function getCurrentOrganizationId(): string | null {
  return localStorage.getItem('current_organization_id');
}

/**
 * Make an authenticated API request
 *
 * NOTE: This function retrieves the Supabase JWT token from the active session.
 * The token is automatically refreshed by Supabase when needed.
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  // Get token from Supabase session (async operation)
  let token: string | null = null;
  try {
    token = await getAuthToken();
  } catch (error) {
    // Token retrieval failed (likely not authenticated)
    console.warn('Failed to get auth token:', error);
  }

  const organizationId = getCurrentOrganizationId();

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  if (organizationId) {
    headers['X-Organization-Id'] = organizationId;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
    throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
  }

  // Handle 204 No Content (DELETE returns this)
  if (response.status === 204) {
    return {} as T;
  }

  // Handle empty responses
  const text = await response.text();
  if (!text) {
    return {} as T;
  }

  return JSON.parse(text);
}

// ============================================================================
// AUTHENTICATION API
// ============================================================================

export const authApi = {
  async login(email: string, password: string) {
    // Supabase auth is handled client-side, just verify with backend
    return apiRequest('/auth/me', {
      method: 'GET',
    });
  },

  async register(data: {
    email: string;
    password: string;
    full_name: string;
    role: string;
  }) {
    return apiRequest('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async getCurrentUser() {
    return apiRequest('/auth/me', {
      method: 'GET',
    });
  },
};

// ============================================================================
// ANALYTICS API
// ============================================================================

export const analyticsApi = {
  async getDashboardStats(days: number = 30) {
    return apiRequest(`/analytics/dashboard?days=${days}`, {
      method: 'GET',
    });
  },

  async getUserMetrics(days: number = 30) {
    return apiRequest(`/analytics/users?days=${days}`, {
      method: 'GET',
    });
  },

  async getContentAnalytics(days: number = 30) {
    return apiRequest(`/analytics/content?days=${days}`, {
      method: 'GET',
    });
  },

  async getSystemHealth() {
    return apiRequest('/analytics/system/health', {
      method: 'GET',
    });
  },

  async getFinancialAnalytics(days: number = 30) {
    return apiRequest(`/analytics/financial?days=${days}`, {
      method: 'GET',
    });
  },

  async getTopUsers(metric: 'questions' | 'sessions' | 'learning_time', limit: number = 10) {
    return apiRequest(`/analytics/top-users?metric=${metric}&limit=${limit}`, {
      method: 'GET',
    });
  },
};

// ============================================================================
// USAGE API
// ============================================================================

export const usageApi = {
  async getMyUsage(days: number = 30, serviceType?: string) {
    const params = new URLSearchParams({ days: days.toString() });
    if (serviceType) params.append('service_type', serviceType);
    return apiRequest(`/usage/me?${params}`, {
      method: 'GET',
    });
  },

  async getUsageSummary(days: number = 30) {
    return apiRequest(`/usage/summary?days=${days}`, {
      method: 'GET',
    });
  },

  async getMyTier() {
    return apiRequest('/usage/tier', {
      method: 'GET',
    });
  },

  async estimateCost(inputTokens: number, outputTokens: number, numQueries: number = 1) {
    const params = new URLSearchParams({
      input_tokens: inputTokens.toString(),
      output_tokens: outputTokens.toString(),
      num_queries: numQueries.toString(),
    });
    return apiRequest(`/usage/estimate?${params}`, {
      method: 'POST',
    });
  },

  async getPricingTiers() {
    return apiRequest('/usage/tiers', {
      method: 'GET',
    });
  },
};

// ============================================================================
// MATERIALS API
// ============================================================================

export const materialsApi = {
  async upload(file: File, data: {
    title: string;
    subject: string;
    grade?: number;
    description?: string;
    topics?: string[];
  }) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', data.title);
    formData.append('subject', data.subject);
    if (data.grade !== undefined) formData.append('grade', data.grade.toString());
    if (data.description) formData.append('description', data.description);
    if (data.topics && data.topics.length > 0) {
      formData.append('topics', data.topics.join(','));
    }

    let token: string;
    try {
      token = await getAuthToken();
    } catch (error) {
      throw new Error('Authentication required. Please log in again.');
    }

    const organizationId = getCurrentOrganizationId();

    // Debug logging (remove after verification)
    console.log('[DEBUG] Upload token:', token ? 'Present' : 'Missing');
    console.log('[DEBUG] Upload headers:', {
      'Authorization': `Bearer ${token.substring(0, 20)}...`,
      'X-Organization-Id': organizationId || 'None'
    });

    const response = await fetch(`${API_BASE_URL}/materials/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        ...(organizationId && { 'X-Organization-Id': organizationId }),
      },
      body: formData,
    });

    if (response.status === 401) {
      throw new Error('Session expired. Please log in again.');
    }

    if (response.status === 403) {
      throw new Error('Access denied. Only teachers and admins can upload materials.');
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(error.detail || 'Upload failed');
    }

    return response.json();
  },

  async list(params?: {
    subject?: string;
    grade?: number;
    school_id?: string;
    status?: string;
    limit?: number;
    skip?: number;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.subject) queryParams.append('subject', params.subject);
    if (params?.grade !== undefined) queryParams.append('grade', params.grade.toString());
    if (params?.school_id) queryParams.append('school_id', params.school_id);
    if (params?.status) queryParams.append('status', params.status);
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString());
    if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString());

    const url = queryParams.toString() ? `/materials/?${queryParams}` : '/materials/';
    return apiRequest(url, {
      method: 'GET',
    });
  },

  async get(id: string) {
    return apiRequest(`/materials/${id}`, {
      method: 'GET',
    });
  },

  async update(id: string, data: {
    title?: string;
    subject?: string;
    grade?: number;
    description?: string;
    topics?: string[];
  }) {
    return apiRequest(`/materials/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  async delete(id: string) {
    return apiRequest(`/materials/${id}`, {
      method: 'DELETE',
    });
  },
};

// ============================================================================
// TUTORING API
// ============================================================================

export const tutoringApi = {
  async createSession(data: {
    subject: string;
    topics?: string[];
  }) {
    return apiRequest('/tutoring/sessions', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async askQuestion(data: {
    session_id: string;
    question_text: string;
    subject: string;
    topic?: string;
  }) {
    return apiRequest('/tutoring/ask', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async getSession(id: string) {
    return apiRequest(`/tutoring/sessions/${id}`, {
      method: 'GET',
    });
  },

  async endSession(id: string) {
    return apiRequest(`/tutoring/sessions/${id}/end`, {
      method: 'POST',
    });
  },
};

// ============================================================================
// PROGRESS API
// ============================================================================

export const progressApi = {
  async getMyProgress() {
    return apiRequest('/progress/me', {
      method: 'GET',
    });
  },

  async getWeeklySummary() {
    return apiRequest('/progress/weekly-summary', {
      method: 'GET',
    });
  },

  async getStreak() {
    return apiRequest('/progress/streak', {
      method: 'GET',
    });
  },

  async getTopicMastery() {
    return apiRequest('/progress/topics', {
      method: 'GET',
    });
  },
};

// ============================================================================
// WALLET API
// ============================================================================

export const walletApi = {
  async getMyWallet() {
    return apiRequest('/wallet/me', {
      method: 'GET',
    });
  },

  async topUp(amount: number, paymentMethod: string) {
    return apiRequest('/wallet/top-up', {
      method: 'POST',
      body: JSON.stringify({
        amount,
        payment_method: paymentMethod,
      }),
    });
  },

  async getTransactions(transactionType?: string, startDate?: string, endDate?: string) {
    const params = new URLSearchParams();
    if (transactionType) params.append('transaction_type', transactionType);
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    return apiRequest(`/wallet/transactions?${params}`, {
      method: 'GET',
    });
  },

  async getBalance() {
    return apiRequest('/wallet/balance', {
      method: 'GET',
    });
  },

  async getSummary(days: number = 30) {
    return apiRequest(`/wallet/summary?days=${days}`, {
      method: 'GET',
    });
  },
};

// ============================================================================
// VOICE SETTINGS API
// ============================================================================

export const voiceSettingsApi = {
  async getMySettings() {
    return apiRequest('/voice-settings/me', {
      method: 'GET',
    });
  },

  async updateMySettings(updates: any) {
    return apiRequest('/voice-settings/me', {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  },

  async getOrgDefaults() {
    return apiRequest('/voice-settings/org-defaults', {
      method: 'GET',
    });
  },

  async setOrgDefaults(settings: any) {
    return apiRequest('/voice-settings/org-defaults', {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  },

  async deleteMySettings() {
    return apiRequest('/voice-settings/me', {
      method: 'DELETE',
    });
  },

  async getOrgStatistics() {
    return apiRequest('/voice-settings/statistics', {
      method: 'GET',
    });
  },
};

// ============================================================================
// EXERCISES API
// ============================================================================

export const exercisesApi = {
  /**
   * List available exercises with optional filters
   */
  async list(params?: {
    subject?: string;
    difficulty?: string;
    created_by?: string;
    limit?: number;
    skip?: number;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.subject) queryParams.append('subject', params.subject);
    if (params?.difficulty) queryParams.append('difficulty', params.difficulty);
    if (params?.created_by) queryParams.append('created_by', params.created_by);
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString());
    if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString());

    const url = queryParams.toString() ? `/exercises/?${queryParams}` : '/exercises/';
    return apiRequest(url, {
      method: 'GET',
    });
  },

  /**
   * Get exercise details with questions
   */
  async get(id: string) {
    return apiRequest(`/exercises/${id}`, {
      method: 'GET',
    });
  },

  /**
   * Generate exercise from study material
   */
  async generate(data: {
    material_id: string;
    num_questions: number;
    difficulty: string;
    topic?: string;
    question_types: string[];
    time_limit_minutes?: number;
  }) {
    return apiRequest('/exercises/generate', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Submit exercise answers
   */
  async submit(exerciseId: string, data: {
    answers: Array<{
      question_id: string;
      answer: string;
      time_spent_seconds?: number;
    }>;
    time_taken_seconds: number;
  }) {
    return apiRequest(`/exercises/${exerciseId}/submit`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Get detailed feedback for a submission
   */
  async getFeedback(submissionId: string) {
    return apiRequest(`/exercises/submissions/${submissionId}/feedback`, {
      method: 'GET',
    });
  },

  /**
   * Get personalized recommendations
   */
  async getRecommendations(subject: string) {
    return apiRequest(`/exercises/performance/${subject}`, {
      method: 'GET',
    });
  },

  /**
   * Get current user's submission history
   */
  async getMySubmissions(params?: { limit?: number; skip?: number }) {
    const queryParams = new URLSearchParams();
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString());
    if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString());

    const url = queryParams.toString() ? `/exercises/submissions/me?${queryParams}` : '/exercises/submissions/me';
    return apiRequest(url, {
      method: 'GET',
    });
  },
};

// ============================================================================
// VAPI TUTORING API
// ============================================================================

export const vapiTutoringApi = {
  /**
   * Create VAPI assistant for a document
   */
  async createAssistant(data: {
    material_id: string;
    voice_id?: string;
    language?: string;
  }) {
    return apiRequest('/vapi-tutoring/assistants', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Start voice tutoring session
   */
  async startSession(data: {
    material_id: string;
    phone_number: string;
  }) {
    return apiRequest('/vapi-tutoring/sessions/start', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Get available tutor voices
   */
  async getVoices() {
    return apiRequest('/vapi-tutoring/voices', {
      method: 'GET',
    });
  },

  /**
   * Check if material has assistant configured
   */
  async getMaterialAssistant(materialId: string) {
    return apiRequest(`/vapi-tutoring/materials/${materialId}/assistant`, {
      method: 'GET',
    });
  },
};

// ============================================================================
// MATERIAL VOICE CHAT API
// ============================================================================

export interface MaterialVoiceResponse {
  chat_id: string;
  transcribed_text: string;
  detected_language: string | null;
  response_text: string;
  response_audio_base64: string;
  audio_duration: number;
  confidence_score: number;
  sources: any[];
  cost_breakdown: {
    asr: number;
    llm: number;
    tts: number;
    total: number;
  };
  performance: {
    asr_time: number;
    rag_time: number;
    tts_time: number;
    total_time: number;
  };
}

export interface ChatHistoryEntry {
  id: string;
  question_text: string;
  answer_text: string;
  confidence_score: number;
  created_at: string;
  cost_breakdown?: {
    asr: number;
    llm: number;
    tts: number;
    total: number;
  };
}

export const materialVoiceApi = {
  /**
   * Send a voice question about a material
   *
   * Uses the user's voice settings for TTS/ASR if not specified.
   */
  async ask(
    materialId: string,
    audioBase64: string,
    options?: {
      asrProviderId?: string;
      ttsProviderId?: string;
      ttsVoiceId?: string;
      ttsSpeed?: number;
      ttsPitch?: number;
      language?: string;
    }
  ): Promise<MaterialVoiceResponse> {
    // Pass undefined for all optional params so backend uses Voice Settings
    return apiRequest(`/material-voice/${materialId}/ask`, {
      method: 'POST',
      body: JSON.stringify({
        audio_base64: audioBase64,
        asr_provider_id: options?.asrProviderId,
        tts_provider_id: options?.ttsProviderId,
        tts_voice_id: options?.ttsVoiceId,
        tts_speed: options?.ttsSpeed,
        tts_pitch: options?.ttsPitch,
        language: options?.language,  // Let backend use Voice Settings if undefined
      }),
    });
  },

  /**
   * Get voice chat history for a material
   */
  async getHistory(
    materialId: string,
    limit: number = 20
  ): Promise<{ material_id: string; count: number; history: ChatHistoryEntry[] }> {
    return apiRequest(`/material-voice/${materialId}/history?limit=${limit}`, {
      method: 'GET',
    });
  },

  /**
   * Clear voice chat history for a material
   */
  async clearHistory(materialId: string): Promise<{ deleted_count: number }> {
    return apiRequest(`/material-voice/${materialId}/history`, {
      method: 'DELETE',
    });
  },

  /**
   * Check if a material is ready for voice chat
   */
  async checkReady(materialId: string): Promise<{
    ready: boolean;
    material_id: string;
    title?: string;
    subject?: string;
    topics?: string[];
    reason?: string;
  }> {
    return apiRequest(`/material-voice/${materialId}/check`, {
      method: 'GET',
    });
  },
};

export default {
  auth: authApi,
  analytics: analyticsApi,
  usage: usageApi,
  materials: materialsApi,
  tutoring: tutoringApi,
  progress: progressApi,
  wallet: walletApi,
  voiceSettings: voiceSettingsApi,
  exercises: exercisesApi,
  vapiTutoring: vapiTutoringApi,
  materialVoice: materialVoiceApi,
};
