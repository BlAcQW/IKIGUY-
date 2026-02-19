/**
 * API Configuration for EstateFlow frontend.
 *
 * Centralizes API base URLs and endpoint paths.
 */

// Get API base URL from environment variable
export const API_BASE_URL = import.meta.env.VITE_API_URL || "https://estateflow-api.ailabsafrica.com";

/**
 * API endpoint paths.
 * All paths are relative to /api/v1
 */
export const API_ENDPOINTS = {
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

  // Future endpoints (Phase 2+)
  chat: {
    send: (propertyId: string) => `/api/v1/properties/${propertyId}/chat`,
  },

  campaigns: {
    list: "/api/v1/campaigns",
    create: "/api/v1/campaigns",
    get: (id: string) => `/api/v1/campaigns/${id}`,
    launch: (id: string) => `/api/v1/campaigns/${id}/launch`,
    analytics: (id: string) => `/api/v1/campaigns/${id}/analytics`,
  },

  contacts: {
    list: "/api/v1/contacts",
    create: "/api/v1/contacts",
    import: "/api/v1/contacts/import",
  },

  // Bookings (Phase 5)
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
    // Admin endpoints
    admin: {
      manualCreate: "/api/v1/bookings/admin/manual-create",
      reassignAgent: (id: string) => `/api/v1/bookings/${id}/admin/reassign-agent`,
      bulkAction: "/api/v1/bookings/admin/bulk-action",
      actionLogs: (id: string) => `/api/v1/bookings/${id}/admin/action-logs`,
    },
  },

  // Search (Phase 10)
  search: {
    query: "/api/v1/search",
    popularSearches: "/api/v1/search/analytics/popular-searches",
    zeroResults: "/api/v1/search/analytics/zero-results",
    performance: "/api/v1/search/analytics/performance",
    locationSuggestions: "/api/v1/search/suggestions/locations",
    amenitySuggestions: "/api/v1/search/suggestions/amenities",
  },

  // Documents (Phase 11)
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

  templates: {
    list: "/api/v1/documents/templates",
    create: "/api/v1/documents/templates",
    get: (id: string) => `/api/v1/documents/templates/${id}`,
    update: (id: string) => `/api/v1/documents/templates/${id}`,
    delete: (id: string) => `/api/v1/documents/templates/${id}`,
    generateAi: "/api/v1/documents/templates/generate-ai",
  },

  // Organizations (Multi-tenancy)
  organizations: {
    list: "/api/v1/organizations",
    get: (id: string) => `/api/v1/organizations/${id}`,
  },

  // Users (Admin-only)
  users: {
    list: "/api/v1/users",
    invite: "/api/v1/users/invite",
    update: (id: string) => `/api/v1/users/${id}`,
    pendingInvitations: "/api/v1/users/invitations/pending",
    // Saved Properties
    savedProperties: {
      list: "/api/v1/users/me/saved-properties",
      save: (propertyId: string) => `/api/v1/users/me/saved-properties/${propertyId}`,
      unsave: (propertyId: string) => `/api/v1/users/me/saved-properties/${propertyId}`,
      check: (propertyId: string) => `/api/v1/users/me/saved-properties/${propertyId}/check`,
    },
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
 * Images/videos are stored as paths (e.g., "properties/org_id/property-images/2025/12/file.jpg")
 * and need to be accessed via the storage API endpoint.
 *
 * @param path - Storage path or full URL (or GridFS file_id)
 * @param useGridFS - Whether to use GridFS endpoint (default: false for backward compatibility)
 * @returns Full URL for accessing the file
 */
export function getStorageUrl(path: string, useGridFS: boolean = false): string {
  // If already a full URL, return as-is
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }

  // If path starts with /api/v1, it's already a relative API path
  if (path.startsWith('/api/v1/storage/')) {
    return `${API_BASE_URL}${path}`;
  }

  // GridFS endpoint for MongoDB-stored images
  if (useGridFS) {
    return `${API_BASE_URL}/api/v1/storage/gridfs/${path}`;
  }

  // Legacy: Convert storage path to Hetzner Storage URL
  return `${API_BASE_URL}/api/v1/storage/${path}`;
}

/**
 * Get the selected organization ID from localStorage.
 * Used for admin users switching between organizations.
 *
 * @returns Organization ID or null
 */
export function getSelectedOrganizationId(): string | null {
  return localStorage.getItem('selectedOrganizationId');
}

/**
 * Default headers for API requests.
 *
 * @param token - Optional authentication token
 * @param organizationId - Optional organization ID for admin users switching organizations
 * @returns Headers object
 */
export function getDefaultHeaders(token?: string, organizationId?: string): HeadersInit {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // Add organization ID header if provided (for admin users switching orgs)
  if (organizationId) {
    headers["X-Organization-Id"] = organizationId;
  }

  return headers;
}
