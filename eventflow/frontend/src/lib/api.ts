// EventFlow API Service Layer
// Centralized API communication for the EventFlow application

import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  Event,
  EventFormData,
  Task,
  TaskFormData,
  ResponsiblePerson,
  DashboardData,
  Recommendation,
  VoiceCall,
  Notification,
  Wallet,
  Transaction,
  TopUpRequest,
  TopUpResponse,
  UsageStats,
  PaginatedResponse,
  ApiResponse,
  TaskFilters,
  EventFilters,
} from '../types';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://eventflow-api.ailabsafrica.com/api/v1';

// Export API_BASE_URL for use in hooks
export { API_BASE_URL };

// Create axios instance with default config
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Request interceptor (no auth required for public demo)
apiClient.interceptors.request.use(
  (config) => {
    // No authentication needed in public demo mode
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiResponse>) => {
    // Suppress 403 errors for wallet endpoints (expected for unauthenticated users)
    const is403WalletError = error.response?.status === 403 &&
                             error.config?.url?.includes('/wallet');

    if (!is403WalletError) {
      // Log other errors but don't redirect (public demo mode)
      console.error('API Error:', error.response?.data || error.message);
    }
    return Promise.reject(error);
  }
);

// Helper function to handle API responses
const handleResponse = <T>(promise: Promise<any>): Promise<T> => {
  return promise
    .then((res) => {
      // If response has pagination structure (data, total, page), return whole object
      if (res.data && typeof res.data === 'object' && 'data' in res.data && 'total' in res.data) {
        return res.data;
      }
      // Otherwise, try to extract nested data or return as-is
      return res.data.data || res.data;
    })
    .catch((error: AxiosError<ApiResponse>) => {
      const message = error.response?.data?.error?.message || error.message;
      throw new Error(message);
    });
};

// ====================
// Authentication
// ====================
export const authApi = {
  login: (phone: string) =>
    handleResponse<{ otp_sent: boolean }>(
      apiClient.post('/auth/login', { phone })
    ),

  verifyOtp: (phone: string, otp: string) =>
    handleResponse<{ token: string; user: any }>(
      apiClient.post('/auth/verify-otp', { phone, otp })
    ),

  getProfile: () =>
    handleResponse<any>(apiClient.get('/auth/profile')),

  updateProfile: (data: Partial<any>) =>
    handleResponse<any>(apiClient.patch('/auth/profile', data)),

  logout: () =>
    handleResponse<{ success: boolean }>(apiClient.post('/auth/logout')),
};

