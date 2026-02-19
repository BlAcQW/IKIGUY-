/**
 * API Client
 * Axios-based client for backend API communication
 */

import axios, { AxiosError, AxiosInstance } from 'axios';
import { supabase } from './supabase';

const API_URL = import.meta.env.VITE_API_BASE_URL || 'https://inkwave-api.ailabsafrica.com/api/v1';

// Export API_BASE_URL for use in hooks
export const API_BASE_URL = API_URL;

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth token
apiClient.interceptors.request.use(
  async (config) => {
    try {
      const { data: { session }, error: sessionError } = await supabase.auth.getSession();

      if (sessionError) {
        console.error('[Auth] Failed to get session:', sessionError);
        return config;
      }

      if (session?.access_token) {
        config.headers.Authorization = `Bearer ${session.access_token}`;
        console.debug('[Auth] Request authenticated:', {
          url: config.url,
          hasToken: true,
          tokenPrefix: session.access_token.substring(0, 20) + '...',
        });
      } else {
        console.warn('[Auth] No active session found for request:', config.url);
      }
    } catch (error) {
      console.error('[Auth] Unexpected error getting session:', error);
    }
    return config;
  },
  (error) => {
    console.error('[Auth] Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor - handle errors with smart retry
let isRefreshing = false;
let failedQueue: Array<{ resolve: (value?: any) => void; reject: (reason?: any) => void }> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any;

    // Handle 401 errors intelligently
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      // Check if offline - don't try to refresh if offline
      if (!navigator.onLine) {
        console.warn('[Auth] Cannot refresh token while offline');
        return Promise.reject(new Error('Offline: Cannot refresh authentication'));
      }

      // If already refreshing, queue this request
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return apiClient(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        console.log('[Auth] 401 detected - attempting token refresh');

        // Try to refresh the session
        const { data: { session }, error: refreshError } = await supabase.auth.refreshSession();

        if (refreshError || !session) {
          console.error('[Auth] Token refresh failed:', refreshError);
          // Only sign out if refresh actually failed (not network error)
          if (refreshError && !refreshError.message?.includes('fetch')) {
            processQueue(refreshError, null);
            await supabase.auth.signOut();
            window.location.href = '/login';
          } else {
            console.warn('[Auth] Refresh failed due to network, will retry when online');
          }
          isRefreshing = false;
          return Promise.reject(refreshError);
        }

        console.log('[Auth] Token refreshed successfully');

        // Update the failed request with new token
        originalRequest.headers.Authorization = `Bearer ${session.access_token}`;

        // Process queued requests
        processQueue(null, session.access_token);
        isRefreshing = false;

        // Retry the original request
        return apiClient(originalRequest);
      } catch (refreshError) {
        console.error('[Auth] Unexpected error during token refresh:', refreshError);
        processQueue(refreshError, null);
        isRefreshing = false;
        // Don't sign out on network errors
        const isNetworkError = refreshError instanceof Error &&
          (refreshError.message?.includes('fetch') || refreshError.message?.includes('network'));
        if (!isNetworkError) {
          await supabase.auth.signOut();
          window.location.href = '/login';
        }
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// API methods
export const api = {
  // Books
  books: {
    list: (params?: { genre?: string; search?: string; page?: number; limit?: number }) =>
      apiClient.get('/books', { params }),
    getAllBooks: (params?: { page?: number; per_page?: number; search?: string }) =>
      apiClient.get('/books', { params }),
    get: (id: string) => apiClient.get(`/books/${id}`),
    search: (query: string, category?: string, page?: number, per_page?: number) =>
      apiClient.get('/books/search', {
        params: { q: query, category, page, per_page }
      }),
    continueReading: (limit?: number) =>
      apiClient.get('/books/continue-reading', { params: { limit } }),
    checkDuplicateTitle: (title: string) =>
      apiClient.get<{
        exists: boolean;
        duplicates: Array<{
          book_id: string;
          title: string;
          author: string;
          visibility: string;
          is_hidden: boolean;
          is_own_book: boolean;
          created_at: string | null;
        }>;
        similar: Array<{
          book_id: string;
          title: string;
          author: string;
          visibility: string;
          is_hidden: boolean;
          is_own_book: boolean;
          created_at: string | null;
        }>;
        total_count: number;
        message: string;
      }>('/books/check-duplicate-title', { params: { title } }),
    generateAudio: (bookId: string, params?: { provider_id?: string; voice_id?: string; speed?: number; pitch?: number; language?: string }) =>
      apiClient.post(`/books/${bookId}/generate-audio`, null, { params }),
    // Get chunk information for audio playback
    getChunksInfo: (bookId: string) =>
      apiClient.get<{
        book_id: string;
        total_chunks: number;
        chunk_durations: number[];
        total_duration: number;
        generated_count: number;
        all_generated: boolean;
        chapter_boundaries: { chunk_index: number; chapter_title: string }[];
      }>(`/books/${bookId}/chunks/info`),
    // Book voice settings
    getVoiceSettings: (bookId: string) =>
      apiClient.get(`/books/${bookId}/voice-settings`),
    updateVoiceSettings: (bookId: string, settings: any) =>
      apiClient.put(`/books/${bookId}/voice-settings`, settings),
    deleteVoiceSettings: (bookId: string) =>
      apiClient.delete(`/books/${bookId}/voice-settings`),
    // Author book management
    myBooks: (params?: { page?: number; per_page?: number; status?: string }) =>
      apiClient.get('/books/my-books', { params }),
    upload: (formData: FormData) =>
      apiClient.post('/books/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000, // 2 minutes for file upload
      }),
    update: (bookId: string, data: {
      title?: string;
      author?: string;
      description?: string;
      cover_url?: string;
      genre?: string;
    }) => {
      // Backend expects form data, not JSON
      const formData = new FormData();
      if (data.title !== undefined) formData.append('title', data.title);
      if (data.author !== undefined) formData.append('author', data.author);
      if (data.description !== undefined) formData.append('description', data.description);
      if (data.cover_url !== undefined) formData.append('cover_url', data.cover_url);
      if (data.genre !== undefined) formData.append('genre', data.genre);
      return apiClient.put(`/books/${bookId}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
    delete: (bookId: string) => apiClient.delete(`/books/${bookId}`),
    getProcessingStatus: (bookId: string) =>
      apiClient.get(`/books/${bookId}/processing-status`),
    // Admin-only: Reprocess a book (cleans up existing data and re-runs processing)
    reprocess: (bookId: string) =>
      apiClient.post(`/books/${bookId}/reprocess`),
    // Admin-only: Preview what will be deleted when deleting a book
    getDeletionPreview: (bookId: string) =>
      apiClient.get<{
        book_id: string;
        book_title: string;
        will_delete: {
          book_record: number;
          chunks: number;
          embeddings: number;
          reading_sessions: number;
          interactions: number;
          voice_settings: number;
          audio_cache_files: number;
          storage_files: string[];
        };
        warning: string;
      }>(`/books/${bookId}/deletion-preview`),
    // Book visibility management (author control)
    updateVisibility: (bookId: string, visibility: 'draft' | 'unlisted' | 'private' | 'public') =>
      apiClient.patch(`/books/${bookId}/visibility`, null, {
        params: { visibility }
      }),
    // Add public book to user library
    addToLibrary: (bookId: string) =>
      apiClient.post(`/books/${bookId}/add-to-library`),
  },

  // Reading
  reading: {
    startSession: (bookId: string) => apiClient.post('/reading/sessions', { book_id: bookId }),
    getSession: (sessionId: string) => apiClient.get(`/reading/sessions/${sessionId}`),
    getUserSessions: (activeOnly?: boolean) =>
      apiClient.get('/reading/sessions', { params: { active_only: activeOnly } }),
    updateProgress: (sessionId: string, chunkIndex: number, positionSeconds: number, totalTimeMinutes?: number) =>
      apiClient.put(`/reading/sessions/${sessionId}`, {
        current_chunk_index: chunkIndex,
        current_position_seconds: positionSeconds,
        total_time_spent_minutes: totalTimeMinutes ?? 0
      }),
    // Bookmark operations
    addBookmark: (sessionId: string, data: {
      chunk_index: number;
      position_seconds: number;
      note?: string;
      chapter_title?: string;
    }) => apiClient.post(`/reading/sessions/${sessionId}/bookmark`, data),
    updateBookmark: (sessionId: string, bookmarkId: string, note?: string) =>
      apiClient.put(`/reading/sessions/${sessionId}/bookmark/${bookmarkId}`, { note }),
    deleteBookmark: (sessionId: string, bookmarkId: string) =>
      apiClient.delete(`/reading/sessions/${sessionId}/bookmark/${bookmarkId}`),
    getBookmarks: (sessionId: string) =>
      apiClient.get(`/reading/sessions/${sessionId}/bookmarks`),
    // Session voice settings (per-interaction overrides)
    getSessionVoiceSettings: (sessionId: string) =>
      apiClient.get(`/reading/sessions/${sessionId}/voice-settings`),
    updateSessionVoiceSettings: (sessionId: string, updates: {
      tts_provider?: string;
      tts_voice?: string;
      tts_speed?: number;
      tts_pitch?: number;
      asr_provider?: string;
      asr_language?: string;
      asr_task?: string;
      llm_model?: string;
      llm_temperature?: number;
      llm_max_tokens?: number;
    }) => apiClient.put(`/reading/sessions/${sessionId}/voice-settings`, updates),
    clearSessionVoiceSettings: (sessionId: string) =>
      apiClient.delete(`/reading/sessions/${sessionId}/voice-settings`),
    getChunk: (bookId: string, chunkIndex: number) => 
      apiClient.get(`/reading/chunks/${bookId}/${chunkIndex}`),
    // Legacy endpoint (kept for backwards compatibility)
    getChunkAudio: (chunkId: string) => apiClient.get(`/reading/chunks/${chunkId}/audio`),
  },

  // Audiobook (chunk-based TTS playback)
  audiobook: {
    // Get audio for a specific chunk (generates on-demand if not cached)
    getChunkAudio: (bookId: string, chunkIndex: number, params?: {
      provider_id?: string;
      voice_id?: string;
      speed?: number;
      language?: string;
    }) => apiClient.get(`/audiobook/books/${bookId}/chunks/${chunkIndex}/audio`, {
      params,
      timeout: 120000, // 2 minutes for TTS generation
    }),

    // Pre-generate audio for multiple chunks
    generateChunks: (bookId: string, params: {
      provider_id?: string;
      voice_id?: string;
      speed?: number;
      language?: string;
      start_chunk?: number;
      end_chunk?: number;
    }) => apiClient.post(`/audiobook/books/${bookId}/generate`, params, {
      timeout: 180000, // 3 minutes for batch generation
    }),

    // Get audio generation status for a book
    getBookAudioStatus: (bookId: string) =>
      apiClient.get(`/audiobook/books/${bookId}/status`),

    // Preload audio for upcoming chunks (for seamless playback)
    preload: (bookId: string, params: {
      start_chunk: number;
      num_chunks?: number;
      provider_id?: string;
      voice_id?: string;
      speed?: number;
    }) => apiClient.post(`/audiobook/books/${bookId}/preload`, params, {
      timeout: 120000, // 2 minutes for preloading multiple chunks
    }),

    // Get available TTS providers
    getProviders: () => apiClient.get('/audiobook/providers'),

    // Stream audio from a specific position (returns next few chunks)
    streamFromPosition: (bookId: string, chunkIndex: number, params?: {
      provider_id?: string;
      speed?: number;
      num_chunks?: number;
    }) => apiClient.get(`/audiobook/books/${bookId}/stream`, {
      params: { chunk_index: chunkIndex, ...params }
    }),
  },

  // Voice Q&A
  voice: {
    transcribe: (audioBlob: Blob) => {
      const formData = new FormData();
      formData.append('audio', audioBlob);
      return apiClient.post('/voice/transcribe', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
    ask: (bookId: string, question: string, currentChunk: number) =>
      apiClient.post('/voice/ask', {
        book_id: bookId,
        question,
        current_chunk: currentChunk
      }),
    synthesize: (text: string, voice?: string) =>
      apiClient.post('/voice/synthesize', { text, voice }, { responseType: 'blob' }),
    providers: () => apiClient.get('/voice/providers'),
  },

  // Interactions
  interactions: {
    create: (sessionId: string, bookId: string) =>
      apiClient.post('/interactions', { session_id: sessionId, book_id: bookId }),
    sendMessage: (interactionId: string, message: string) =>
      apiClient.post(`/interactions/${interactionId}/messages`, { message }),
    get: (interactionId: string) => apiClient.get(`/interactions/${interactionId}`),
  },

  // Wallet
  wallet: {
    get: () => apiClient.get('/wallet/balance'),
    // New payment initiation endpoints
    initiatePaystackTopup: (amount: number, callbackUrl?: string) =>
      apiClient.post('/wallet/topup/paystack/initiate', { amount, callback_url: callbackUrl }),
    initiateStripeTopup: (amount: number, successUrl: string, cancelUrl: string) =>
      apiClient.post('/wallet/topup/stripe/initiate', { amount, success_url: successUrl, cancel_url: cancelUrl }),
    initiateExpressPayTopup: (amount: number, redirectUrl?: string) =>
      apiClient.post('/wallet/topup/expresspay/initiate', { amount, redirect_url: redirectUrl }),
    verifyPaystackPayment: (reference: string) =>
      apiClient.get(`/wallet/topup/paystack/verify/${reference}`),
    verifyExpressPayPayment: (token: string) =>
      apiClient.get(`/wallet/topup/expresspay/verify/${token}`),
    // Get payment status for polling
    getPaymentStatus: (reference: string) =>
      apiClient.get<{
        reference: string;
        status: 'pending' | 'completed' | 'failed';
        amount: number;
        currency: string;
        created_at: string | null;
        verified_at: string | null;
        error: string | null;
      }>(`/wallet/payment/status/${reference}`),
    // Get payment callback details (for ExpressPay)
    getPaymentCallback: (orderId: string, token: string) =>
      apiClient.get('/payments/callback', { params: { 'order-id': orderId, token } }),
    // Get transaction details
    getTransaction: (orderId: string) =>
      apiClient.get(`/payments/transaction/${orderId}`),
    // Legacy endpoints (kept for backwards compatibility)
    topupStripe: (amount: number) =>
      apiClient.post('/wallet/topup', {
        amount,
        payment_gateway: 'stripe',
        payment_reference: `stripe_${Date.now()}`
      }),
    topupPaystack: (amount: number, email: string) =>
      apiClient.post('/wallet/topup', {
        amount,
        payment_gateway: 'paystack',
        payment_reference: `paystack_${Date.now()}`
      }),
    transactions: (limit?: number) =>
      apiClient.get('/wallet/transactions', { params: { limit } }),
  },

  // Profile
  profile: {
    get: () => apiClient.get('/profile'),
    update: (data: {
      display_name?: string;
      avatar_url?: string;
      first_name?: string;
      last_name?: string;
      phone_number?: string;
      date_of_birth?: string;
      preferred_voice?: string;
      playback_speed?: number;
      reading_level?: string;
      voice_preferences?: any;
      interaction_preferences?: any;
    }) => apiClient.put('/profile', data),
    uploadAvatar: (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      return apiClient.post('/profile/avatar/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
    updateAvatarUrl: (avatarUrl: string) =>
      apiClient.put('/profile/avatar/url', { avatar_url: avatarUrl }),
    updateVoicePreferences: (preferences: {
      provider_id?: string;
      voice_id?: string;
      speed?: number;
      language?: string;
      voice_clone_reference?: string;
    }) => apiClient.put('/profile/voice-preferences', preferences),
    updateInteractionPreferences: (preferences: {
      explanation_depth?: string;
      discussion_topics?: string[];
    }) => apiClient.put('/profile/interaction-preferences', preferences),
    updateReadingLevel: (level: string) =>
      apiClient.put(`/profile/reading-level?reading_level=${level}`),
    getStats: () => apiClient.get('/profile/stats'),
  },

  // Auth
  auth: {
    signup: (email: string, password: string, invitationToken?: string) =>
      apiClient.post('/auth/signup', {
        email,
        password,
        invitation_token: invitationToken || undefined,
      }),
    login: (email: string, password: string) => apiClient.post('/auth/login', { email, password }),
    me: () => apiClient.get('/auth/me'),
  },

  // Organizations
  organizations: {
    list: () => apiClient.get('/organizations'),
    get: (id: string) => apiClient.get(`/organizations/${id}`),
    create: (data: any) => apiClient.post('/organizations', data),
    update: (id: string, data: any) => apiClient.put(`/organizations/${id}`, data),
    delete: (id: string) => apiClient.delete(`/organizations/${id}`),

    // Users (renamed from Members to match backend endpoint)
    listMembers: (orgId: string) => apiClient.get(`/organizations/${orgId}/users`),
    addMember: (orgId: string, data: any) => apiClient.post(`/organizations/${orgId}/users`, data),
    updateMemberRole: (orgId: string, userId: string, role: string) =>
      apiClient.put(`/organizations/${orgId}/users/${userId}`, { role }),
    removeMember: (orgId: string, userId: string) =>
      apiClient.delete(`/organizations/${orgId}/users/${userId}`),

    // Invitations
    listInvitations: (orgId: string) => apiClient.get(`/organizations/${orgId}/invitations`),
    inviteMember: (orgId: string, data: any) =>
      apiClient.post(`/organizations/${orgId}/invitations`, data),
    cancelInvitation: (orgId: string, invitationId: string) =>
      apiClient.delete(`/organizations/${orgId}/invitations/${invitationId}`),
  },

  // Admin
  admin: {
    // Provider Management
    listProviders: (providerType?: string) =>
      apiClient.get('/admin/providers', { params: { provider_type: providerType } }),
    updateProvider: (config: any) =>
      apiClient.post('/admin/providers', config),
    getProviderComparison: () =>
      apiClient.get('/admin/providers/comparison'),

    // Book Management
    uploadBook: (formData: FormData) =>
      apiClient.post('/admin/books/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000, // 2 minutes for file upload
      }),
    getBookProcessingStatus: (bookId: string) =>
      apiClient.get(`/admin/books/${bookId}/status`),

    // Analytics
    getAnalytics: (period: string = 'month') =>
      apiClient.get('/admin/analytics', { params: { period } }),
    getUserAnalytics: (limit: number = 50, sortBy: string = 'usage') =>
      apiClient.get('/admin/analytics/users', { params: { limit, sort_by: sortBy } }),
    getUserStats: () =>
      apiClient.get('/admin/analytics/user-stats'),
    getUserActivity: () =>
      apiClient.get('/admin/analytics/user-activity'),
    getUserBookProgress: (userId?: string, limit?: number) =>
      apiClient.get('/admin/analytics/user-book-progress', { params: { user_id: userId, limit } }),
    getCurrentlyLoggedIn: () =>
      apiClient.get('/admin/analytics/currently-logged-in'),
    getCurrentlyListening: () =>
      apiClient.get('/admin/analytics/currently-listening'),

    // Book Moderation
    hideBook: (bookId: string, reason: string) =>
      apiClient.post(`/admin/books/${bookId}/hide`, null, {
        params: { reason }
      }),
    unhideBook: (bookId: string, reason?: string) =>
      apiClient.post(`/admin/books/${bookId}/unhide`, null, {
        params: reason ? { reason } : undefined
      }),
    listHiddenBooks: (params?: { page?: number; per_page?: number }) =>
      apiClient.get('/admin/books/hidden', { params }),
    getAuditLog: (params?: {
      book_id?: string;
      admin_id?: string;
      action?: string;
      limit?: number;
    }) => apiClient.get('/admin/audit-log', { params }),
    permanentlyDeleteBook: (bookId: string, reason: string, confirm: boolean) =>
      apiClient.delete(`/admin/books/${bookId}/permanent`, {
        params: { reason, confirm }
      }),
  },

  // Voice Settings
  voiceSettings: {
    getMySettings: () => apiClient.get('/voice-settings/my-settings'),
    updateMySettings: (updates: any) => apiClient.put('/voice-settings/my-settings', updates),
    getOrgDefaults: () => apiClient.get('/voice-settings/org-defaults'),
    setOrgDefaults: (settings: any) => apiClient.put('/voice-settings/org-defaults', settings),
    deleteMySettings: () => apiClient.delete('/voice-settings/my-settings'),
    getOrgStatistics: () => apiClient.get('/voice-settings/org-statistics'),
  },

  // Recommendations
  recommendations: {
    getPersonalized: (limit?: number, excludeCompleted?: boolean) =>
      apiClient.get('/recommendations', { params: { limit, exclude_completed: excludeCompleted } }),
    getCategories: () => apiClient.get('/recommendations/categories'),
    getByCategory: (category: string, limit?: number) =>
      apiClient.get(`/recommendations/category/${category}`, { params: { limit } }),
    getLatest: (limit?: number) =>
      apiClient.get('/recommendations/latest', { params: { limit } }),
    getSeries: (limit?: number) =>
      apiClient.get('/recommendations/series', { params: { limit } }),
    getSeriesDetailed: (limit?: number) =>
      apiClient.get('/recommendations/series/detailed', { params: { limit } }),
    getSimilar: (bookId: string, limit?: number) =>
      apiClient.get(`/recommendations/similar/${bookId}`, { params: { limit } }),
    getFeatured: () => apiClient.get('/recommendations/featured'),
    getForYou: () => apiClient.get('/recommendations/for-you'),
  },

  // Author Images (dynamic web search for author photos)
  authorImages: {
    // Search for author images by name
    search: (authorName: string, context?: string, maxResults?: number) =>
      apiClient.get('/author-images/search', {
        params: {
          author_name: authorName,
          context,
          max_results: maxResults
        }
      }),
    // Search via POST (for complex queries)
    searchPost: (authorName: string, context?: string, maxResults?: number) =>
      apiClient.post('/author-images/search', {
        author_name: authorName,
        context,
        max_results: maxResults || 5
      }),
    // Look up and save author image for existing book
    lookupForBook: (bookId: string) =>
      apiClient.post(`/author-images/lookup-for-book/${bookId}`),
    // Bulk update author images for books without photos
    bulkUpdate: (limit?: number) =>
      apiClient.post('/author-images/bulk-update', null, { params: { limit } }),
  },

  // Reference Audio (for zero-shot TTS providers)
  referenceAudio: {
    upload: (formData: FormData) =>
      apiClient.post('/reference-audio/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 60000, // 1 minute for audio upload
      }),
    list: () => apiClient.get('/reference-audio/'),
    get: (id: string) => apiClient.get(`/reference-audio/${id}`),
    getAudio: (id: string) => apiClient.get(`/reference-audio/${id}/audio`, { responseType: 'blob' }),
    delete: (id: string) => apiClient.delete(`/reference-audio/${id}`),
  },

  // Book Invitations (admin feature to share book access via URL)
  bookInvitations: {
    // Admin: Create a new invitation link
    create: (data: {
      book_id: string;
      max_uses?: number;
      expires_in_days?: number;
      welcome_message?: string;
    }) => apiClient.post('/book-invitations', data),

    // Admin: List all invitations
    list: (params?: {
      book_id?: string;
      include_inactive?: boolean;
      page?: number;
      per_page?: number;
    }) => apiClient.get('/book-invitations', { params }),

    // Admin: Revoke an invitation
    revoke: (invitationId: string) =>
      apiClient.delete(`/book-invitations/${invitationId}`),

    // Admin: Get invitation statistics
    getStats: () => apiClient.get('/book-invitations/stats'),

    // Public: Get invitation details (for signup page)
    getPublicInfo: (invitationId: string) =>
      apiClient.get(`/book-invitations/public/${invitationId}`),

    // Authenticated: Redeem an invitation
    redeem: (invitationId: string) =>
      apiClient.post(`/book-invitations/${invitationId}/redeem`),

    // Authenticated: Get user's library
    getMyLibrary: () => apiClient.get('/book-invitations/my-library'),
  },

  // Bookmarked books (save books for later)
  bookmarks: {
    // List all bookmarked books
    list: () => apiClient.get('/bookmarks'),
    // Add a book to bookmarks
    add: (bookId: string) => apiClient.post(`/bookmarks/${bookId}`),
    // Remove a book from bookmarks
    remove: (bookId: string) => apiClient.delete(`/bookmarks/${bookId}`),
    // Check if a book is bookmarked
    getStatus: (bookId: string) => apiClient.get(`/bookmarks/${bookId}/status`),
  },

  // Short URLs (URL shortening for social sharing)
  shortUrls: {
    // Create a short URL for sharing
    create: (targetUrl: string, customCode?: string) =>
      apiClient.post('/short-urls/create', {
        target_url: targetUrl,
        custom_code: customCode,
      }),
    // Get stats for a short URL
    getStats: (shortCode: string) =>
      apiClient.get(`/short-urls/${shortCode}/stats`),
  },

  // Comments (book reviews and ratings)
  comments: {
    // Get comments for a book
    list: (bookId: string, params?: {
      sort_by?: 'recent' | 'helpful' | 'rating';
      limit?: number;
      offset?: number;
    }) => apiClient.get(`/comments/books/${bookId}`, { params }),

    // Create a new comment
    create: (bookId: string, data: {
      rating?: number;
      title?: string;
      comment_text: string;
    }) => apiClient.post(`/comments/books/${bookId}`, data),

    // Update own comment
    update: (commentId: string, data: {
      rating?: number;
      title?: string;
      comment_text?: string;
    }) => apiClient.put(`/comments/${commentId}`, data),

    // Delete own comment
    delete: (commentId: string) => apiClient.delete(`/comments/${commentId}`),

    // Toggle helpful vote
    toggleHelpful: (commentId: string) =>
      apiClient.post(`/comments/${commentId}/helpful`),
  },

  // Social (follow/unfollow, followers/following, blocking, reporting)
  social: {
    // Follow a user
    followUser: (userId: string) =>
      apiClient.post(`/social/follow/${userId}`),

    // Unfollow a user
    unfollowUser: (userId: string) =>
      apiClient.delete(`/social/follow/${userId}`),

    // Get user's followers list
    getFollowers: (userId: string, page?: number, per_page?: number) =>
      apiClient.get(`/social/followers/${userId}`, { params: { page, per_page } }),

    // Get user's following list
    getFollowing: (userId: string, page?: number, per_page?: number) =>
      apiClient.get(`/social/following/${userId}`, { params: { page, per_page } }),

    // Get follow suggestions
    getFollowSuggestions: (limit?: number) =>
      apiClient.get('/social/suggestions', { params: { limit } }),

    // Get activity feed from followed users
    getFollowingFeed: (limit?: number) =>
      apiClient.get('/social/feed', { params: { limit } }),

    // Block a user
    blockUser: (userId: string, reason?: string) =>
      apiClient.post(`/social/block/${userId}`, { reason }),

    // Unblock a user
    unblockUser: (userId: string) =>
      apiClient.delete(`/social/unblock/${userId}`),

    // Report a user
    reportUser: (userId: string, report: {
      report_type: string;
      description: string;
      evidence_urls?: string[];
    }) => apiClient.post(`/social/report/${userId}`, report),
  },

  // Leaderboard (top listeners rankings)
  leaderboard: {
    // Get top listeners for a period (with optional search)
    getTopListeners: (period?: 'week' | 'month' | 'all_time', limit?: number, search?: string) =>
      apiClient.get('/leaderboard', { params: { period, limit, search } }),

    // Get current user's rank
    getUserRank: (period?: 'week' | 'month' | 'all_time') =>
      apiClient.get('/leaderboard/rank', { params: { period } }),

    // Get current user's own listening history by book
    getMyHistory: () =>
      apiClient.get('/leaderboard/my-history'),

    // Get user's listening history by book (admin only)
    getUserHistory: (userId: string) =>
      apiClient.get(`/leaderboard/user/${userId}/history`),
  },

  // Users (public profiles, discovery, search)
  users: {
    // Get public profile for a user
    getPublicProfile: (userId: string) =>
      apiClient.get(`/users/${userId}/profile`),

    // Get books user is currently reading
    getCurrentlyReading: (userId: string) =>
      apiClient.get(`/users/${userId}/currently-reading`),

    // Get user's reading activity
    getUserActivity: (userId: string, limit?: number) =>
      apiClient.get(`/users/${userId}/activity`, { params: { limit } }),

    // Search users by username or display name
    searchUsers: (query: string, page?: number, per_page?: number) =>
      apiClient.get('/users/search', { params: { query, page, per_page } }),

    // Check username availability
    checkUsername: (username: string) =>
      apiClient.get('/users/username/check', { params: { username } }),

    // Update username (30-day cooldown)
    updateUsername: (username: string) =>
      apiClient.put('/users/username', { username }),
  },

  // Tracking & Analytics
  tracking: {
    // Log an error
    logError: (data: {
      error_type: string;
      error_message: string;
      stack_trace?: string;
      context?: any;
      user_agent?: string;
      browser?: string;
      device_type?: string;
    }) => apiClient.post('/tracking/errors', data),

    // Track an event
    trackEvent: (data: {
      event_type: string;
      event_name: string;
      properties?: any;
      page_url?: string;
      referrer?: string;
    }) => apiClient.post('/tracking/events', data),

    // Log usage/cost
    logUsage: (data: {
      service: string;
      action: string;
      cost_credits: number;
      metadata?: any;
    }) => apiClient.post('/tracking/usage', data),

    // Log playback metrics
    logPlaybackMetrics: (data: {
      session_id: string;
      book_id: string;
      chunk_index: number;
      buffer_start_ms: number;
      buffer_end_ms?: number;
      buffer_duration_ms?: number;
      stall_count?: number;
      total_stall_duration_ms?: number;
      audio_format?: string;
      audio_bitrate?: number;
      audio_size_bytes?: number;
      download_time_ms?: number;
      cache_hit?: boolean;
    }) => apiClient.post('/tracking/playback-metrics', data),

    // Get recent errors (admin)
    getRecentErrors: (limit?: number, errorType?: string) =>
      apiClient.get('/tracking/errors/recent', { params: { limit, error_type: errorType } }),

    // Get error stats (admin)
    getErrorStats: () =>
      apiClient.get('/tracking/errors/stats'),
  },

  // Consumption Tracking (unified activity tracking)
  consumption: {
    // Record a consumption event
    recordEvent: (data: {
      book_id: string;
      session_id: string;
      event_type: 'book_opened' | 'reading_started' | 'listening_started' | 'progress_update' | 'paused' | 'resumed' | 'completed';
      consumption_mode: 'manual_reading' | 'audio_playback' | 'ai_voice_narration';
      chunk_index?: number;
      total_chunks?: number;
      progress_percentage?: number;
      position_seconds?: number;
      duration_seconds?: number;
      cumulative_time_seconds?: number;
      book_title?: string;
      book_author?: string;
      context?: Record<string, any>;
      device_type?: string;
      browser?: string;
      user_agent?: string;
    }) => apiClient.post('/consumption/events', data),

    // Record timer-based progress update
    updateProgress: (data: {
      session_id: string;
      book_id: string;
      consumption_mode: 'manual_reading' | 'audio_playback' | 'ai_voice_narration';
      chunk_index: number;
      position_seconds: number;
      duration_since_last_update: number;
      cumulative_time_seconds: number;
      total_chunks: number;
      is_final_chunk?: boolean;
      chunk_completed?: boolean;
    }) => apiClient.post('/consumption/progress', data),

    // Record book completion
    recordCompletion: (data: {
      session_id: string;
      book_id: string;
      consumption_mode: 'manual_reading' | 'audio_playback' | 'ai_voice_narration';
      total_chunks: number;
      final_chunk_index: number;
      total_time_seconds: number;
      all_chunks_consumed?: boolean;
      chunk_indices_consumed?: number[];
    }) => apiClient.post('/consumption/complete', data),

    // Get session latest progress (for page refresh recovery)
    getSessionProgress: (sessionId: string) =>
      apiClient.get(`/consumption/sessions/${sessionId}/latest`),

    // Get my stats
    getMyStats: (periodDays?: number) =>
      apiClient.get('/consumption/me/stats', { params: { period_days: periodDays } }),

    // Get my sessions
    getMySessions: (bookId?: string, limit?: number, offset?: number) =>
      apiClient.get('/consumption/me/sessions', { params: { book_id: bookId, limit, offset } }),

    // Get my recent activity
    getMyRecentActivity: (limit?: number) =>
      apiClient.get('/consumption/me/recent', { params: { limit } }),

    // Admin endpoints
    admin: {
      getDashboard: (periodDays?: number) =>
        apiClient.get('/consumption/admin/dashboard', { params: { period_days: periodDays } }),
      getUserStats: (userId: string, periodDays?: number) =>
        apiClient.get(`/consumption/admin/users/${userId}/stats`, { params: { period_days: periodDays } }),
      getBookStats: (bookId: string, periodDays?: number) =>
        apiClient.get(`/consumption/admin/books/${bookId}/stats`, { params: { period_days: periodDays } }),
      getAllRecentActivity: (limit?: number) =>
        apiClient.get('/consumption/admin/recent', { params: { limit } }),
    },
  },
};

export default apiClient;
