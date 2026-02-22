/**
 * API Configuration for EstateFlow frontend.
 *
 * Standalone local application - connects to local backend.
 */

// Get API base URL from environment variable, fallback to localhost
export const API_BASE_URL = import.meta.env.VITE_API_URL || "";

// Enable mock data for frontend development (can be set via env var)
export const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA === "true" || false;


/**
 * API endpoint paths.
 * All paths are relative to /api/v1
 */
export const API_ENDPOINTS = {
  // Authentication
  auth: {
    login: "/api/v1/auth/login",
    signup: "/api/v1/auth/signup",
    me: "/api/v1/auth/me",
    logout: "/api/v1/auth/logout",
    refresh: "/api/v1/auth/refresh",
  },

  // Properties
  properties: {
    list: "/api/v1/properties",
    create: "/api/v1/properties",
    get: (id: string) => `/api/v1/properties/${id}`,
    update: (id: string) => `/api/v1/properties/${id}`,
    delete: (id: string) => `/api/v1/properties/${id}`,
    search: "/api/v1/properties/search",
    stats: "/api/v1/properties/stats/counts",
  },

  // Currencies
  currencies: {
    list: "/api/v1/currencies",
    rates: "/api/v1/currencies/rates",
  },

  // Chat
  chat: {
    send: (propertyId: string) => `/api/v1/properties/${propertyId}/chat`,
  },

  // Campaigns
  campaigns: {
    list: "/api/v1/campaigns",
    create: "/api/v1/campaigns",
    get: (id: string) => `/api/v1/campaigns/${id}`,
    launch: (id: string) => `/api/v1/campaigns/${id}/launch`,
    analytics: (id: string) => `/api/v1/campaigns/${id}/analytics`,
  },

  // Contacts
  contacts: {
    list: "/api/v1/contacts",
    create: "/api/v1/contacts",
    import: "/api/v1/contacts/import",
  },

  // Bookings
  bookings: {
    list: "/api/v1/bookings",
    create: "/api/v1/bookings",
    get: (id: string) => `/api/v1/bookings/${id}`,
    update: (id: string) => `/api/v1/bookings/${id}`,
    cancel: (id: string) => `/api/v1/bookings/${id}`,
    confirm: (id: string) => `/api/v1/bookings/${id}/confirm`,
    complete: (id: string) => `/api/v1/bookings/${id}/complete`,
    noShow: (id: string) => `/api/v1/bookings/${id}/no-show`,
    availability: "/api/v1/bookings/availability",
    propertyAvailability: (propertyId: string) => `/api/v1/bookings/properties/${propertyId}/availability`,
    admin: {
      manualCreate: "/api/v1/bookings/admin/manual-create",
      reassignAgent: (id: string) => `/api/v1/bookings/${id}/admin/reassign-agent`,
      bulkAction: "/api/v1/bookings/admin/bulk-action",
      actionLogs: (id: string) => `/api/v1/bookings/${id}/admin/action-logs`,
    },
  },

  // Search
  search: {
    query: "/api/v1/search",
    popularSearches: "/api/v1/search/analytics/popular-searches",
    zeroResults: "/api/v1/search/analytics/zero-results",
    performance: "/api/v1/search/analytics/performance",
    locationSuggestions: "/api/v1/search/suggestions/locations",
    amenitySuggestions: "/api/v1/search/suggestions/amenities",
  },

  // Documents
  documents: {
    list: "/api/v1/documents",
    create: "/api/v1/documents",
    get: (id: string) => `/api/v1/documents/${id}`,
    update: (id: string) => `/api/v1/documents/${id}`,
    delete: (id: string) => `/api/v1/documents/${id}`,
    sendForSignature: (id: string) => `/api/v1/documents/${id}/send-for-signature`,
    downloadPdf: (id: string) => `/api/v1/documents/${id}/download/pdf`,
    downloadDocx: (id: string) => `/api/v1/documents/${id}/download/docx`,
  },

  // Templates
  templates: {
    list: "/api/v1/documents/templates",
    create: "/api/v1/documents/templates",
    get: (id: string) => `/api/v1/documents/templates/${id}`,
    update: (id: string) => `/api/v1/documents/templates/${id}`,
    delete: (id: string) => `/api/v1/documents/templates/${id}`,
    generateAi: "/api/v1/documents/templates/generate-ai",
  },

  // Organizations
  organizations: {
    list: "/api/v1/organizations",
    get: (id: string) => `/api/v1/organizations/${id}`,
  },

  // Users
  users: {
    list: "/api/v1/users",
    invite: "/api/v1/users/invite",
    update: (id: string) => `/api/v1/users/${id}`,
    pendingInvitations: "/api/v1/users/invitations/pending",
    savedProperties: {
      list: "/api/v1/users/me/saved-properties",
      save: (propertyId: string) => `/api/v1/users/me/saved-properties/${propertyId}`,
      unsave: (propertyId: string) => `/api/v1/users/me/saved-properties/${propertyId}`,
      check: (propertyId: string) => `/api/v1/users/me/saved-properties/${propertyId}/check`,
    },
  },

  // Leads (public)
  leads: {
    submit: "/api/v1/leads",
  },

  // Payments
  payments: {
    list: "/api/v1/payments",
    create: "/api/v1/payments",
    get: (id: string) => `/api/v1/payments/${id}`,
  },

  // Invoices
  invoices: {
    list: "/api/v1/invoices",
    create: "/api/v1/invoices",
    get: (id: string) => `/api/v1/invoices/${id}`,
  },
};

/**
 * Helper function to build full API URL.
 *
 * @param path - API endpoint path
 * @returns Full URL
 */
export function buildApiUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}

/**
 * Convert storage path to full URL for accessing files.
 *
 * @param path - Storage path or full URL
 * @param useGridFS - Whether to use GridFS endpoint
 * @returns Full URL for accessing the file
 */
export function getStorageUrl(path: string, useGridFS: boolean = false): string {
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }

  if (path.startsWith('/api/v1/storage/')) {
    return `${API_BASE_URL}${path}`;
  }

  if (useGridFS) {
    return `${API_BASE_URL}/api/v1/storage/gridfs/${path}`;
  }

  return `${API_BASE_URL}/api/v1/storage/${path}`;
}

/**
 * Get the selected organization ID from localStorage.
 *
 * @returns Organization ID or null
 */
export function getSelectedOrganizationId(): string | null {
  return localStorage.getItem('selectedOrganizationId');
}

/**
 * Get the auth token from localStorage.
 *
 * @returns Auth token or null
 */
export function getAuthToken(): string | null {
  return localStorage.getItem('authToken');
}

/**
 * Set the auth token in localStorage.
 *
 * @param token - Auth token
 */
export function setAuthToken(token: string): void {
  localStorage.setItem('authToken', token);
}

/**
 * Remove the auth token from localStorage.
 */
export function removeAuthToken(): void {
  localStorage.removeItem('authToken');
}

/**
 * Default headers for API requests.
 *
 * @param token - Optional authentication token
 * @param organizationId - Optional organization ID
 * @returns Headers object
 */
export function getDefaultHeaders(token?: string, organizationId?: string): HeadersInit {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };

  // Use provided token or get from localStorage
  const authToken = token || getAuthToken();
  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }

  if (organizationId) {
    headers["X-Organization-Id"] = organizationId;
  }

  return headers;
}
