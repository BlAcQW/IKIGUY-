import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';

// API Configuration
// Using API_BASE_URL from api-config;

export const API_ENDPOINTS = {
  // System Health
  systemHealth: `${API_BASE_URL}/api/system/health`,
  systemCleanup: `${API_BASE_URL}/api/system/cleanup`,
  systemGpu: `${API_BASE_URL}/api/system/gpu`,
  systemOverview: `${API_BASE_URL}/api/system/overview`,
  processKill: `${API_BASE_URL}/api/system/process/kill`,

  // Service Management
  servicesList: `${API_BASE_URL}/api/services/list`,
  servicesScan: `${API_BASE_URL}/api/services/scan`,
  servicesTemplates: `${API_BASE_URL}/api/services/templates`,
  servicesAction: (serviceName: string) => `${API_BASE_URL}/api/services/${serviceName}/action`,
  servicesStatus: (serviceName: string) => `${API_BASE_URL}/api/services/${serviceName}/status`,
  servicesFile: (serviceName: string) => `${API_BASE_URL}/api/services/${serviceName}/file`,
  servicesLogs: (serviceName: string) => `${API_BASE_URL}/api/services/${serviceName}/logs`,
  servicesCreate: `${API_BASE_URL}/api/services/create`,
  servicesDelete: (serviceName: string) => `${API_BASE_URL}/api/services/${serviceName}`,
  servicesDaemonReload: `${API_BASE_URL}/api/services/daemon-reload`,
  
  // Admin
  adminUsers: `${API_BASE_URL}/api/admin/users`,
  adminUser: (userId: string) => `${API_BASE_URL}/api/admin/users/${userId}`,
  adminUserResetPassword: (userId: string) => `${API_BASE_URL}/api/admin/users/${userId}/reset-password`,
  adminUserVerifyEmail: (userId: string) => `${API_BASE_URL}/api/admin/users/${userId}/verify-email`,

  // User Invitations (Admin)
  adminInvitations: `${API_BASE_URL}/api/admin/invitations`,
  adminInvitation: (invitationId: string) => `${API_BASE_URL}/api/admin/invitations/${invitationId}`,
  adminInvitationResend: (invitationId: string) => `${API_BASE_URL}/api/admin/invitations/${invitationId}/resend`,

  // User Invitations (Public)
  invitationDetails: (token: string) => `${API_BASE_URL}/api/invitations/${token}/details`,
  invitationAccept: (token: string) => `${API_BASE_URL}/api/invitations/${token}/accept`,

  // Add other endpoints as needed
};

// Helper function for API calls with common headers
export const apiRequest = async (
  url: string,
  options: RequestInit = {}
): Promise<Response> => {
  const headers: any = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  
  // Add auth token if available (MongoDB auth uses 'mongo_access_token')
  const token = localStorage.getItem('mongo_access_token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  return fetch(url, {
    ...options,
    headers,
  });
};

export default API_BASE_URL;