// ====================
// Events API
// ====================
export const eventsApi = {
  getAll: (filters?: EventFilters) =>
    handleResponse<PaginatedResponse<Event>>(
      apiClient.get('/events', { params: filters })
    ),

  getById: (id: string) =>
    handleResponse<Event>(apiClient.get(`/events/${id}`)),

  create: (data: EventFormData) =>
    handleResponse<Event>(apiClient.post('/events', data)),

  update: (id: string, data: Partial<EventFormData>) =>
    handleResponse<Event>(apiClient.patch(`/events/${id}`, data)),

  delete: (id: string) =>
    handleResponse<{ success: boolean }>(apiClient.delete(`/events/${id}`)),

  getDashboard: (id: string) =>
    handleResponse<DashboardData>(apiClient.get(`/events/${id}/dashboard`)),

  generateTasks: (id: string) =>
    handleResponse<Task[]>(apiClient.post(`/events/${id}/generate-tasks`)),

  uploadDocument: (id: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return handleResponse<{ url: string }>(
      apiClient.post(`/events/${id}/documents`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    );
  },
};

// ====================
// Tasks API
// ====================
export const tasksApi = {
  getAll: (eventId?: string, filters?: TaskFilters) =>
    handleResponse<PaginatedResponse<Task>>(
      apiClient.get('/tasks', { params: { event_id: eventId, ...filters } })
    ),

  getById: (id: string) =>
    handleResponse<Task>(apiClient.get(`/tasks/${id}`)),

  create: (eventId: string, data: TaskFormData) =>
    handleResponse<Task>(
      apiClient.post('/tasks', { ...data, event_id: eventId })
    ),

  update: (id: string, data: Partial<TaskFormData>) =>
    handleResponse<Task>(apiClient.patch(`/tasks/${id}`, data)),

  updateStatus: (id: string, status: string, notes?: string) =>
    handleResponse<Task>(
      apiClient.patch(`/tasks/${id}/status`, { status, notes })
    ),

  delete: (id: string) =>
    handleResponse<{ success: boolean }>(apiClient.delete(`/tasks/${id}`)),

  getUpdates: (id: string) =>
    handleResponse<any[]>(apiClient.get(`/tasks/${id}/updates`)),

  addUpdate: (id: string, update_text: string) =>
    handleResponse<any>(
      apiClient.post(`/tasks/${id}/updates`, { update_text })
    ),
};

// ====================
// Responsible Persons API
// ====================
export const responsiblePersonsApi = {
  getAll: (eventId: string) =>
    handleResponse<ResponsiblePerson[]>(
      apiClient.get(`/events/${eventId}/persons`)
    ),

  getById: (id: string) =>
    handleResponse<ResponsiblePerson>(apiClient.get(`/persons/${id}`)),

  create: (eventId: string, data: Omit<ResponsiblePerson, 'id' | 'event_id' | 'created_at'>) =>
    handleResponse<ResponsiblePerson>(
      apiClient.post(`/events/${eventId}/persons`, data)
    ),

  update: (id: string, data: Partial<ResponsiblePerson>) =>
    handleResponse<ResponsiblePerson>(apiClient.patch(`/persons/${id}`, data)),

  delete: (id: string) =>
    handleResponse<{ success: boolean }>(apiClient.delete(`/persons/${id}`)),
};

// ====================
// AI Recommendations API
// ====================
export const recommendationsApi = {
  getForEvent: (eventId: string) =>
    handleResponse<Recommendation[]>(
      apiClient.get(`/events/${eventId}/recommendations`)
    ),

  dismiss: (id: string) =>
    handleResponse<{ success: boolean }>(
      apiClient.post(`/recommendations/${id}/dismiss`)
    ),

  accept: (id: string) =>
    handleResponse<{ success: boolean }>(
      apiClient.post(`/recommendations/${id}/accept`)
    ),
};

// ====================
// Voice Calls API
// ====================
export const callsApi = {
  initiate: (taskId: string, personId: string) =>
    handleResponse<VoiceCall>(
      apiClient.post('/calls/initiate', { task_id: taskId, person_id: personId })
    ),

  getHistory: (taskId?: string) =>
    handleResponse<VoiceCall[]>(
      apiClient.get('/calls', { params: { task_id: taskId } })
    ),

  getById: (id: string) =>
    handleResponse<VoiceCall>(apiClient.get(`/calls/${id}`)),

  scheduleCallback: (taskId: string, personId: string, datetime: string) =>
    handleResponse<{ success: boolean }>(
      apiClient.post('/calls/schedule', {
        task_id: taskId,
        person_id: personId,
        datetime,
      })
    ),
};

// ====================
// Notifications API
// ====================
export const notificationsApi = {
  sendReminder: (taskId: string, channel: string) =>
    handleResponse<Notification>(
      apiClient.post('/notifications/reminder', { task_id: taskId, channel })
    ),

  getHistory: (eventId?: string) =>
    handleResponse<Notification[]>(
      apiClient.get('/notifications', { params: { event_id: eventId } })
    ),

  escalate: (taskId: string) =>
    handleResponse<{ success: boolean }>(
      apiClient.post(`/tasks/${taskId}/escalate`)
    ),
};

// ====================
// Wallet API
// ====================
export const walletApi = {
  getBalance: () =>
    handleResponse<Wallet>(apiClient.get('/wallet/balance')),

  getTransactions: (page = 1, per_page = 20) =>
    handleResponse<PaginatedResponse<Transaction>>(
      apiClient.get('/wallet/transactions', { params: { page, per_page } })
    ),

  topUp: (data: TopUpRequest) =>
    handleResponse<TopUpResponse>(apiClient.post('/wallet/topup', data)),

  verifyPayment: (reference: string) =>
    handleResponse<Transaction>(
      apiClient.get(`/wallet/verify/${reference}`)
    ),

  getUsageStats: (period: 'day' | 'week' | 'month' = 'week') =>
    handleResponse<UsageStats>(
      apiClient.get('/wallet/usage', { params: { period } })
    ),
};

// ====================
// Health Check
// ====================
export const healthApi = {
  check: () =>
    handleResponse<{ status: string; service: string }>(
      apiClient.get('/health')
    ),
};

// ====================
// Voice Settings
// ====================
export const voiceSettingsApi = {
  getMySettings: () =>
    handleResponse<any>(
      apiClient.get('/voice-settings/me')
    ),

  updateMySettings: (updates: any) =>
    handleResponse<any>(
      apiClient.put('/voice-settings/me', updates)
    ),

  deleteMySettings: () =>
    handleResponse<void>(
      apiClient.delete('/voice-settings/me')
    ),

  getOrgDefaults: () =>
    handleResponse<any>(
      apiClient.get('/voice-settings/org-defaults')
    ),

  setOrgDefaults: (settings: any) =>
    handleResponse<any>(
      apiClient.put('/voice-settings/org-defaults', settings)
    ),

  getOrgStatistics: () =>
    handleResponse<any>(
      apiClient.get('/voice-settings/statistics')
    ),
};

// Export default API object
const api = {
  auth: authApi,
  events: eventsApi,
  tasks: tasksApi,
  persons: responsiblePersonsApi,
  recommendations: recommendationsApi,
  calls: callsApi,
  notifications: notificationsApi,
  wallet: walletApi,
  health: healthApi,
  voiceSettings: voiceSettingsApi,
};

export default api;
